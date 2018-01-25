from flask import render_template, redirect, request, url_for, flash, jsonify
from . import auth
from .. import db
from .. models import User, Device, AppointmentEvents
from .forms import LoginForm, RegistrationForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print("pass")
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
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


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Welcome on board!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)
