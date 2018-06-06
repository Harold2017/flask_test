from datetime import datetime, timedelta
from ..models import Device, AppointmentEvents
from .. import db
from pytz import timezone
from sqlalchemy import desc, inspect, and_
from sqlalchemy.ext.automap import automap_base
from flask_table import create_table, Col, LinkCol
from collections import OrderedDict
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, \
    SubmitField, FloatField, IntegerField, BooleanField
from wtforms.fields.html5 import DateTimeField
from wtforms.validators import Required, Length, Email


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')


def tz_local(_datetime: datetime) -> str:
    """
    timezone transfer function, from utc to local
    meanwhile format it
    :param datetime _datetime:
    :return: string local datetime
    """
    return _datetime.replace(tzinfo=utc).astimezone(tzchina).strftime(
            "%Y/%m/%d-%H:%M:%S")


def check_booking(device_id: int) -> 'sql query result(dict)' or None:
    """
    check booking condition of the scanned QR-code device
    if the device is booked during this time period, only user with booked email can login
    if the booked user not login within 30 mins, the booking will be cancelled and the device will be open for login
    :param int device_id:
    :return: dict booking event or None
    """
    time = datetime.utcnow()
    event = AppointmentEvents.query.filter(
        and_(AppointmentEvents.device_id == device_id,
             AppointmentEvents.start <= time,
             AppointmentEvents.end >= time)
    ).first()
    device = Device.query.filter_by(id=device_id).first()
    if device.device_inuse:
        return event
    elif event:
        if event.start <= time - timedelta(seconds=1800) and not event.is_finished:
            db.session.delete(event)
            db.session.commit()
            return None
        elif event.is_finished:
            return None
    return event


def find_database_table(table_name: str) -> 'sql table':
    """
    find and return sql table with table_name
    :param table_name:
    :return:
    """
    Base = automap_base()
    Base.prepare(db.engine, reflect=True)  # use automap of sqlalchemy to get table's corresponding class model
    table = getattr(Base.classes, table_name, None)  # getattr to access attribute like Base.classes.device_type
    return table


def generate_table(device_type: str, device_id: int or str) -> 'flask_table Table object' or None:
    """
    generate html table according to device type and device_id
    :param string device_type:
    :param int or str device_id:
    :return: flask_table Table object or None
    """
    table = find_database_table(device_type)
    devices = db.session.query(table.device_id).distinct()  # find all distinct devices
    available_devices = []
    table = None
    for device in devices:
        device = Device.query.filter_by(id=device.device_id).first()
        if device.id == int(device_id):  # only record devices with different id from booked device
            pass
        elif device.device_inuse:  # only record devices not used
            pass
        else:
            available_devices.append({"device_id": device.id,
                                      "device_name": device.name,
                                      "booking_link": device.id})
    if len(available_devices) != 0:
        TableCls = create_table('TableCls', options=dict(classes=['table', 'table-bordered'], no_items='No Items')) \
            .add_column('device_id', Col('Device ID')) \
            .add_column('device_name', Col('Device Name')) \
            .add_column('booking_link', LinkCol('Booking Link', 'appointment.calendar',
                                                url_kwargs=dict(selected_device='booking_link')))
        table = TableCls(available_devices)
    return table


def row2dict(row: 'sql query') -> dict:
    """
    convert sql query result to dict
    :param row: sql query row
    :return: dict
    """
    dict = {column.key: getattr(row, column.key) for column in inspect(row).mapper.column_attrs}
    try:
        del dict["email"]
        del dict["id"]
    except KeyError as e:
        print("No such key: '%s'" % e)
    finally:
        return dict


def row2ordereddict(row: 'sql query') -> OrderedDict:
    """
    convert sql query result to OrderedDict
    :param sql query row:
    :return:
    """
    result = OrderedDict()
    for column in inspect(row).mapper.column_attrs:
        result[column.key] = getattr(row, column.key)
    try:
        del result["email"]
        del result["id"]
    except KeyError as e:
        print("No such key: '%s'" % e)
    finally:
        return result


def query_new_log(table: 'sql table', device_id: int, limit: int=5, offset: int=0) -> list:
    """
    query sql table with device_id = device_id to get a limit number of records with offset
    :param sql table table:
    :param int device_id:
    :param int limit:
    :param int offset:
    :return: list log_list
    """
    # display the records with limit number and offset
    table_logs = db.session.query(table).filter_by(device_id=device_id).order_by(desc(table.id)). \
        limit(limit).offset(offset).all()

    # get device name
    device_name = Device.query.filter_by(id=device_id).first().name

    log_list = []
    for table_log in table_logs:
        # log = row2dict(table_log)
        log = row2ordereddict(table_log)
        log["start_time"] = tz_local(log["start_time"])
        log["end_time"] = tz_local(log["end_time"]) if table_log.end_time is not None else 'Inuse'
        log["device_name"] = device_name
        log.move_to_end('device_name', last=False)
        log_list.append(log)
    return log_list


fields = {'INT': IntegerField,
          'VAR': StringField,
          'TEX': TextAreaField,
          'TIN': BooleanField,
          'DAT': DateTimeField,
          'FLO': FloatField
          }


def generate_form(form_type: str, columns: 'sql table columns', **kwargs) -> 'wtforms form object':
    """
    generate login / logout form according to form type and table columns
    :param form_type: str -> login / logout
    :param columns: table columns from sqlalchemy table description
    :param kwargs: may extend some features later
    :return: wtforms' form object
    """
    class BaseForm(FlaskForm):
        """
        base form with common username, device_status fields
        """
        username = StringField('User name', validators=[Required(), Length(1, 64)])
        email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
        device_status = SelectField('Device status', coerce=int,
                                    choices=[(0, 'None'), (1, 'Normal'), (2, 'Broken'), (3, 'Fixing'),
                                             (4, 'Terminated')],
                                    default=0,
                                    validators=[Required()])

    for c in list(columns)[5:]:  # ignore id, device_id, device_status, username and email fields
        field = fields.get(str(c.type)[:3])
        if str(c.type)[:3] == 'DAT':
            # field = field(c.name.capitalize(), format="%Y-%m-%d %H:%M", default=datetime.utcnow().replace(
            # tzinfo=utc).astimezone(tzchina))
            continue
        elif form_type == 'login' and (str(c.name) == 'product' or str(c.name) == 'remarks'):  # login form
            continue
        elif form_type == 'logout' and (str(c.name) == 'material' or str(c.name) == 'details'):  # logout form
            continue
        else:  # Text field (details / remarks are not required)
            field = field(c.name.capitalize(), validators=[Required()] if str(c.type)[:3] != 'TEX' else None)
        setattr(BaseForm, c.name, field)

    class Form(BaseForm):
        """
        add submit filed
        """
        submit = SubmitField('Submit')

        def __init__(self, *args, **kwargs):
            super(Form, self).__init__(*args, **kwargs)

    return Form(**kwargs)
