from . import form
from .forms import StartForm, EndForm, ItemTable, GloveBoxStartForm, \
    GloveBoxEndForm, GloveItemTable, StateTransferForm, BookedForm
from flask import render_template, redirect, url_for, request
from datetime import datetime
from ..models import Device, DeviceUsageLog, GloveBoxLog, AppointmentEvents, User
from .. import db
from sqlalchemy import desc, Table, MetaData, and_
from flask_table import create_table, Col
from .utils import check_booking, find_database_table, generate_table, tz_local, query_new_log, generate_form


BASEURL = 'http://namihk.com'


@form.route('/<device_id>', methods=['GET', 'POST'])
def log(device_id):
    device_id = int(device_id)
    logs = BASEURL + "/form/device_log/" + str(device_id)
    booked_event = check_booking(device_id)
    if booked_event:
        start = tz_local(booked_event.start)
        end = tz_local(booked_event.end)
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
                # start_time = datetime.utcnow()
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
            device_usage_log = DeviceUsageLog.query.filter_by(device_id=device_id).order_by(
                desc(DeviceUsageLog.id)).first_or_404()
            username = device_usage_log.user_name
            if form.validate_on_submit():
                status = form.status.data
                s = {0: None, 1: 'Normal', 2: 'Broken', 3: 'Fixing', 4: 'Terminated'}
                status = s.get(status)
                remarks = form.remarks.data
                product = form.product.data
                end_time = datetime.utcnow()
                try:
                    device_usage_log.end_time = end_time
                    device_usage_log.product = product
                    device_usage_log.remarks = remarks
                    if status != device.status:
                        device.status = status
                        device.state_transfer = True
                    device.device_inuse = False
                    # delete appointment event to release booking check
                    # use is_finished field instead of delete event to mark event is completed
                    event = AppointmentEvents.query.filter(
                        and_(AppointmentEvents.device_id == device_id,
                             AppointmentEvents.start <= end_time,
                             AppointmentEvents.end >= end_time)
                    ).first()
                    if event and not event.is_finished:
                        # db.session.delete(event)
                        event.is_finished = True
                        db.session.add(event)
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log_logout.html', device_id=device_id, form=form, logs=logs, username=username)
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


def query_device_log(device_id, limit=5, offset=0):
    d_logs = DeviceUsageLog.query.filter_by(device_id=device_id).order_by(desc(DeviceUsageLog.id)). \
        limit(limit).offset(offset).all()
    device_name = Device.query.filter_by(id=device_id).first().name
    ls = []
    for d_log in d_logs:
        d = {'user_name': d_log.user_name,
             'device_id': d_log.device_id,
             'device_name': device_name,
             'device_status': d_log.device_status,
             'start_time': tz_local(d_log.start_time),
             'material': d_log.material,
             'details': d_log.details,

             'end_time': tz_local(d_log.end_time) if d_log.end_time is not None else 'Inuse',
             'product': d_log.product,
             'remarks': d_log.remarks
             }
        ls.append(d)
    return ls


@form.route('/device_log/<device_id>', methods=['GET', 'POST'])
def device_log(device_id):
    device_id = int(device_id)
    try:
        offset = request.get_json(force=True).get("offset")
    except:
        offset = None
    if offset is None:
        offset = 0
    else:
        offset = offset
    # print(offset)
    if DeviceUsageLog.query.filter_by(device_id=device_id).first() and offset == 0:
        ls = query_device_log(device_id)
        table = ItemTable(ls)
        warn = 0
    elif offset == 0:
        warn = 'No logs for this device!'
        table = 0
    else:
        ls = query_device_log(device_id, offset=offset)
        table = ItemTable(ls)
        return table.__html__()
    return render_template('log/device_log.html', warn=warn, table=table,
                           url=url_for('form.device_log', device_id=device_id))


@form.route('/glovebox/<device_id>', methods=['GET', 'POST'])
def glovebox(device_id):
    device_id = int(device_id)
    logs = BASEURL + "/form/glovebox/glovebox_log/" + str(device_id)
    booked_event = check_booking(device_id)
    if booked_event:
        start = tz_local(booked_event.start)
        end = tz_local(booked_event.end)
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
            gloveboxlog = GloveBoxLog.query.filter_by(device_id=device_id).order_by(
                desc(GloveBoxLog.id)).first_or_404()
            username = gloveboxlog.user_name
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
                    if event and not event.is_finished:
                        # db.session.delete(event)
                        event.is_finished = True
                        db.session.add(event)
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log_logout.html', device_id=device_id, form=form, logs=logs, username=username)
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


def query_glovebox_log(device_id, limit=5, offset=0):
    g_logs = GloveBoxLog.query.filter_by(device_id=device_id).order_by(desc(GloveBoxLog.id)). \
        limit(limit).offset(offset).all()
    device_name = Device.query.filter_by(id=device_id).first().name
    ls = []
    for g_log in g_logs:
        g = {'user_name': g_log.user_name,
             'device_id': g_log.device_id,
             'device_name': device_name,
             'device_status': g_log.device_status,
             'start_time': tz_local(g_log.start_time),
             'h2o_before': g_log.h2o_before,
             'o2_before': g_log.o2_before,
             'ar_before': g_log.ar_before,
             'pressure_before': g_log.pressure_before,
             'material': g_log.material,
             'details': g_log.details,

             'end_time': tz_local(g_log.end_time) if g_log.end_time is not None else 'Inuse',
             'h2o_after': g_log.h2o_after,
             'o2_after': g_log.o2_after,
             'ar_after': g_log.ar_after,
             'pressure_after': g_log.pressure_after,
             'product': g_log.product,
             'remarks': g_log.remarks
             }
        ls.append(g)
    return ls


