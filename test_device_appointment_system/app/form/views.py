from . import form
from .forms import StartForm, EndForm, ItemTable, GloveBoxStartForm, \
        GloveBoxEndForm, GloveItemTable, StateTransferForm
from flask import render_template
from datetime import datetime
import os
import json
from ..models import Device, DeviceUsageLog, GloveBoxLog
from .. import db
from pytz import timezone
from sqlalchemy import desc


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')

log_folder = os.path.abspath('app') + '\\form\\log\\'
BASEURL = 'http://namihk.com'


@form.route('/<device_id>', methods=['GET', 'POST'])
def log(device_id):
    device_id = int(device_id)
    device = Device.query.filter_by(id=device_id).first()
    logs = BASEURL + "/form/device_log/" + str(device_id)
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
                    device_usage_log = DeviceUsageLog(user_name=user, device_id=device_id, device_status=status, material=material, details=details)
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
                    device_usage_log = DeviceUsageLog.query.filter_by(device_id=device_id).order_by(desc(DeviceUsageLog.id)).first()
                    device_usage_log.end_time = end_time
                    device_usage_log.product = product
                    device_usage_log.remarks = remarks
                    if status != device.status:
                        device.status = status
                        device.state_transfer = True
                    device.device_inuse = False
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log_logout.html', form=form, logs=logs)
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
        d_logs = DeviceUsageLog.query.filter_by(device_id=device_id).all()
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

                 'end_time': d_log.end_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S') if d_log.end_time is not None else 'Inuse',
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
    device = Device.query.filter_by(id=device_id).first()
    if GloveBoxLog.query.filter_by(device_id=device_id).first():
        logs = BASEURL + "/form/glovebox/glovebox_log/" + str(device_id)
    else:
        logs = None
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
                    gloveboxlog = GloveBoxLog(user_name=user, device_id=device_id, device_status=status, h2o_before=h2o_before, o2_before=o2_before, ar_before=ar_before, pressure_before=pressure_before, material=material, details=details)
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
                    gloveboxlog = GloveBoxLog.query.filter_by(device_id=device_id).order_by(desc(GloveBoxLog.id)).first()
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
                    db.session.commit()
                    return render_template('log/success.html')
                except:
                    db.session.rollback()
                    db.session.flush()
            return render_template('log/log_logout.html', form=form, logs=logs)
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
        g_logs = GloveBoxLog.query.filter_by(device_id=device_id).all()
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

                 'end_time': g_log.end_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S') if g_log.end_time is not None else 'Inuse',
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
