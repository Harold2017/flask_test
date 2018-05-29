from . import form
from .forms import StartForm, EndForm, ItemTable, GloveBoxStartForm, \
    GloveBoxEndForm, GloveItemTable, StateTransferForm, generate_form, BookedForm
from flask import render_template, redirect, url_for, request
from datetime import datetime, timedelta
import os
from ..models import Device, DeviceUsageLog, GloveBoxLog, AppointmentEvents, User
from .. import db
from pytz import timezone
from sqlalchemy import desc, Table, MetaData, inspect, and_
from sqlalchemy.ext.automap import automap_base
from flask_table import create_table, Col
from collections import OrderedDict


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')

log_folder = os.path.abspath('app') + '\\form\\log\\'
BASEURL = 'http://namihk.com'


# check booking condition of the scanned QR-code device
# if the device is booked during this time period, only user with booked email can login
# if the booked user not login within 30 mins, the booking will be cancelled and the device will be open for login
def check_booking(device_id):
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
        if event.start <= time - timedelta(seconds=1800):
            db.session.delete(event)
            db.session.commit()
            return None
    return event


@form.route('/<device_id>', methods=['GET', 'POST'])
def log(device_id):
    device_id = int(device_id)
    logs = BASEURL + "/form/device_log/" + str(device_id)
    booked_event = check_booking(device_id)
    if booked_event:
        start = booked_event.start.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S')
        end = booked_event.end.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S')
        user = User.query.filter_by(id=booked_event.user_id).first_or_404()
        # form to collect user email
        form = BookedForm()
        if form.validate_on_submit():
            email = form.email.data
            # if user's email is equal to booked email, then redirect to common login
            if email == user.email:
                return redirect(url_for('form.common_device_login', device_id=device_id, logs=logs))
        return render_template('log/booked.html', username=booked_event.name, start=start,
                               end=end, device_id=device_id, logs=logs, form=form)
    else:
        return redirect(url_for('form.common_device_login', device_id=device_id, logs=logs))


@form.route('/common_device/login', methods=['GET', 'POST'])
def common_device_login():
    device_id = int(request.args['device_id'])
    logs = request.args['logs']
    device = Device.query.filter_by(id=device_id).first_or_404()
    if device.status == 'Normal':
        if device.device_inuse is False:
            form = StartForm()
            if form.validate_on_submit():
                user = form.user.data
                status = form.status.data
                s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
                status = s.get(status)
                details = form.details.data
                start_time = datetime.utcnow()
                material = form.material.data
                try:
                    device_usage_log = DeviceUsageLog(user_name=user, device_id=device_id, device_status=status,
                                                      material=material, details=details)
                    db.session.add(device_usage_log)
                    if status != device.status:
                        device.status = status
                        device.state_transfer = True
                    device.device_inuse = True
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log.html', device_id=device_id, form=form, logs=logs)
        else:
            form = EndForm()
            if form.validate_on_submit():
                status = form.status.data
                s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
                status = s.get(status)
                remarks = form.remarks.data
                product = form.product.data
                end_time = datetime.utcnow()
                try:
                    device_usage_log = DeviceUsageLog.query.filter_by(device_id=device_id).order_by(
                        desc(DeviceUsageLog.id)).first()
                    device_usage_log.end_time = end_time
                    device_usage_log.product = product
                    device_usage_log.remarks = remarks
                    if status != device.status:
                        device.status = status
                        device.state_transfer = True
                    device.device_inuse = False
                    # delete appointment event to release booking check
                    event = AppointmentEvents.query.filter(
                        and_(AppointmentEvents.device_id == device_id,
                             AppointmentEvents.start <= end_time,
                             AppointmentEvents.end >= end_time)
                    ).first()
                    db.session.delete(event)
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log_logout.html', device_id=device_id, form=form, logs=logs)
    elif device.status == 'Terminated':
        return render_template('log/terminated.html')
    else:
        form = StateTransferForm()
        status = device.status
        if form.validate_on_submit():
            status_s = form.status.data
            s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
            status_s = s.get(status_s)
            if status_s == status:
                return
            else:
                try:
                    device.status = status_s
                    device.state_transfer = True
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
        return render_template('log/state_transfer.html', status=status, form=form, logs=logs)


'''def log(device_id):
    form = LogForm()
    if form.validate_on_submit():
        device = form.name.data
        user = form.user.data
        status = form.status.data
        s = {0: None, 1: 'Normal', 2: 'Broken'}
        details = form.details.data
        d = {'device': device,
             'user': user,
             'status': s.get(status),
             'details': details,
             'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
             }
        with open(log_folder + 'log.txt', 'a') as f:
            f.write(json.dumps(d))
            f.write('\n')
        return render_template('log/success.html')
    return render_template('log/log.html', form=form)'''


