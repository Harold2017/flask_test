from flask import render_template, flash, redirect, url_for, request
from . import appointment
from .. import db
from ..models import Device, user_device, User
from flask_login import login_required, current_user
from .forms import DeviceSelectionForm


def find_devices(user):
    uds = db.session.query(user_device).filter_by(user_id=user.id).all()
    devices = []
    for ud in uds:
        device = Device.query.filter_by(id=ud.device_id).first()
        devices.append({"id": device.id,
                        "name": device.name,
                        "status": device.status,
                        "details": device.details})
    return devices


@appointment.route('/', methods=['GET', 'POST'])
@login_required
def select_device():
    devices = find_devices(current_user)
    if len(devices) == 0:
        flash("You have no access to any devices!")
        return render_template("appointment/select_device.html", devices=None, form=None)
    devices_for_selection = list(devices)
    for device in devices_for_selection:
        if not device['status']:
            devices_for_selection.remove(device)
    form = DeviceSelectionForm(devices_for_selection)
    if form.validate_on_submit():
        selected_device = form.device.data
        flash('Device Selected!')
        return redirect(url_for('appointment.calendar', selected_device=selected_device))
    return render_template("appointment/select_device.html", devices=devices, form=form)


@appointment.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    selected_device = request.args['selected_device']
    # print(selected_device)
    # print(url_for('api.return_data', device_id=selected_device))
    user = User.query.filter_by(id=current_user.id).first()
    token = user.avatar_hash
    return render_template("appointment/calendar.html", device_id=selected_device, token=token)
