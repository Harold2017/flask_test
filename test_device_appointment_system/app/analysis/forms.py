from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField


class DeviceForm(FlaskForm):
    device = SelectMultipleField('Devices', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, devices, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        self.device.choices = [(device.id, device.name) for device in devices]
        self.devices = devices

