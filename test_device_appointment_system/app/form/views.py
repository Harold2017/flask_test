from . import form
from .forms import StartForm, EndForm, ItemTable
from flask import render_template
from datetime import datetime
import os
import json
from ..models import Device, DeviceUsageLog
from .. import db
from pytz import timezone
from sqlalchemy import desc


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')

log_folder = os.path.abspath('app') + '\\form\\log\\'


@form.route('/<device_id>', methods=['GET', 'POST'])
def log(device_id):
    device_id = int(device_id)
    device = Device.query.filter_by(id=device_id).first()
    if device.device_inuse is False:
        form = StartForm()
        if form.validate_on_submit():
            user = form.user.data
            status = form.status.data
            s = {0: None, 1: True, 2: False}
            status = s.get(status)
            details = form.details.data
            start_time = datetime.utcnow()
            material = form.material.data
            try:
                device_usage_log = DeviceUsageLog(user_name=user, device_id=device_id, device_status=status, material=material, details=details)
                db.session.add(device_usage_log)
                device.device_inuse = True
                db.session.commit()
                return render_template('log/success.html')
            except:
                db.session.rollback()
                db.session.flush()
    else:
        form = EndForm()
        if form.validate_on_submit():
            status = form.status.data
            s = {0: None, 1: True, 2: False}
            status = s.get(status)
            remarks = form.remarks.data
            product = form.product.data
            #  end_time = datetime.utcnow()
            try:
                device_usage_log = DeviceUsageLog.query.filter_by(device_id=device_id).order_by(desc(DeviceUsageLog.id)).first()
                # device_usage_log.end_time = end_time
                device_usage_log.product = product
                device_usage_log.remarks = remarks
                device.device_inuse = False
                db.session.commit()
                return render_template('log/success.html')
            except:
                db.session.rollback()
                db.session.flush()
    return render_template('log/log.html', form=form)


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
                 'device_status': {0: None, 1: 'Normal', 2: 'Broken'}.get(d_log.device_status),
                 'start_time': d_log.start_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S'),
                 'material': d_log.material,
                 'details': d_log.details,

                 'end_time': d_log.end_time,
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