@form.route('/glovebox/glovebox_log/<device_id>', methods=['GET', 'POST'])
def glovebox_log(device_id):
    device_id = int(device_id)
    try:
        offset = request.get_json(force=True).get("offset")
    except:
        offset = None
    if offset is None:
        offset = 0
    else:
        offset = offset
    if GloveBoxLog.query.filter_by(device_id=device_id).first() and offset == 0:
        ls = query_glovebox_log(device_id)
        table = GloveItemTable(ls)
        warn = 0
    elif offset == 0:
        warn = 'No logs for this glovebox!'
        table = 0
    else:
        ls = query_glovebox_log(device_id, offset=offset)
        table = GloveItemTable(ls)
        return table.__html__()
    return render_template('log/device_log.html', warn=warn, table=table,
                           url=url_for('form.glovebox_log', device_id=device_id))


@form.route('/new/<device_type>/<device_id>', methods=['GET', 'POST'])
def new_log_form(device_type, device_id):
    device_type = str(device_type)
    device_id = int(device_id)
    logs = BASEURL + "/form/new/" + device_type + '/log/' + str(device_id)
    booked_event = check_booking(device_id)
    if booked_event:
        start = tz_local(booked_event.start)
        end = tz_local(booked_event.end)
        user = User.query.filter_by(id=booked_event.user_id).first_or_404()
        # form to collect user email
        form = BookedForm()
        table = generate_table(device_type, device_id)
        if form.validate_on_submit():
            email = form.email.data
            # if user's email is equal to booked email, then redirect to common login
            if email == user.email:
                return redirect(url_for('form.new_device_type_login', device_type=device_type,
                                        device_id=device_id, logs=logs))
        return render_template('log/booked.html', username=booked_event.name, start=start,
                               end=end, device_id=device_id, logs=logs, form=form, table=table)
    else:
        return redirect(url_for('form.new_device_type_login', device_type=device_type, device_id=device_id, logs=logs))


@form.route('/new_device_type/login', methods=["GET", "POST"])
def new_device_type_login():
    device_type = request.args["device_type"]
    device_id = request.args["device_id"]
    logs = request.args["logs"]
    device = Device.query.filter_by(id=device_id).first()

    table_description = Table(device_type, MetaData(), autoload=True, autoload_with=db.engine)  # get table description

    table = find_database_table(device_type)
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
            device_table = generate_table(device_type, device_id)
            table_log = db.session.query(table).filter_by(device_id=device_id). \
                order_by(desc(table.id)).first_or_404()
            username = table_log.username
            if form.validate_on_submit():
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
                    if event and not event.is_finished:
                        # db.session.delete(event)
                        event.is_finished = True
                        db.session.add(event)
                    db.session.commit()
                    return render_template('log/success.html')
                except Exception as e:
                    db.session.rollback()
                    db.session.flush()
                    print(e)
            return render_template('log/log_logout.html', device_id=device_id, form=form, logs=logs,
                                   table=device_table, username=username)
    elif device.status == 'Terminated':
        device_table = generate_table(device_type, device_id)
        return render_template('log/terminated.html', table=device_table)
    else:
        form = StateTransferForm()
        device_table = generate_table(device_type, device_id)
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
        return render_template('log/state_transfer.html', status=status, form=form, logs=logs, table=device_table)


@form.route('/new/<device_type>/log/<device_id>', methods=['GET', 'POST'])
def new_log(device_type, device_id):
    device_type = str(device_type)
    device_id = int(device_id)
    table = find_database_table(device_type)
    try:
        offset = request.get_json(force=True).get("offset")
    except:
        offset = None
    if offset is None:
        offset = 0
    else:
        offset = offset
    if db.session.query(table).filter_by(device_id=device_id).first() and offset == 0:
        log_list = query_new_log(table, device_id)
        TableCls = create_table('TableCls', options=dict(classes=['table', 'table-bordered'], no_items='No Items'))
        for key in log_list[0].keys():
            TableCls.add_column(key, Col(key.capitalize()))
        table = TableCls(log_list)
        # print(table.__html__())
        warn = 0
    elif offset == 0:
        warn = 'No logs for this device!'
        table = 0
    else:
        log_list = query_new_log(table, device_id, offset=offset)
        TableCls = create_table('TableCls', options=dict(classes=['table', 'table-bordered'], no_items='No Items'))
        if len(log_list) != 0:
            for key in log_list[0].keys():
                TableCls.add_column(key, Col(key.capitalize()))
        table = TableCls(log_list)
        return table.__html__()
    return render_template('log/device_log.html', warn=warn, table=table,
                           url=url_for('form.new_log', device_type=device_type, device_id=device_id))
