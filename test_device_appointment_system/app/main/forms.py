from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, \
    SubmitField, SelectMultipleField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User
from flask_table import Table, Col


class EditUserForm(FlaskForm):
    name = StringField('Real name', validators=[Length(1, 64),
                                                Regexp('^[A-Za-z][A-Za-z\s]*$', 0,
                                                       'Names must have only letters, '
                                                       'or space')])
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    # role = SelectField('Role', coerce=int)
    device = TextAreaField('Device')
    submit = SubmitField('Submit')


class ItemTable(Table):
    name = Col('Name')
    id = Col('id')
    classes = ['table', 'table-bordered']
    devices = Col('devices')


class Item(object):
    def __init__(self, name, id, devices):
        self.name = name
        self.id = id
        self.devices = devices
