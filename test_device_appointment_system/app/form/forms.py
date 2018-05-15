from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, \
    SubmitField, FloatField, IntegerField, BooleanField
from wtforms.fields.html5 import DateTimeField
from wtforms.validators import Required, Length
from flask_table import Table, Col
from datetime import datetime

from pytz import timezone


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')


class StartForm(FlaskForm):
    # name = StringField('Device name', validators=[Required(), Length(1, 64)])
    user = StringField('User name', validators=[Required(), Length(1, 64)])
    status = SelectField('Device status', coerce=int,
                         choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken'), (3, 'Fixing'), (4, 'Terminated')],
                         default=0,
                         validators=[Required()])
    material = StringField('Material', validators=[Required()])
    details = TextAreaField('Details')
    submit = SubmitField('Submit')


class EndForm(FlaskForm):
    status = SelectField('Device status', coerce=int,
                         choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken'), (3, 'Fixing'), (4, 'Terminated')],
                         default=0,
                         validators=[Required()])
    product = StringField('Product', validators=[Required()])
    remarks = TextAreaField('Remarks')
    submit = SubmitField('Submit')


class GloveBoxStartForm(FlaskForm):
    user = StringField('User name', validators=[Required(), Length(1, 64)])
    status = SelectField('Glovebox status', coerce=int,
                         choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken'), (3, 'Fixing'), (4, 'Terminated')],
                         default=0,
                         validators=[Required()])
    h2o = FloatField('H2O(ppm)', validators=[Required()])
    o2 = FloatField('O2(ppm)', validators=[Required()])
    ar = FloatField('Ar(psi)', validators=[Required()])
    pressure = FloatField('Pressure(mbar)', validators=[Required()])
    material = StringField('Material', validators=[Required(), Length(1, 128)])
    details = TextAreaField('Details')
    submit = SubmitField('Submit')


class GloveBoxEndForm(FlaskForm):
    status = SelectField('Glovebox status', coerce=int,
                         choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken'), (3, 'Fixing'), (4, 'Terminated')],
                         default=0,
                         validators=[Required()])
    h2o = FloatField('H2O(ppm)', validators=[Required()])
    o2 = FloatField('O2(ppm)', validators=[Required()])
    ar = FloatField('Ar(psi)', validators=[Required()])
    pressure = FloatField('Pressure(mbar)', validators=[Required()])
    product = StringField('Product', validators=[Required(), Length(1, 128)])
    remarks = TextAreaField('Remarks')
    submit = SubmitField('Submit')


class ItemTable(Table):
    user_name = Col('Username')
    device_id = Col('Device_id')
    device_name = Col('Device_name')
    classes = ['table', 'table-bordered']
    device_status = Col('Device_status')
    start_time = Col('Start_time')
    material = Col('Material')
    details = Col('Details')
    end_time = Col('End_time')
    product = Col('Product')
    remarks = Col('Remarks')


class Item(object):
    def __init__(self, user_name, device_id, device_name, device_status, start_time, end_time, details, remarks):
        self.user_name = user_name
        self.device_id = device_id
        # self.device_status = {0: None, 1: 'Normal', 2: 'Broken'}.get(device_status)
        # self.log_time = log_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S')
        self.details = details
        # Username	Device_id	Device_status	Log_time	Details
        # Ivan Lau	15	        True	        2018-03-01 07:08:26
        self.device_status = device_status
        self.start_time = start_time
        self.device_name = device_name
        self.end_time = end_time
        self.remarks = remarks


class GloveItemTable(Table):
    user_name = Col('Username')
    device_id = Col('Device_id')
    device_name = Col('Device_name')
    classes = ['table', 'table-bordered']
    device_status = Col('Device_status')
    start_time = Col('Start_time')
    h2o_before = Col('H2O(ppm) before')
    o2_before = Col('O2(ppm) before')
    ar_before = Col('Ar(psi) before')
    pressure_before = Col('Pressure(mbar) before')
    material = Col('Material')
    details = Col('Details')
    end_time = Col('End_time')
    h2o_after = Col('H2O(ppm) after')
    o2_after = Col('O2(ppm) after')
    ar_after = Col('Ar(psi) after')
    pressure_after = Col('Pressure(mbar) after')
    product = Col('Product')
    remarks = Col('Remarks')


class StateTransferForm(FlaskForm):
    status = SelectField('Device status', coerce=int,
                         choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken'), (3, 'Fixing'), (4, 'Terminated')],
                         default=0,
                         validators=[Required()])
    submit = SubmitField('Submit')


fields = {'INT': IntegerField,
          'VAR': StringField,
          'TEX': TextAreaField,
          'TIN': BooleanField,
          'TIM': DateTimeField,
          'FLO': FloatField
          }


def generate_form(columns, **kwargs):

    class BaseForm(FlaskForm):
        user = StringField('User name', validators=[Required(), Length(1, 64)])
        status = SelectField('Device status', coerce=int,
                             choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken'), (3, 'Fixing'), (4, 'Terminated')],
                             default=0,
                             validators=[Required()])

    for c in list(columns)[3:]:  # ignore id, user and status fields
        field = fields.get(str(c.type)[:3])
        # if isinstance(field, DateTimeField):
        if str(c.type)[:3] == 'TIM':
            field = field(c.name.capitalize(), format="%Y-%m-%d %H:%M", default=datetime.utcnow().replace(tzinfo=utc).astimezone(tzchina))
        else:
            field = field(c.name.capitalize(), validators=[Required()] if str(c.type)[:3] != 'TEX' else None)
        setattr(BaseForm, c.name, field)

    class Form(BaseForm):
        submit = SubmitField('Submit')

        def __init__(self, *args, **kwargs):
            super(Form, self).__init__(*args, **kwargs)

    return Form(**kwargs)
