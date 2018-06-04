from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for


class Permission:
    USER = 0x01
    ADMINISTER = 0x80


class BaseOperationModel:
    def __commit(self):
        try:
            db.session.commit()
        except:
            db.session.rollback()
            db.session.flush()

    def save(self):
        db.session.add(self)
        self.__commit()
        return self

    def delete(self):
        db.session.delete(self)
        self.__commit()
        return None


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


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    todo_lists = db.relationship('Todo_list', backref='users', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Todo_list(db.Model, BaseOperationModel):
    __tablename__ = 'todo_lists'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator = db.Column(db.String(64), db.ForeignKey('users.username'))
    todos = db.relationship('Todo', backref='todo_lists', lazy='dynamic')

    def __init__(self, title=None, creator=None, created_at=None):
        self.title = title or 'untitled'
        self.creator = creator
        self.created_at = created_at or datetime.utcnow()

    @property
    def todos_url(self):
        url = None
        kwargs = dict(todo_list_id=self.id, _external=True)
        if self.creator:
            kwargs['username'] = self.creator
            url = 'api.get_user_todo_list_todos'
            return url_for(url, **kwargs)

    def to_dict(self):
        return {
            'title': self.title,
            'creator': self.creator,
            'created_at': self.created_at,
            'total_todo_count': self.todo_count,
            'open_todo_count': self.open_count,
            'finished_to_count': self.finished_count,
            'todos': self.todos_url
        }

    @property
    def todo_count(self):
        return self.todos.order_by(None).count()

    @property
    def open_todo_count(self):
        return self.todos.filter_by(is_finished=False).count()

    @property
    def finished_todo_count(self):
        return self.todos.filter_by(is_finished=True).count()


class Todo(db.Model, BaseOperationModel):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text())
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, index=True, default=None)
    is_finished = db.Column(db.Boolean, default=False)
    creator = db.Column(db.String(64), db.ForeignKey('users.username'))
    todo_list_id = db.Column(db.Integer, db.ForeignKey('todo_lists.id'))

    def __init__(self, description, todo_list_id, creator=None, created_at=None):
        self.description = description
        self.todo_list_id = todo_list_id
        self.created_at = created_at or datetime.utcnow()

    @property
    def status(self):
        return 'finished' if self.is_finished else 'open'

    def finished(self):
        self.is_finished = True
        self.finished_at = datetime.utcnow()
        self.save()

    def reopen(self):
        self.is_finished = False
        self.finished_at = None
        self.save()

    def to_dict(self):
        return {
            'description': self.description,
            'creator': self.creator,
            'created_at': self.created_at,
            'status': self.status
        }
