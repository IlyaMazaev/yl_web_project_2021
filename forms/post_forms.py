from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from flask_wtf.file import FileField, FileRequired
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class AddNewPostForm(FlaskForm):
    text = StringField('Текст записи', validators=[DataRequired()])
    file = FileField('Прикрепите картинку')

    submit = SubmitField('Подтвердить')
