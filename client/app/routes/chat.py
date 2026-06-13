from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import requests

chat = Blueprint("chat", __name__)

FASTAPI_URL = "http://127.0.0.1:8000/api/v1"


@chat.route("/")
@chat.route("/chat")
@login_required
def index():
    return render_template("chat.html", user=current_user)


@chat.route("/chat/generate", methods=["POST"])
@login_required
def generate():
    prompt = request.form.get("prompt", "").strip()
    files = request.files.getlist("files")

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        file_list = []
        for file in files:
            if file and file.filename:
                file_list.append((file.filename, file.read(), file.content_type))

        multipart_files = [
            ("files", (fname, data, ctype))
            for fname, data, ctype in file_list
        ] if file_list else None

        response = requests.post(
            f"{FASTAPI_URL}/faq/generate",
            data={"prompt": prompt},
            files=multipart_files,
            timeout=180
        )

        print(f"[CHAT] FastAPI status: {response.status_code}")
        print(f"[CHAT] FastAPI body: {response.text[:300]}")

        if response.status_code != 200:
            try:
                error_detail = response.json().get("detail", response.text[:300])
            except Exception:
                error_detail = response.text[:300]
            return jsonify({"error": f"Backend error: {error_detail}"}), 500

        return jsonify(response.json())

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot reach backend. Is FastAPI running?"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"error": "The AI is taking too long. Please try again in a few seconds."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500