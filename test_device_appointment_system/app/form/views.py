from . import form
from .forms import LogForm
from flask import render_template
from datetime import datetime
import os
import json
from ..models import UserLog
from .. import db


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
        user_log = UserLog(user_name=user, device_id=device_id, device_status=status, log_time=log_time, details=details)
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
