from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateTimeField, FileField
from wtforms.validators import DataRequired


class EventForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired()])
    image = FileField('Фотография', validators=[DataRequired()])
    date_begin = DateTimeField('Дата начала', validators=[DataRequired()])
    date_end = DateTimeField('Дата окончания', validators=[DataRequired()])
    place = StringField('Место проведения', validators=[DataRequired()])
    submit = SubmitField('Отправить')