from wtforms import StringField, TextAreaField, IntegerField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed


class ListingForm(FlaskForm):
    title = StringField("Заголовок", validators=[DataRequired(), Length(max=140)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=4000)])
    city = StringField("Город", validators=[Optional(), Length(max=128)])
    address = StringField("Адрес", validators=[Optional(), Length(max=255)])
    housing_type = SelectField(
        "Тип жилья",
        choices=[("apartment", "Квартира"), ("house", "Дом"), ("room", "Комната"), ("studio", "Студия")],
        validators=[Optional()],
    )
    room_count = IntegerField("Комнат", validators=[Optional(), NumberRange(min=0, max=50)])
    available_from = DateField("Доступно с", validators=[Optional()])
    available_to = DateField("Доступно по", validators=[Optional()])
    # Для простоты: ввод удобств и фото через запятую (позже заменим на теги/загрузчик)
    amenities = StringField("Удобства (через запятую)", validators=[Optional(), Length(max=500)])
    photos = FileField(
        "Фото (png/jpg/jpeg/webp, heic)",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp", "heic", "heif"], "Только изображения: JPG, PNG, WEBP, HEIC")],
        render_kw={"multiple": True, "accept": "image/*"},
    )


class FilterForm(FlaskForm):
    q = StringField("Поиск", validators=[Optional(), Length(max=128)])
    city = StringField("Город", validators=[Optional(), Length(max=128)])
    housing_type = SelectField(
        "Тип",
        choices=[("", "Любой"), ("apartment", "Квартира"), ("house", "Дом"), ("room", "Комната"), ("studio", "Студия")],
        validators=[Optional()],
    )
    rooms_min = IntegerField("Мин. комнат", validators=[Optional(), NumberRange(min=0, max=50)])
    rooms_max = IntegerField("Макс. комнат", validators=[Optional(), NumberRange(min=0, max=50)])

