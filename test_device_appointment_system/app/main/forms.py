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
    device = TextAreaField('Device')
    submit = SubmitField('Submit')


class EditDeviceForm(FlaskForm):
    name = StringField('Device name', validators=[Required(), Length(1, 64)])
    users = TextAreaField('User names(separated by comma)')
    status = SelectField('Device status', choices=[('Normal', 'Normal'), ('Broken', 'Broken'), ('Fixing', 'Fixing'), ('Terminated', 'Terminated')])
    device_type = SelectField('Device type')
    details = TextAreaField('Details')
    submit = SubmitField('Submit')

    def __init__(self, device_types, *args, **kwargs):
        super(EditDeviceForm, self).__init__(*args, **kwargs)
        self.device_type.choices = [(device["type"], device["type"]) for device in device_types]


class ItemTable(Table):
    name = Col('Name')
    id = Col('id')
    classes = ['table', 'table-bordered']
    status = Col('status')
    details = Col('details')
    # users = Col('users')


class Item(object):
    def __init__(self, name, id, status, details):
        self.name = name
        self.id = id
        self.status = status
        self.details = details
        # ud = db.session.query(user_device).filter_by(device_id=id).all()
        # self.users = ud


class DeleteDeviceTypeForm(FlaskForm):
    device_type = SelectField('Device type')
    submit = SubmitField('Delete Confirm')

    def __init__(self, device_types, *args, **kwargs):
        super(DeleteDeviceTypeForm, self).__init__(*args, **kwargs)
        self.device_type.choices = [(device["type"], device["type"]) for device in device_types]
