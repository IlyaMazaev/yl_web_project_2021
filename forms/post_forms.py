from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class AddNewPostForm(FlaskForm):
    text = StringField('текст записи', validators=[DataRequired()])
    file = FileField('Прикрепите картинку')

    submit = SubmitField('Подтвердить')
