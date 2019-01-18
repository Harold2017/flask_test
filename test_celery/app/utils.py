from flask import request
from hashlib import sha512
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import BadData
from . import celery
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')


def get_remote_address():
    address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if not address:
        address = address.encode('utf-8').split(b',')[0].strip()
    return address


def create_browser_id():
    agent = request.headers.get('User-Agent')
    if not agent:
        agent = str(agent).encode('utf-8')
    base_str = "%s|%s" % (get_remote_address(), agent)
    h = sha512()
    h.update(base_str.encode('utf8'))
    return h.hexdigest()


def generate_access_token(current_app, current_user_id):
    expiration = current_app.config.get('TOKEN_LIFETIME', 3600)
    s = Serializer(current_app.config['SECRET_KEY'])
    token = s.dumps((current_user_id, create_browser_id(), expiration))
    return token


def verify_access_token(current_app, current_user_id, token):
    expiration = current_app.config.get('TOKEN_LIFETIME', 3600)
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        user_id, browser_id, _ = s.loads(token, max_age=expiration)
    except BadData:
        return False
    if user_id != current_user_id or create_browser_id() != browser_id:
        return False
    return True


class MyTask(celery.Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('{0!r} failed: {1!r}'.format(task_id, exc))


@celery.task(base=MyTask)
def alert_logger(user_id, task):
        logging.info("Task {task} of {user_id} will expire in 15 mins".format(task=task, user_id=user_id))
