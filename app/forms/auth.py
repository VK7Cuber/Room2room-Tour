from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf import FlaskForm


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(message="Введите email"), Email(message="Неверный email")],
        render_kw={"placeholder": "you@example.com"},
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(message="Введите пароль"), Length(min=6, message="Минимум 6 символов")],
        render_kw={"placeholder": "Ваш пароль"},
    )
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[DataRequired(message="Введите имя пользователя"), Length(min=3, max=64)],
        render_kw={"placeholder": "username"},
    )
    email = StringField(
        "Email",
        validators=[DataRequired(message="Введите email"), Email(message="Неверный email")],
        render_kw={"placeholder": "you@example.com"},
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(min=6, message="Минимум 6 символов")],
        render_kw={"placeholder": "Придумайте пароль"},
    )
    password2 = PasswordField(
        "Повторите пароль",
        validators=[DataRequired(), EqualTo("password", message="Пароли не совпадают")],
        render_kw={"placeholder": "Повторите пароль"},
    )
    submit = SubmitField("Зарегистрироваться")


