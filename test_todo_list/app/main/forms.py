from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Required, Length


class TodoForm(FlaskForm):
    todo = TextAreaField(
        'Your task to do',
        validators=[Required()]
    )
    submit = SubmitField('Submitted')


class Todo_listForm(FlaskForm):
    title = StringField(
        'Your todo-list title',
        validators=[Required(), Length(1, 128)]
    )
    submit = SubmitField('Submit')
