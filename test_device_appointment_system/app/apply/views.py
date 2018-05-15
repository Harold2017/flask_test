from . import apply
from .forms import DeviceForm, ConfirmForm, ApplicationTable, DeviceTable # ChoiceObj
from flask import render_template, flash # session
from flask_login import login_required, current_user
# from ..decorators import admin_required
from ..models import Device, User, user_device, ApplicationLog
from ..email import send_email
from .. import db
from sqlalchemy import desc
import ast
from pytz import timezone


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')


email_receiver = ['peixindu@nami.org.hk', 'jimmywlhon@nami.org.hk']


@apply.route('/device', methods=['GET', 'POST'])
@login_required
def apply_device():
    devices = Device.query.filter(~Device.name.op('regexp')('test.*')).all()
    uds = db.session.query(user_device).filter_by(user_id=current_user.id).all()
    ds = []
    for ud in uds:
        device = Device.query.filter_by(id=ud.device_id).first()
        for d in devices:
            if device.id == d.id:
                devices.remove(d)
                ds.append({
                    "device_id": d.id,
                    "device_name": d.name,
                    "device_status": d.status,
                    "device_details": d.details
                })
    # selectedChoices = ChoiceObj('devices', session.get(selected))
    # form = DeviceForm(obj=selectedChoices, devices=devices)
    if len(ds) == 0:
        table = None
    else:
        table = DeviceTable(ds)
    if len(devices) == 0:
        return render_template('apply/apply_device.html', form=None, table=table)
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
    return render_template('apply/apply_device.html', form=form, table=table)


@apply.route('/confirm/<user_email>', methods=['GET', 'POST'])
@login_required
# @admin_required
def confirm(user_email):
    if current_user.email not in email_receiver and current_user.email != 'harold@harold.com':
        return render_template('403.html'), 403
    application = ApplicationLog.query.filter_by(user_email=user_email).order_by(desc(ApplicationLog.id)).first()
    if application.application_state == 'Apply':
        applications = ApplicationLog.query.filter_by(user_email=user_email).filter_by(application_state='Apply').order_by(desc(ApplicationLog.id)).all()
    # print(type(application.devices))
    # devices = [int(d.strip()) for d in ast.literal_eval(application.devices)]
        for application in applications:
            d_list = []
            id_list = []
            devices = [int(d) for d in ast.literal_eval(application.devices)]
        # print(type(devices))
            for d in devices:
                if d not in id_list:
                    id_list.append(d)
                    d_list.append(Device.query.filter_by(id=d).first())
                else:
                    continue
        form = ConfirmForm(devices=d_list)
        if form.validate_on_submit():
            c_devices = form.device.data
            user = User.query.filter_by(email=user_email).first_or_404()
            d_names = []
            for c_d in c_devices:
                c_d = Device.query.filter_by(id=int(c_d)).first_or_404()
                c_d.users.append(user)
                d_names.append(c_d.name)
                db.session.add(c_d)
            application.approved_devices = c_devices
            application.application_state = 'Approved'
            db.session.add(application)
            try:
                db.session.commit()
                send_email(user_email, 'Application Confirmed',
                      'apply/email/approve',
                       devices=d_names)
                flash('User Device approved.')
            except:
                db.session.rollback()
                db.session.flush()
    else:
        a_dict = {'user_email': application.user_email,
                  'devices': application.devices,
                  'application_time':application.application_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S'),
                  'handled_time': application.handled_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S'),
                  'approved_devices': application.approved_devices,
                  'application_state': application.application_state}
        table = ApplicationTable([a_dict])
        return render_template('apply/handled.html', table=table)
    return render_template('apply/confirm.html', user_email=user_email, form=form)


@apply.route('/reject/<user_email>', methods=['GET', 'POST'])
@login_required
# @admin_required
def reject(user_email):
    # print(user_email)
    if current_user.email not in email_receiver and current_user.email != 'harold@harold.com':
        return render_template('403.html'), 403
    application = ApplicationLog.query.filter_by(user_email=user_email).order_by(desc(ApplicationLog.id)).first()
    application.application_state = 'Rejected'
    try:
        db.session.add(application)
        db.session.commit()
    except:
        db.session.rollback()
        db.session.flush()
    send_email(user_email, 'Application Rejected',
              'apply/email/reject')
    flash('Reject email has been sent to user.')
    return render_template('apply/reject.html')
