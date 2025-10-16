from wtforms import StringField, TextAreaField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf import FlaskForm


class TourismOfferForm(FlaskForm):
    title = StringField("Заголовок", validators=[DataRequired(), Length(max=140)])
    city = StringField("Город", validators=[Optional(), Length(max=128)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=4000)])
    price_per_hour = IntegerField("Цена/час (₽)", validators=[DataRequired(), NumberRange(min=0, max=1_000_000)])
    duration_hours = IntegerField("Длительность (часов)", validators=[DataRequired(), NumberRange(min=1, max=24)])
    photos = StringField("Фото URL (через запятую)", validators=[Optional(), Length(max=2000)])
    available_from = DateField("Доступно с", validators=[Optional()])
    available_to = DateField("Доступно по", validators=[Optional()])


class TourismFilterForm(FlaskForm):
    q = StringField("Поиск", validators=[Optional(), Length(max=128)])
    city = StringField("Город", validators=[Optional(), Length(max=128)])

