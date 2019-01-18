from flask import Flask, request
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from .views import TasksListHandler, TaskHandler


app = Flask(__name__)
app.config['SECRET_KEY'] = 'this is a secret string!'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://test:123456@127.0.0.1:3306/restful_api_test'

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

db = SQLAlchemy()
db.init_app(app)
celery = Celery('app', broker=app.config['CELERY_BROKER_URL'], include=['app.utils'])
# need refer where tasks in to include...
celery.conf.update(app.config)

api = Api(app)
api.add_resource(TasksListHandler, '/tasks/')
api.add_resource(TaskHandler, '/task/<task_id>')


# debug
@app.before_request
def before_request():
    ip = request.remote_addr
    url = request.url
    form = request.form
    args = request.args
    values = request.values
    headers = request.headers
    method = request.method
    path = request.path
    base_url = request.base_url
    url_root = request.url_root
    # print(url)
    # print(args)


@app.route('/')
def hello():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
