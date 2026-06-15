from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from client.app.models.user import db, User
from client.app.models.chat import Chat, FAQCollection, FAQPair, Document

admin = Blueprint("admin", __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@admin.route("/admin")
@login_required
@admin_required
def dashboard():
    users       = User.query.all()
    total_users = User.query.count()
    admin_count = User.query.filter_by(role="admin").count()
    user_count  = User.query.filter_by(role="user").count()

    # extra stats
    total_chats    = Chat.query.count()
    total_faqs     = FAQPair.query.count()
    total_docs     = Document.query.count()
    total_collections = FAQCollection.query.count()

    # most active user
    from sqlalchemy import func
    most_active = db.session.query(
        User.username,
        func.count(Chat.id).label("chat_count")
    ).join(Chat, Chat.user_id == User.id)\
     .group_by(User.id)\
     .order_by(func.count(Chat.id).desc())\
     .first()

    return render_template(
        "admin.html",
        users=users,
        total_users=total_users,
        admin_count=admin_count,
        user_count=user_count,
        total_chats=total_chats,
        total_faqs=total_faqs,
        total_docs=total_docs,
        total_collections=total_collections,
        most_active=most_active,
        current_user=current_user
    )


@admin.route("/admin/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete yourself.", "error")
        return redirect(url_for("admin.dashboard"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/admin/promote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    user.role = "admin"
    db.session.commit()
    flash(f"{user.username} promoted to admin.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/admin/demote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot demote yourself.", "error")
        return redirect(url_for("admin.dashboard"))
    user.role = "user"
    db.session.commit()
    flash(f"{user.username} demoted to user.", "success")
    return redirect(url_for("admin.dashboard"))