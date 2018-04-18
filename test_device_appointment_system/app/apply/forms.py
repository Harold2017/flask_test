from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import Required
from flask_table import Table, Col


'''
class ChoiceObj(object):
    def __init__(self, name, choices):
        setattr(self, name, choices)


class MultipleCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    # widget = widgets.TableWidget()
    option_widget = widgets.CheckboxInput()'''


class DeviceForm(FlaskForm):
    # device = MultipleCheckboxField('Devices', coerce=int)
    device = SelectMultipleField('Devices', coerce=int)
    submit = SubmitField('Apply')

    def __init__(self, devices, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        self.device.choices = [(device.id, device.name) for device in devices]
        self.devices = devices


class ConfirmForm(FlaskForm):
    device = SelectMultipleField('Devices', coerce=int)
    submit = SubmitField('Confirm')

    def __init__(self, devices, *args, **kwargs):
        super(ConfirmForm, self).__init__(*args, **kwargs)
        self.device.choices = [(device.id, device.name) for device in devices]
        self.devices = devices


class ApplicationTable(Table):
    user_email = Col('User Email')
    devices = Col('Applied Devices')
    classes = ['table', 'table-bordered']
    application_time = Col('Application Time')
    handled_time = Col('Handled Time')
    approved_devices = Col('Approved Devices')
    application_state = Col('Application State')

