from sqlalchemy.exc import IntegrityError
import logging
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from datetime import datetime


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')


class BaseModel:

    def __commit(self):
        try:
            db.session.commit()
        except IntegrityError:
            logging.info("Commit data to table {} failed and rollback".format(self.__tablename__))
            db.session.rollback()
            db.session.flush()

    def delete(self):
        db.session.delete(self)
        self.__commit()
        return None

    def save(self):
        db.session.add(self)
        self.__commit()
        return self


class User(UserMixin, BaseModel, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.save()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class AnonymousUser(AnonymousUserMixin):
    pass


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Task(BaseModel, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    start = db.Column(db.DateTime(), default=datetime.utcnow)
    end = db.Column(db.DateTime())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_uuid = db.Column(db.String(64))
    is_finished = db.Column(db.Boolean, default=False)

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start': self.start,
            'end': self.end,
            'is_finished': self.is_finished
        }
