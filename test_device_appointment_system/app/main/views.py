from flask import request, render_template, jsonify, flash, current_app, redirect, url_for
from . import main
from .. import db
from ..models import User, Device, Permission, user_device, AnonymousUser, \
    DeviceUsageLog, GloveBoxLog, DeviceType, SlowQuery
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from .forms import EditUserForm, Item, ItemTable, EditDeviceForm
from ..QRcode.QRcode import qr_generator
from flask_sqlalchemy import get_debug_queries
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import desc
import re
from datetime import datetime
from pytz import timezone


BASEURL = 'http://namihk.com'
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


def find_users(device):
    uds = db.session.query(user_device).filter_by(device_id=device.id).all()
    users = []
    for ud in uds:
        user = User.query.filter_by(id=ud.user_id).first()
        users.append({"id": user.id, "name": user.name})
    return users


def find_devices(user):
    uds = db.session.query(user_device).filter_by(user_id=user.id).all()
    devices = []
    for ud in uds:
        device = Device.query.filter_by(id=ud.device_id).first()
        devices.append({"id": device.id, "name": device.name})
    return devices


def find_device_types():
    device_types = db.session.query(DeviceType).all()
    dt_list = []
    for dt in device_types:
        dt_list.append({"type": dt.type})
    return dt_list


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config["SLOW_QUERY_TIME"]:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
                                       (query.statement, query.parameters, query.duration, query.context))
            slowquery = SlowQuery(slowquery=query.statement,
                                  duration=query.duration,
                                  parameters=query.parameters,
                                  context=query.context)
            try:
                db.session.add(slowquery)
                db.commit()
            except Exception as e:
                db.session.rollback()
                db.session.flush()
                current_app.logger.warning('Cannot record this slow query into db!')
    return response


@main.route('/', methods=['GET', 'POST'])
def index():
    show_edit = False
    # print(current_user.is_administrator())
    # print(isinstance(current_user, AnonymousUser))
    # print(isinstance(current_user, User))
    if current_user.is_administrator():
        show_edit = True
    elif hasattr(current_user, 'email'):
        if current_user.email == 'jimmywlhon@nami.org.hk':
            show_edit = True
    else:
        pass
    return render_template("index.html", show_edit=show_edit)


@main.route('/edit', methods=['GET', 'POST'])
@login_required
# @admin_required
def edit():
    devices = Device.query.all()
    users = User.query.all()
    # ud = db.session.query(user_device).filter_by(device_id=devices[0].id).all()
    # print(ud[0].user_id)
    '''if devices is not None:
        table = ItemTable(devices)
    else:
        table = None'''
    device_list = []
    devicetypes = DeviceType.query.all()
    Base = automap_base()
    Base.prepare(db.engine,
                 reflect=True)  # use automap of sqlalchemy to get table's corresponding class model
    for device in devices:
        img_path = "../static/QRcode/Device" + str(device.id) + '.png'
        if DeviceUsageLog.query.filter_by(device_id=device.id).first():
            logs = BASEURL + "/form/device_log/" + str(device.id)
        elif GloveBoxLog.query.filter_by(device_id=device.id).first():
            logs = BASEURL + "/form/glovebox/glovebox_log/" + str(device.id)
        else:
            logs = None
            for devicetype in devicetypes:
                table = getattr(Base.classes, devicetype.type,
                                None)  # getattr to access attribute like Base.classes.device_type
                query = db.session.query(table).filter_by(device_id=device.id).first()
                if query:
                    device_type = devicetype.type
                    logs = BASEURL + "/form/new/" + device_type + '/log/' + str(device.id)
                    break
                else:
                    continue

        device_list.append({"id": device.id,
                            "name": device.name,
                            "status": device.status,
                            "details": device.details,
                            "img_path": img_path,
                            "users": find_users(device),
                            "logs": logs
                            })

    user_list = []
    for user in users:
        user_list.append({"id": user.id,
                          "name": user.name,
                          "devices": find_devices(user)})

    return render_template('edit/edit.html', devices=device_list, users=user_list)