@form.route('/device_log/<device_id>')
def device_log(device_id):
    device_id = int(device_id)
    if DeviceUsageLog.query.filter_by(device_id=device_id).first():
        d_logs = DeviceUsageLog.query.filter_by(device_id=device_id).filter(
            DeviceUsageLog.start_time <= datetime.utcnow()).filter(
            DeviceUsageLog.start_time >= (datetime.utcnow().date() - timedelta(days=2))).order_by(
            desc(DeviceUsageLog.id)).all()
        if len(d_logs) >= 5:
            d_logs = d_logs[:5]
        else:
            d_logs = DeviceUsageLog.query.filter_by(device_id=device_id).order_by(desc(DeviceUsageLog.id)).limit(
                5).all()
        device_name = Device.query.filter_by(id=device_id).first().name
        ls = []
        for d_log in d_logs:
            d = {'user_name': d_log.user_name,
                 'device_id': d_log.device_id,
                 'device_name': device_name,
                 'device_status': d_log.device_status,
                 'start_time': d_log.start_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S'),
                 'material': d_log.material,
                 'details': d_log.details,

                 'end_time': d_log.end_time.replace(tzinfo=utc).astimezone(tzchina).strftime(
                     '%Y/%m/%d-%H:%M:%S') if d_log.end_time is not None else 'Inuse',
                 'product': d_log.product,
                 'remarks': d_log.remarks
                 }
            ls.append(d)
        table = ItemTable(ls)
        warn = 0
    else:
        warn = 'No logs for this device!'
        table = 0
    return render_template('log/device_log.html', warn=warn, table=table)


@form.route('/glovebox/<device_id>', methods=['GET', 'POST'])
def glovebox(device_id):
    device_id = int(device_id)
    logs = BASEURL + "/form/glovebox/glovebox_log/" + str(device_id)
    booked_event = check_booking(device_id)
    if booked_event:
        start = booked_event.start.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S')
        end = booked_event.end.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S')
        user = User.query.filter_by(id=booked_event.user_id).first_or_404()
        # form to collect user email
        form = BookedForm()
        if form.validate_on_submit():
            email = form.email.data
            # if user's email is equal to booked email, then redirect to common login
            if email == user.email:
                return redirect(url_for('form.glovebox_login', device_id=device_id, logs=logs))
        return render_template('log/booked.html', username=booked_event.name, start=start,
                               end=end, device_id=device_id, logs=logs, form=form)
    else:
        return redirect(url_for('form.glovebox_login', device_id=device_id, logs=logs))


@form.route('/glovebox/login', methods=['GET', 'POST'])
def glovebox_login():
    device_id = int(request.args["device_id"])
    logs = request.args["logs"]
    device = Device.query.filter_by(id=device_id).first()
    if device.status == 'Normal':
        if device.device_inuse is False:
            form = GloveBoxStartForm()
            if form.validate_on_submit():
                user = form.user.data
                status = form.status.data
                s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
                status = s.get(status)
                h2o_before = form.h2o.data
                o2_before = form.o2.data
                ar_before = form.ar.data
                pressure_before = form.pressure.data
                material = form.material.data
                details = form.details.data
                try:
                    gloveboxlog = GloveBoxLog(user_name=user, device_id=device_id, device_status=status,
                                              h2o_before=h2o_before, o2_before=o2_before, ar_before=ar_before,
                                              pressure_before=pressure_before, material=material, details=details)
                    db.session.add(gloveboxlog)
                    if status != device.status:
                        device.status = status
                        device.state_transfer = True
                    device.device_inuse = True
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log.html', device_id=device_id, form=form, logs=logs)
        else:
            form = GloveBoxEndForm()
            if form.validate_on_submit():
                status = form.status.data
                s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
                status = s.get(status)
                h2o_after = form.h2o.data
                o2_after = form.o2.data
                ar_after = form.ar.data
                pressure_after = form.pressure.data
                product = form.product.data
                remarks = form.remarks.data
                try:
                    gloveboxlog = GloveBoxLog.query.filter_by(device_id=device_id).order_by(
                        desc(GloveBoxLog.id)).first()
                    gloveboxlog.h2o_after = h2o_after
                    gloveboxlog.o2_after = o2_after
                    gloveboxlog.ar_after = ar_after
                    gloveboxlog.pressure_after = pressure_after
                    gloveboxlog.product = product
                    gloveboxlog.remarks = remarks
                    if status != device.status:
                        device.status = status
                        device.state_transfer = True
                    device.device_inuse = False
                    # delete appointment event to release booking check
                    end_time = datetime.utcnow()
                    event = AppointmentEvents.query.filter(
                        and_(AppointmentEvents.device_id == device_id,
                             AppointmentEvents.start <= end_time,
                             AppointmentEvents.end >= end_time)
                    ).first()
                    db.session.delete(event)
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log_logout.html', device_id=device_id, form=form, logs=logs)
    elif device.status == 'Terminated':
        return render_template('log/terminated.html')
    else:
        form = StateTransferForm()
        status = device.status
        if form.validate_on_submit():
            status_s = form.status.data
            s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
            status_s = s.get(status_s)
            if status_s == status:
                return
            else:
                try:
                    device.status = status_s
                    device.state_transfer = True
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
        return render_template('log/state_transfer.html', status=status, form=form, logs=logs)


