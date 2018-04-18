from . import apply
from .forms import DeviceForm, ConfirmForm # ChoiceObj
from flask import render_template, flash # session
from flask_login import login_required, current_user
from ..decorators import admin_required
from ..models import Device, User, user_device, ApplicationLog
from ..email import send_email
from .. import db
from sqlalchemy import desc
import ast


email_receiver = ['peixindu@nami.org.hk', 'jimmywlhon@nami.org.hk']


@apply.route('/device', methods=['GET', 'POST'])
@login_required
def apply_device():
    devices = Device.query.all()
    # selectedChoices = ChoiceObj('devices', session.get(selected))
    # form = DeviceForm(obj=selectedChoices, devices=devices)
    form = DeviceForm(devices=devices)
    if form.validate_on_submit():
        # session['selected'] = form.devices.data
        # print(form.device.data)
        if form.device.data is None:
            flash('Please choose one instrument for application.')
        else:
            device_id = form.device.data
            device_name = []
            for id in device_id:
                device = Device.query.filter_by(id=id).first()
                device_name.append((id, device.name))
            user_email = current_user.email
            application = ApplicationLog(user_email=user_email,
                                        devices=str(device_id))
            try:
                db.session.add(application)
                db.session.commit()
                for i in email_receiver:
                    send_email(i, 'Device Privilege Application',
                            'apply/email/application',
                            user_email=user_email,
                            device_name=device_name)
                flash('Your application has been sent to admin,'
                    ' Please wait for confirmation.')
            except:
                db.session.rollback()
                db.session.flush()
                flash('Some errors occurs, please contact Admin for help.')
    else:
        pass
        # flash(form.errors)
    return render_template('apply/apply_device.html', form=form)


@apply.route('/confirm/<user_email>', methods=['GET', 'POST'])
@login_required
@admin_required
def confirm(user_email):
    application = ApplicationLog.query.filter_by(user_email=user_email).order_by(desc(ApplicationLog.id)).first()
    # print(type(application.devices))
    # devices = [int(d.strip()) for d in ast.literal_eval(application.devices)]
    devices = [int(d) for d in ast.literal_eval(application.devices)]
    # print(type(devices))
    d_list = []
    for d in devices:
        d_list.append(Device.query.filter_by(id=d).first())
    form = ConfirmForm(devices=d_list)
    if form.validate_on_submit():
        c_devices = form.device.data
        user = User.query.filter_by(email=user_email).first_or_404()
        for c_d in c_devices:
            c_d = Device.query.filter_by(id=int(c_d)).first_or_404()
            c_d.users.append(user)
            db.session.add(c_d)
        try:
            db.session.commit()
            flash('User Device Confirmed.')
        except:
            db.session.rollback()
            db.session.flush()
    return render_template('apply/confirm.html', user_email=user_email, form=form)

