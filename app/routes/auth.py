from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from sqlalchemy import select

from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegisterForm


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        stmt = select(User).where(User.email == form.email.data.lower().strip())
        user = db.session.execute(stmt).scalar_one_or_none()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Вы успешно вошли", "success")
            next_url = request.args.get("next") or url_for("main.index")
            return redirect(next_url)
        flash("Неверный email или пароль", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.lower().strip()
        # Проверка уникальности
        exists = db.session.execute(
            select(User).where((User.email == email) | (User.username == username))
        ).scalar_one_or_none()
        if exists:
            flash("Пользователь с таким email или именем уже существует", "warning")
            return render_template("auth/register.html", form=form)

        user = User(username=username, email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Регистрация прошла успешно!", "success")
        return redirect(url_for("main.index"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Вы вышли из аккаунта", "info")
    return redirect(url_for("main.index"))