@main.route('/edit_device', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_device():
    device_types = [{'type': 'common_device'}, {'type': 'glovebox'}]
    device_types.extend(find_device_types())
    form = EditDeviceForm(device_types)
    if form.validate_on_submit():
        name = form.name.data
        status = form.status.data
        details = form.details.data
        users = form.users.data
        device_type = form.device_type.data
        print(device_type)
        device = Device(name=name)
        device.status = status
        if details:
            device.details = details
        if users:
            users = users.split(',')
            print(users)
            for user in users:
                if len(user) == 0:
                    continue
                user = User.query.filter_by(name=user).first_or_404()
                if user not in device.users:
                    device.users.append(user)
        db.session.add(device)
        db.session.commit()
        flash("Device updated!")
        if device_type == 'common_device':
            baseUrl = BASEURL + '/form/'
            qr_generator(baseUrl, device.id)
        elif device_type == 'glovebox':
            baseUrl = BASEURL + '/form/glovebox/'
            qr_generator(baseUrl, device.id)
        elif device_type is not None:
            baseUrl = BASEURL + '/form/new/' + device_type + '/'
            qr_generator(baseUrl, device.id)
        else:
            pass
        # qr_generator will take more than 2s to generate the img
        # if upload device too fast, it may generate wrong imgs
        # need find a way to solve this problem
    return render_template('edit/edit_device.html', form=form)


@main.route('/edit_user_device', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user_device():
    form = EditUserForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first_or_404()
        name = form.name.data
        devices = form.device.data.split(',')
        if name:
            user.name = name
            db.session.add(user)
        for device in devices:
            device = Device.query.filter_by(id=int(device)).first_or_404()
            device.users.append(user)
            db.session.add(device)
        db.session.commit()
        flash("User device updated!")
    return render_template('edit/edit_user_device.html', form=form)


@main.route('/edit_device_type', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_device_type():
    if request.method == 'POST':
        try:
            r = request.get_json(force=True)
            # print(r)
            device_name = r.pop(0)['device_name']
            field_list = ['id INT NOT NULL AUTO_INCREMENT PRIMARY KEY', 'device_id INT',
                          "device_status VARCHAR(32) DEFAULT 'Normal'",
                          'username VARCHAR(64)', 'email VARCHAR(64)',
                          'start_time DATETIME DEFAULT CURRENT_TIMESTAMP',
                          'end_time DATETIME ON UPDATE CURRENT_TIMESTAMP']
            for field in r:
                field_list.append(field['field_name'] + ' ' + field['field_type'])
            # print(field_list)
            create_table_query = 'CREATE TABLE ' + device_name + ' ( ' + ", ".join(field_list) + ' );'
            # print(create_table_query)
            db.session.execute(create_table_query)
            device_type = DeviceType(type=device_name)
            db.session.add(device_type)
            db.session.commit()
            flash('New Type Device Added!')
            return 'Succeed!', 200
        except Exception as e:
            # print(e)
            db.session.rollback()
            db.session.flush()
            flash('Error occurs: ', str(e))
            return str(e)
    return render_template('/edit/edit_device_type.html')


@main.route('/device_inuse', methods=['GET', 'POST'])
@login_required
@admin_required
def device_inuse():
    return render_template('/edit/reset_device_inuse.html')


@main.route('/device_inuse_json_data', methods=['GET'])
def device_inuse_json_data():
    inuse_devices = Device.query.filter_by(device_inuse=True).all()
    devices = []
    for device in inuse_devices:
        log = find_latest_log_with_certain_device_id(device.id)
        devices.append({
            'id': device.id,
            'name': device.name,
            'current_user': getattr(log, re.findall('user.name', ''.join(log.__table__.columns.keys()))[0]),
            'start_time': tz_local(log.start_time),
        })
    return jsonify({"data": devices})


@main.route('/device_inuse_receive', methods=['POST'])
def device_inuse_receive():
    data = request.get_json(force=True)["data"]
    device_id = int(data[0])
    device = Device.query.filter_by(id=device_id).first()
    device.device_inuse = False
    db.session.commit()
    return url_for('main.device_inuse')


def find_latest_log_with_certain_device_id(device_id):
    devicetypes = DeviceType.query.all()
    Base = automap_base()
    Base.prepare(db.engine,
                 reflect=True)  # use automap of sqlalchemy to get table's corresponding class model
    if DeviceUsageLog.query.filter_by(device_id=device_id).first():
        log = DeviceUsageLog.query.filter_by(device_id=device_id).order_by(desc(DeviceUsageLog.id)).first()
    elif GloveBoxLog.query.filter_by(device_id=device_id).first():
        log = GloveBoxLog.query.filter_by(device_id=device_id).order_by(desc(GloveBoxLog.id)).first()
    else:
        log = None
        for devicetype in devicetypes:
            table = getattr(Base.classes, devicetype.type,
                            None)  # getattr to access attribute like Base.classes.device_type
            query = db.session.query(table).filter_by(device_id=device_id).first()
            if query:
                # device_type = devicetype.type
                log = db.session.query(table).filter_by(device_id=device_id).order_by(desc(table.id)).first()
                break
            else:
                continue
    return log
