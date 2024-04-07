from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class ProfileForm(FlaskForm):
    information = StringField('Information about you', validators=[DataRequired()])
    interests = StringField('Your interests(space)', validators=[DataRequired()])
    connection = StringField('Contact information', validators=[DataRequired()])
    image = StringField('Url of your image', validators=[DataRequired()])
    is_allow_gps = BooleanField('Do you agree to our site tracking your gps?')
    submit = SubmitField('Submit')
