from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from . import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
import string
import random
import time


class Permission:
    USER = 0x01
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.USER, True),
            'Administrator': (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role {0}>'.format(self.name)


# user_id and device_id consist a primary key together
user_device = db.Table('user_device',
                       db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                       db.Column('device_id', db.Integer, db.ForeignKey('devices.id'), primary_key=True)
                       )


class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    status = db.Column(db.Boolean, default=True, index=True)
    details  = db.Column(db.Text())
    # secret_key = db.Column(db.String(64))
    # devices and users have a middle-table user_device
    # if get a user, then backref to devices to find all devices the user has
    users = db.relationship('User', secondary=user_device, lazy='subquery',
                            backref=db.backref('devices', lazy=True))
    # add in-use to determine whether the device is in use
    device_inuse = db.Column(db.Boolean, default=False)
    '''def __init__(self):
        keygen = KeyGenerator()
        key = keygen.generator()
        self.secret_key = key
        db.session.add(self)
        db.session.commit()'''


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    avatar_hash = db.Column(db.String(32))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    @property
    def __repr__(self):
        return '<User {0}>'.format(self.name)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AppointmentEvents(db.Model):
    __tablename__ = 'appointmentevents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, index=True)
    device_id = db.Column(db.Integer, index=True)
    start = db.Column(db.DateTime(), default=datetime.utcnow)
    end = db.Column(db.DateTime())
    remark = db.Column(db.Text())

    def __repr__(self):
        return '<Event {0} on device {1} appointed by {2}>'.format(self.id, self.device_id, self.user_id)


'''class Key(db.Model):
    __tablename__ = 'keys'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer)
    key = db.Column(db.String(64))

    def __init__(self):
        keygen = KeyGenerator()
        key = keygen.generator()
        self.secret_key = key
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<Secret key {0}> for <Event {1}>'.format(self.id, self.event_id)'''


'''class KeyGenerator:
    def __init__(self, size=6, chars=string.ascii_uppercase + string.digits):
        random.seed(time.time())
        self.size = size
        self.chars = chars

    def generator(self):
        return ''.join(random.choice(self.chars) for x in range(self.size))'''


class UserLog(db.Model):
    __tablename__ = 'userlogs'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64))
    device_id = db.Column(db.Integer)
    device_status = db.Column(db.Boolean, default=True, index=True)
    log_time = db.Column(db.DateTime(), default=datetime.utcnow)
    details = db.Column(db.Text())


class DeviceUsageLog(db.Model):
    __tablename__ = 'deviceusagelogs'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64))
    device_id = db.Column(db.Integer)
    device_status = db.Column(db.Boolean, default=True, index=True)
    start_time = db.Column(db.DateTime(), default=datetime.utcnow)
    end_time = db.Column(db.DateTime()) # onupdate=datetime.utcnow)
    material = db.Column(db.String(64))
    product = db.Column(db.String(64))
    details = db.Column(db.Text())
    remarks = db.Column(db.Text())


class GloveBoxLog(db.Model):
    __tablename__ = 'gloveboxlogs'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64))
    device_id = db.Column(db.Integer)
    device_status = db.Column(db.Boolean, default=True, index=True)
    h2o_before = db.Column(db.Float)
    o2_before = db.Column(db.Float)
    ar_before = db.Column(db.Float)
    pressure_before = db.Column(db.Float)
    start_time = db.Column(db.DateTime(), default=datetime.utcnow)
    material = db.Column(db.String(128))
    details = db.Column(db.Text())

    h2o_after = db.Column(db.Float)
    o2_after = db.Column(db.Float)
    ar_after = db.Column(db.Float)
    pressure_after = db.Column(db.Float)
    end_time = db.Column(db.DateTime(), onupdate=datetime.utcnow)
    product = db.Column(db.String(128))
    remarks = db.Column(db.Text())


class JobLog(db.Model):
    __tablename__ = 'joblogs'
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(64))
    excute_time = db.Column(db.DateTime(), default=datetime.utcnow)
    excute_status = db.Column(db.Boolean, default=True, index=True)
    result = db.Column(db.Text(), default=None)

