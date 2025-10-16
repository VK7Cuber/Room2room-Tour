from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Length
from flask_wtf import FlaskForm


class ReviewForm(FlaskForm):
    rating = IntegerField("Оценка", validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField("Комментарий", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Отправить отзыв")


