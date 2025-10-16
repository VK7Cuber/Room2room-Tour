from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Length, Optional
from flask_wtf import FlaskForm


class ProfileForm(FlaskForm):
    first_name = StringField("Имя", validators=[Optional(), Length(max=64)])
    last_name = StringField("Фамилия", validators=[Optional(), Length(max=64)])
    city = StringField("Город", validators=[Optional(), Length(max=128)])
    phone = StringField("Телефон", validators=[Optional(), Length(max=32)])
    avatar = StringField("URL аватара", validators=[Optional(), Length(max=255)])
    description = TextAreaField("О себе", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Сохранить")


