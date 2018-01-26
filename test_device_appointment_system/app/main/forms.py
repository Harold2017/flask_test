from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, \
    SubmitField, SelectMultipleField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User


class EditUserForm(FlaskForm):
    name = StringField('Real name', validators=[Required(), Length(1, 64),
                                                Regexp('^[A-Za-z][A-Za-z\s]*$', 0,
                                                       'Names must have only letters, '
                                                       'or space')])
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    role = SelectField('Role', coerce=int)
    submit = SubmitField('Submit')
