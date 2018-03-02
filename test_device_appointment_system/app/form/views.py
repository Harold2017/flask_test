from . import form
from .forms import LogForm, ItemTable
from flask import render_template
from datetime import datetime
import os
import json
from ..models import UserLog, Device
from .. import db
from pytz import timezone


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')

log_folder = os.path.abspath('app') + '\\form\\log\\'


@form.route('/<device_id>', methods=['GET', 'POST'])
def log(device_id):
    form = LogForm()
    if form.validate_on_submit():
        device_id = int(device_id)
        user = form.user.data
        status = form.status.data
        s = {0: None, 1: True, 2: False}
        status = s.get(status)
        details = form.details.data
        log_time = datetime.utcnow()
        user_log = UserLog(user_name=user, device_id=device_id, device_status=status, log_time=log_time,
                           details=details)
        db.session.add(user_log)
        db.session.commit()
        return render_template('log/success.html')
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
    if UserLog.query.filter_by(device_id=device_id).first():
        d_logs = UserLog.query.filter_by(device_id=device_id).all()
        device_name = Device.query.filter_by(id=device_id).first().name
        ls = []
        for d_log in d_logs:
            d = {'user_name': d_log.user_name,
                 'device_id': d_log.device_id,
                 'device_name': device_name,
                 'device_status': {0: None, 1: 'Normal', 2: 'Broken'}.get(d_log.device_status),
                 'log_time': d_log.log_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S'),
                 'details': d_log.details}
            ls.append(d)
        table = ItemTable(ls)
        warn = 0
    else:
        warn = 'No logs for this device!'
        table = 0
    return render_template('log/device_log.html', warn=warn, table=table)
