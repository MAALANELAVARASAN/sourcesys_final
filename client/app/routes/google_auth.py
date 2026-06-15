from flask import redirect, url_for, flash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user
from client.app.models.user import db, User
import os

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_to="google_auth.google_login_callback"
)

from flask import Blueprint
callback_bp = Blueprint("google_auth", __name__)

@callback_bp.route("/login/google/callback")
def google_login_callback():
    if not google.authorized:
        flash("Google login failed.", "error")
        return redirect(url_for("auth.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "error")
        return redirect(url_for("auth.login"))

    info = resp.json()
    email = info["email"]
    name  = info.get("name", email.split("@")[0]).replace(" ", "_").lower()

    # Find or create user
    user = User.query.filter_by(email=email).first()
    if not user:
        # Check if first user → make admin
        is_first = User.query.count() == 0
        user = User(
            username=name,
            email=email,
            password_hash="google_oauth",  # no password for OAuth users
            role="admin" if is_first else "user"
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("chat.new_chat"))