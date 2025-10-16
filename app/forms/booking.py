from wtforms import DateField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf import FlaskForm


class TourBookingForm(FlaskForm):
    start_date = DateField("Дата начала", validators=[DataRequired()])
    end_date = DateField("Дата окончания", validators=[DataRequired()])
    hours = IntegerField("Часов", validators=[DataRequired(), NumberRange(min=1, max=24)])
    submit = SubmitField("Забронировать")