@form.route('/glovebox/glovebox_log/<device_id>')
def glovebox_log(device_id):
    device_id = int(device_id)
    if GloveBoxLog.query.filter_by(device_id=device_id).first():
        g_logs = GloveBoxLog.query.filter_by(device_id=device_id).filter(
            GloveBoxLog.start_time <= datetime.utcnow()).filter(
            GloveBoxLog.start_time >= (datetime.utcnow().date() - timedelta(days=2))).order_by(
            desc(GloveBoxLog.id)).all()
        if len(g_logs) >= 5:
            g_logs = g_logs[:5]
        else:
            g_logs = GloveBoxLog.query.filter_by(device_id=device_id).order_by(desc(GloveBoxLog.id)).limit(5).all()
        device_name = Device.query.filter_by(id=device_id).first().name
        ls = []
        for g_log in g_logs:
            g = {'user_name': g_log.user_name,
                 'device_id': g_log.device_id,
                 'device_name': device_name,
                 'device_status': g_log.device_status,
                 'start_time': g_log.start_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S'),
                 'h2o_before': g_log.h2o_before,
                 'o2_before': g_log.o2_before,
                 'ar_before': g_log.ar_before,
                 'pressure_before': g_log.pressure_before,
                 'material': g_log.material,
                 'details': g_log.details,

                 'end_time': g_log.end_time.replace(tzinfo=utc).astimezone(tzchina).strftime(
                     '%Y/%m/%d-%H:%M:%S') if g_log.end_time is not None else 'Inuse',
                 'h2o_after': g_log.h2o_after,
                 'o2_after': g_log.o2_after,
                 'ar_after': g_log.ar_after,
                 'pressure_after': g_log.pressure_after,
                 'product': g_log.product,
                 'remarks': g_log.remarks
                 }
            ls.append(g)
        table = GloveItemTable(ls)
        warn = 0
    else:
        warn = 'No logs for this glovebox!'
        table = 0
    return render_template('log/device_log.html', warn=warn, table=table)


@form.route('/new/<device_type>/<device_id>', methods=['GET', 'POST'])
def new_log_form(device_type, device_id):
    device_type = str(device_type)
    device_id = int(device_id)
    logs = BASEURL + "/form/new/" + device_type + '/log/' + str(device_id)
    booked_event = check_booking(device_id)
    if booked_event:
        start = booked_event.start.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S')
        end = booked_event.end.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S')
        user = User.query.filter_by(id=booked_event.user_id).first_or_404()
        # form to collect user email
        form = BookedForm()
        if form.validate_on_submit():
            email = form.email.data
            # if user's email is equal to booked email, then redirect to common login
            if email == user.email:
                return redirect(url_for('form.new_device_type_login', device_type=device_type,
                                        device_id=device_id, logs=logs))
        return render_template('log/booked.html', username=booked_event.name, start=start,
                               end=end, device_id=device_id, logs=logs, form=form)
    else:
        return redirect(url_for('form.new_device_type_login', device_type=device_type, device_id=device_id, logs=logs))


