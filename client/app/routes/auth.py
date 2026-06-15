from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from client.app.models.user import db, User
from bcrypt import hashpw, checkpw, gensalt

auth = Blueprint("auth", __name__)


# SIGNUP
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username  = request.form.get("username")
        email     = request.form.get("email")
        password  = request.form.get("password")

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Username or email already exists.", "error")
            return redirect(url_for("auth.signup"))

        password_hash = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role="user"
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


# LOGIN
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("chat.index"))

    return render_template("login.html")


# LOGOUT
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))