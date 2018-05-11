from flask import render_template, redirect, request, url_for, flash, jsonify
from . import auth
from .. import db
from .. models import User, Device, AppointmentEvents, Permission
from .forms import LoginForm, RegistrationForm, KeyGenerator
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
from sqlalchemy import and_
import os


keys_folder = os.path.abspath("app") + "\\auth\\keys\\"


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print("pass")
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('Welcome %s!' % user.name)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/login/mobile', methods=['POST'])
def loginMobile():
    r = request.get_json(force=True)
    if r is None:
        return "No Data Posted", 404
    username = r['username']
    password = r['password']
    user = User.query.filter_by(email=username).first()
    token = user.avatar_hash
    if user is not None and user.verify_password(password):
        return jsonify({"token": token, "code": 200}), 200


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('See you friend!')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    name=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Welcome on board!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/unlock_key/<device_id>', methods=['GET'])
@login_required
def unlock_key(device_id):
    user = current_user
    device_id = int(device_id)
    keygen = KeyGenerator()
    key = keygen.generator()
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    print(current_time)
    event = AppointmentEvents.query.filter(
        and_(AppointmentEvents.user_id == user.id, AppointmentEvents.device_id == device_id,
             AppointmentEvents.start <= current_time, AppointmentEvents.end > current_time)
    ).first()
    print(event)
    if event:
        with open(keys_folder + str(device_id)+'.txt', 'w') as f:
            f.write(key)
        return jsonify({'key': key}), 200
    else:
        return 'Not found', 404


@auth.route('/check_key/<device_id>', methods=['GET'])
def check_key(device_id):
    # check key from models?
    # but how? need add a time field to key model?
    if not os.path.isfile(keys_folder + device_id + '.txt'):
        return 'Not found', 404
    with open(keys_folder + device_id + '.txt', 'r') as f:
        key = f.read()
    return jsonify({'key': key}), 200


'''@auth.route('/unlock_key/<device_id>', methods=['GET'])
@login_required
# use token, public key on device
# but it may be too hard for implementing this serialization on the device...
# if send the key back for confirm, it is useless for security...
def unlock_key(device_id):
    user = current_user
    device_id = int(device_id)
    device = Device.query.filter_by(id=device_id).first_or_404()

    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    # print(current_time)
    event = AppointmentEvents.query.filter(
        and_(AppointmentEvents.user_id == user.id, AppointmentEvents.device_id == device_id,
             AppointmentEvents.start <= current_time, AppointmentEvents.end > current_time)
    ).first()
    # print(event)

    if event:
        secret_key = device.secret_key
        token = generate_token(secret_key)
        print(token)
        return jsonify({'OK': 'OK'}), 200
        # return jsonify({'token': token}), 200'''


'''def generate_token(secret_key, expiration=3600):
    s = Serializer(secret_key, expiration)
    return s'''
