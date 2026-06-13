from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from client.app.models.user import db, User

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


# ADMIN DASHBOARD
@admin.route("/admin")
@login_required
@admin_required
def dashboard():
    users      = User.query.all()
    total_users = User.query.count()
    admin_count = User.query.filter_by(role="admin").count()
    user_count  = User.query.filter_by(role="user").count()

    return render_template(
        "admin.html",
        users=users,
        total_users=total_users,
        admin_count=admin_count,
        user_count=user_count,
        current_user=current_user
    )


# DELETE USER
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


# PROMOTE USER TO ADMIN
@admin.route("/admin/promote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    user.role = "admin"
    db.session.commit()
    flash(f"{user.username} promoted to admin.", "success")
    return redirect(url_for("admin.dashboard"))