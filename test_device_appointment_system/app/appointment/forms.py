from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField


class DeviceSelectionForm(FlaskForm):
    device = SelectField('Devices', coerce=int)
    submit = SubmitField('Confirm')

    def __init__(self, devices, *args, **kwargs):
        super(DeviceSelectionForm, self).__init__(*args, **kwargs)
        self.device.choices = [(device["id"], device["name"]) for device in devices]
        self.devices = devices
