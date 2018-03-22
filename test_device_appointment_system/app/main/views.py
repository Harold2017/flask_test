from flask import request, render_template, jsonify, flash
from . import main
from .. import db
from ..models import User, Device, Permission, user_device, AnonymousUser
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from .forms import EditUserForm, Item, ItemTable, EditDeviceForm
from ..QRcode.QRcode import qr_generator


def find_users(device):
    uds = db.session.query(user_device).filter_by(device_id=device.id).all()
    users = []
    for ud in uds:
        user = User.query.filter_by(id=ud.user_id).first()
        users.append({"id": user.id, "name": user.name})
    return users


def find_devices(user):
    uds = db.session.query(user_device).filter_by(user_id=user.id).all()
    devices = []
    for ud in uds:
        device = Device.query.filter_by(id=ud.device_id).first()
        devices.append({"id": device.id, "name": device.name})
    return devices


@main.route('/', methods=['GET', 'POST'])
def index():
    show_edit = False
    # print(current_user.is_administrator())
    # print(isinstance(current_user, AnonymousUser))
    # print(isinstance(current_user, User))
    if current_user.is_administrator():
        show_edit = True
    return render_template("index.html", show_edit=show_edit)


@main.route('/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit():
    devices = Device.query.all()
    users = User.query.all()
    # ud = db.session.query(user_device).filter_by(device_id=devices[0].id).all()
    # print(ud[0].user_id)
    '''if devices is not None:
        table = ItemTable(devices)
    else:
        table = None'''
    device_list = []
    for device in devices:
        img_path = "../static/QRcode/Device" + str(device.id) + '.png'
        device_list.append({"id": device.id,
                            "name": device.name,
                            "status": device.status,
                            "details": device.details,
                            "img_path": img_path,
                            "users": find_users(device)})

    user_list = []
    for user in users:
        user_list.append({"id": user.id,
                          "name": user.name,
                          "devices": find_devices(user)})

    return render_template('edit/edit.html', devices=device_list, users=user_list)


@main.route('/edit_device', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_device():
    form = EditDeviceForm()
    if form.validate_on_submit():
        name = form.name.data
        status = form.status.data
        details = form.details.data
        users = form.users.data
        device = Device(name=name)
        if status:
            device.status = True if status == 'True' else False
        if details:
            device.details = details
        if users:
            users = users.split(',')
            print(users)
            for user in users:
                if len(user) == 0:
                    continue
                user = User.query.filter_by(name=user).first_or_404()
                if user not in device.users:
                    device.users.append(user)
        db.session.add(device)
        db.session.commit()
        flash("Device updated!")
        qr_generator(device.id)
        # qr_generator will take more than 2s to generate the img
        # if upload device too fast, it may generate wrong imgs
        # need find a way to solve this problem
    return render_template('edit/edit_device.html', form=form)


@main.route('/edit_user_device', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user_device():
    form = EditUserForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first_or_404()
        name = form.name.data
        devices = form.device.data.split(',')
        if name:
            user.name = name
            db.session.add(user)
        for device in devices:
            device = Device.query.filter_by(id=int(device)).first_or_404()
            device.users.append(user)
            db.session.add(device)
        db.session.commit()
        flash("User device updated!")
    return render_template('edit/edit_user_device.html', form=form)
