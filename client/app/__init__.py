from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from .models import db, User, Chat, Message, FAQCollection, FAQPair, Document
import os
from dotenv import load_dotenv

load_dotenv()

# Allow HTTP for local development
if os.getenv("ENVIRONMENT") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # Secret key
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

    # Database URL
    client_db_uri = os.getenv("CLIENT_DATABASE_URL")

    if not client_db_uri:
        sqlite_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "client.db")
        )
        client_db_uri = f"sqlite:///{sqlite_path}"

    app.config["SQLALCHEMY_DATABASE_URI"] = client_db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Prevent stale SSL/database connection issues on Render
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Initialize extensions
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Google OAuth
    from client.app.routes.google_auth import google_bp, callback_bp

    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(callback_bp)

    # App routes
    from client.app.routes.auth import auth
    from client.app.routes.chat import chat
    from client.app.routes.admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(chat)
    app.register_blueprint(admin)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def root():
        if current_user.is_authenticated:
            return redirect(url_for("chat.index"))
        return redirect(url_for("auth.login"))

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))