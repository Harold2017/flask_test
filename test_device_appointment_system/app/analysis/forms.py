from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField
from flask_table import Table, Col


class DeviceForm(FlaskForm):
    device = SelectMultipleField('Devices', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, devices, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        self.device.choices = [(device.id, device.name) for device in devices]
        self.devices = devices


class DeviceInUseTable(Table):
    classes = ['table', 'table-bordered']
    user_name = Col('Username')
    device_id = Col('Device_id')
    device_name = Col('Device_name')
    device_status = Col('Device_status')
    start_time = Col('Start_time')
    material = Col('Material')
    details = Col('details')
