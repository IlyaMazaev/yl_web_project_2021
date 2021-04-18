from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class AddNewPostForm(FlaskForm):
    text = IntegerField('текст записи', validators=[DataRequired()])

    submit = SubmitField('Подтвердить')
