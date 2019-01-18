from sqlalchemy.exc import IntegrityError
import logging
from .app import db
from datetime import datetime, timedelta
from . import utils
from celery import uuid
from celery.task.control import revoke


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


class Task(BaseModel, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    expiration = db.Column(db.DateTime())
    task_uuid = db.Column(db.String(64))
    is_finished = db.Column(db.Boolean, default=False)

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_uuid': self.task_uuid,
            'expiration': self.expiration,
            'is_finished': self.is_finished
        }

    @staticmethod
    def get_task_by_id(task_id):
        task = Task.query.filter_by(id=task_id).first()
        if len(task) == 0:
            return None
        else:
            return task.to_json()

    @staticmethod
    def update_task_by_id(task_id, task_info):
        task = Task.query.filter_by(id=task_id).first()
        for key, value in task_info:
            setattr(task, key, value)
        task.save()

    @staticmethod
    def insert_task(task_info):
        task = Task(**task_info)
        task.task_uuid = uuid()
        task.expiration = datetime.strptime(task.expiration, '%Y-%m-%dT%H:%M:%S')

        countdown = (task.expiration - timedelta(0, 60 * 15, 0) - datetime.utcnow()).total_seconds()

        # task reminder 15 mins before expiration
        utils.alert_logger.apply_async(args=[task.to_json()], countdown=countdown,
                                       expires=countdown + 15 * 60, task_id=task.task_uuid)
        task.save()

    @staticmethod
    def delete_task_by_id(task_id):
        task = Task.query.filter_by(id=task_id).first()
        revoke(task.task_uuid, terminate=True)
        task.delete()

    @staticmethod
    def get_tasks_list():
        tasks = Task.query.all()
        if len(tasks) == 0:
            return {}
        res = []
        for task in tasks:
            res.append(task.to_json())
        return {'tasks_list': res}