@form.route('/new_device_type/login', methods=["GET", "POST"])
def new_device_type_login():
    device_type = request.args["device_type"]
    device_id = request.args["device_id"]
    logs = request.args["logs"]
    device = Device.query.filter_by(id=device_id).first()
    table_description = Table(device_type, MetaData(), autoload=True, autoload_with=db.engine)  # get table description

    Base = automap_base()
    Base.prepare(db.engine, reflect=True)  # use automap of sqlalchemy to get table's corresponding class model
    table = getattr(Base.classes, device_type, None)  # getattr to access attribute like Base.classes.device_type
    if device.status == 'Normal':
        if device.device_inuse is False:
            form = generate_form('login', table_description.columns)
            # pass form type and table's columns to generate
            # corresponding forms
            if form.validate_on_submit():
                s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
                data = {key: form.data[key] for key in form.data.keys() if key != 'submit' and key != 'csrf_token'}
                data['device_status'] = s.get(data['device_status'])
                data['device_id'] = device_id
                data['start_time'] = datetime.utcnow()
                # print(data)
                try:
                    table_log = table(**data)  # passing kwargs to table by unpacking dict
                    db.session.add(table_log)
                    if data['device_status'] != device.status:
                        device.status = data['device_status']
                        device.state_transfer = True
                    device.device_inuse = True
                    db.session.commit()
                    return render_template('log/success.html')
                except Exception as e:
                    db.session.rollback()
                    db.session.flush()
                    print(e)
            return render_template('log/log.html', device_id=device_id, form=form, logs=logs)
        else:
            form = generate_form('logout', table_description.columns)
            if form.validate_on_submit():
                table_log = db.session.query(table).filter_by(device_id=device_id). \
                    order_by(desc(table.id)).first_or_404()
                if form.email.data != table_log.email:
                    return render_template('log/noauth.html')
                s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
                data = {key: form.data[key] for key in form.data.keys() if key != 'submit' and key != 'csrf_token'}
                data['device_status'] = s.get(data['device_status'])
                data['end_time'] = datetime.utcnow()
                try:
                    for key, value in data.items():
                        setattr(table_log, key, value)  # set table_log.attr to value
                    if data['device_status'] != device.status:
                        device.status = data['device_status']
                        device.state_transfer = True
                    device.device_inuse = False
                    # delete appointment event to release booking check
                    event = AppointmentEvents.query.filter(
                        and_(AppointmentEvents.device_id == device_id,
                             AppointmentEvents.start <= data["end_time"],
                             AppointmentEvents.end >= data["end_time"])
                    ).first()
                    db.session.delete(event)
                    db.session.commit()
                    return render_template('log/success.html')
                except Exception as e:
                    db.session.rollback()
                    db.session.flush()
                    print(e)
            return render_template('log/log_logout.html', device_id=device_id, form=form, logs=logs)
    elif device.status == 'Terminated':
        return render_template('log/terminated.html')
    else:
        form = StateTransferForm()
        status = device.status
        if form.validate_on_submit():
            status_s = form.status.data
            s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
            status_s = s.get(status_s)
            if status_s == status:
                return
            else:
                try:
                    device.status = status_s
                    device.state_transfer = True
                    db.session.commit()
                    return render_template('log/success.html')
                except Exception as e:
                    db.session.rollback()
                    db.session.flush()
                    print(e)
        return render_template('log/state_transfer.html', status=status, form=form, logs=logs)


def row2dict(row):
    dict = {column.key: getattr(row, column.key) for column in inspect(row).mapper.column_attrs}
    try:
        del dict["email"]
        del dict["id"]
    except KeyError as e:
        print("No such key: '%s'" % e)
    finally:
        return dict


def row2ordereddict(row):
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


@form.route('/new/<device_type>/log/<device_id>')
def new_log(device_type, device_id):
    device_type = str(device_type)
    device_id = int(device_id)

    Base = automap_base()
    Base.prepare(db.engine, reflect=True)  # use automap of sqlalchemy to get table's corresponding class model
    table = getattr(Base.classes, device_type, None)  # getattr to access attribute like Base.classes.device_type

    if db.session.query(table).filter_by(device_id=device_id).first():
        # search logs within two days first
        table_logs = db.session.query(table).filter_by(device_id=device_id). \
            filter(table.start_time <= datetime.utcnow()). \
            filter(table.start_time >= (datetime.utcnow() - timedelta(days=2))). \
            order_by(desc(table.id)).all()
        # display the latest 5 records
        if len(table_logs) >= 5:
            table_logs = table_logs[:5]
        else:
            table_logs = db.session.query(table).filter_by(device_id=device_id).order_by(desc(table.id)).limit(5).all()

        # get device name
        device_name = Device.query.filter_by(id=device_id).first().name

        log_list = []
        for table_log in table_logs:
            # log = row2dict(table_log)
            log = row2ordereddict(table_log)
            log["start_time"] = log["start_time"].replace(tzinfo=utc).astimezone(tzchina).strftime(
                "%Y/%m/%d-%H:%M:%S")
            log["end_time"] = log["end_time"].replace(tzinfo=utc).astimezone(tzchina).strftime(
                "%Y/%m/%d-%H:%M:%S") if table_log.end_time is not None else 'Inuse'
            log["device_name"] = device_name
            log.move_to_end('device_name', last=False)
            log_list.append(log)

        # print(log_list)
        # table = generate_table(log_list[0])(log_list)
        TableCls = create_table('TableCls', options=dict(classes=['table', 'table-bordered'], no_items='Empty'))
        for key in log_list[0].keys():
            TableCls.add_column(key, Col(key.capitalize()))
        table = TableCls(log_list)
        # print(table.__html__())
        warn = 0
    else:
        warn = 'No logs for this device!'
        table = 0
    return render_template('log/device_log.html', warn=warn, table=table)
