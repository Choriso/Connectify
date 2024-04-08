from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class InterestForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired()])
    tags = StringField('Теги', validators=[DataRequired()])
    submit = SubmitField('Завершить')