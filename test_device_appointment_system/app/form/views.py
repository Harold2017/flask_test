from . import form
from .forms import LogForm
from flask import render_template
from datetime import datetime
import os
import json


log_folder = os.path.abspath('app') + '\\form\\log\\'


@form.route('/<device_id>', methods=['GET', 'POST'])
def log(device_id):
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
    return render_template('log/log.html', form=form)
