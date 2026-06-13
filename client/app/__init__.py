from flask import Flask
from flask_login import LoginManager
from .models import db, User
import os
from dotenv import load_dotenv

load_dotenv()

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

    client_db_uri = os.getenv("CLIENT_DATABASE_URL")
    if not client_db_uri:
        sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "client.db"))
        client_db_uri = f"sqlite:///{sqlite_path}"

    app.config["SQLALCHEMY_DATABASE_URI"] = client_db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from client.app.routes.auth import auth
    from client.app.routes.chat import chat
    from client.app.routes.admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(chat)
    app.register_blueprint(admin)

    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))