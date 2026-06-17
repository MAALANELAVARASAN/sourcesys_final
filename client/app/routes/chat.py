import os

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, make_response
from flask_login import login_required, current_user
from client.app.models import db, Chat, Message, FAQCollection, FAQPair
from datetime import datetime
import requests

chat = Blueprint("chat", __name__)
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000/api/v1")
print("FASTAPI_URL =", FASTAPI_URL)


@chat.route("/chat")
@login_required
def index():
    last = Chat.query.filter_by(user_id=current_user.id)\
                     .order_by(Chat.updated_at.desc()).first()
    if last:
        return redirect(url_for("chat.view_chat", chat_id=last.id))
    return redirect(url_for("chat.new_chat"))


#temporary route to check deployment of fastapi
@chat.route("/debug-fastapi")
def debug_fastapi():
    return {"FASTAPI_URL": FASTAPI_URL}


@chat.route("/chat/new")
@login_required
def new_chat():
    c = Chat(user_id=current_user.id, title="New Chat")
    db.session.add(c)
    db.session.commit()
    return redirect(url_for("chat.view_chat", chat_id=c.id))


@chat.route("/chat/<int:chat_id>")
@login_required
def view_chat(chat_id):
    c = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    chats = Chat.query.filter_by(user_id=current_user.id)\
                      .order_by(Chat.updated_at.desc()).all()
    return render_template("chat.html", current_chat=c, chats=chats, user=current_user)


@chat.route("/chat/<int:chat_id>/delete", methods=["POST"])
@login_required
def delete_chat(chat_id):
    c = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True})


@chat.route("/chat/<int:chat_id>/rename", methods=["POST"])
@login_required
def rename_chat(chat_id):
    c = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    c.title = data.get("title", "New Chat")[:100]
    db.session.commit()
    return jsonify({"ok": True, "title": c.title})


def _call_fastapi(endpoint: str, prompt: str, files) -> dict:
    """Shared helper to call FastAPI FAQ endpoints."""
    file_list = []
    for file in files:
        if file and file.filename:
            file_list.append((file.filename, file.read(), file.content_type))

    multipart_files = [
        ("files", (fname, data, ctype))
        for fname, data, ctype in file_list
    ] if file_list else None

    response = requests.post(
        f"{FASTAPI_URL}/{endpoint}",
        data={"prompt": prompt},
        files=multipart_files,
        timeout=180
    )

    if response.status_code != 200:
        try:
            error_detail = response.json().get("detail", response.text[:300])
        except Exception:
            error_detail = response.text[:300]
        raise Exception(f"Backend error: {error_detail}")

    return response.json()


def _save_response(chat_obj, prompt: str, data: dict) -> dict:
    """Save user message, assistant message and FAQ collection to DB."""
    user_msg = Message(chat_id=chat_obj.id, role="user", content=prompt)
    db.session.add(user_msg)

    if chat_obj.title == "New Chat":
        chat_obj.title = prompt[:60]

    asst_msg = Message(chat_id=chat_obj.id, role="assistant", content=data["direct_answer"])
    db.session.add(asst_msg)

    collection = FAQCollection(
        chat_id=chat_obj.id,
        source=data["source"],
        direct_answer=data["direct_answer"]
    )
    db.session.add(collection)
    db.session.flush()

    for pair in data.get("faq_pairs", []):
        faq = FAQPair(
            collection_id=collection.id,
            question=pair["question"],
            answer=pair["answer"]
        )
        db.session.add(faq)

    chat_obj.updated_at = datetime.utcnow()
    db.session.commit()

    return {
        "source":        data["source"],
        "direct_answer": data["direct_answer"],
        "faq_pairs":     [{"id": p.id, "question": p.question,
                           "answer": p.answer, "rating": p.rating}
                          for p in collection.pairs],
        "collection_id": collection.id,
        "message_id":    asst_msg.id
    }


@chat.route("/chat/<int:chat_id>/generate", methods=["POST"])
@login_required
def generate(chat_id):
    """Generate FAQs from current (last) file or prompt."""
    c = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    prompt = request.form.get("prompt", "").strip()
    files  = request.files.getlist("files")

    try:
        data = _call_fastapi("faq/generate", prompt, files)
        return jsonify(_save_response(c, prompt or "Generate FAQs", data))
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot reach backend. Is FastAPI running?"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"error": "The AI is taking too long. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/chat/<int:chat_id>/generate-all", methods=["POST"])
@login_required
def generate_all(chat_id):
    """Generate FAQs from ALL uploaded files."""
    c = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    prompt = request.form.get("prompt", "").strip()
    files  = request.files.getlist("files")

    try:
        data = _call_fastapi("faq/generate-all", prompt, files)
        return jsonify(_save_response(c, prompt or "Overall FAQ from all files", data))
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot reach backend. Is FastAPI running?"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"error": "The AI is taking too long. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/chat/faq/<int:pair_id>/rate", methods=["POST"])
@login_required
def rate_faq(pair_id):
    pair = FAQPair.query.get_or_404(pair_id)
    data = request.get_json()
    rating = data.get("rating")
    if rating not in ("up", "down", None):
        return jsonify({"error": "Invalid rating"}), 400
    pair.rating = None if pair.rating == rating else rating
    db.session.commit()
    return jsonify({"ok": True, "rating": pair.rating})


@chat.route("/chat/faq/<int:pair_id>/edit", methods=["POST"])
@login_required
def edit_faq(pair_id):
    pair = FAQPair.query.get_or_404(pair_id)
    data = request.get_json()
    question = data.get("question", "").strip()
    answer   = data.get("answer", "").strip()
    if not question or not answer:
        return jsonify({"error": "Question and answer required"}), 400
    pair.question = question
    pair.answer   = answer
    db.session.commit()
    return jsonify({"ok": True, "question": pair.question, "answer": pair.answer})


@chat.route("/share/<int:collection_id>")
def share_collection(collection_id):
    collection = FAQCollection.query.get_or_404(collection_id)
    return render_template("share.html", collection=collection)


@chat.route("/chat/export/pdf", methods=["POST"])
@login_required
def export_pdf():
    data = request.get_json()
    try:
        response = requests.post(
            f"{FASTAPI_URL}/faq/export/pdf",
            json=data, timeout=30
        )
        resp = make_response(response.content)
        resp.headers["Content-Type"] = "application/pdf"
        resp.headers["Content-Disposition"] = "attachment; filename=faqs.pdf"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat.route("/chat/<int:chat_id>/history")
@login_required
def chat_history(chat_id):
    c = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    collections = FAQCollection.query.filter_by(chat_id=c.id)\
                                     .order_by(FAQCollection.created_at).all()
    messages = Message.query.filter_by(chat_id=c.id)\
                            .order_by(Message.created_at).all()

    history = []
    col_idx = 0
    for msg in messages:
        if msg.role == "user":
            history.append({"role": "user", "content": msg.content})
        else:
            col = collections[col_idx] if col_idx < len(collections) else None
            if col:
                history.append({
                    "role":       "assistant",
                    "content":    msg.content,
                    "source":     col.source,
                    "collection": col.to_dict()
                })
                col_idx += 1
            else:
                history.append({"role": "assistant", "content": msg.content})

    return jsonify({"history": history, "title": c.title})