import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'this is a secret string!'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'mysql://test:123456@127.0.0.1:3306/restful_api_test'

    # CELERY_BROKER_URL = 'redis://localhost:6379/0'
    # CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672/celeryVhost'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

    SWAGGER = {
        'title': 'Test restful api with swagger',
        'uiversion': 3
    }

    DEBUG = True

    @staticmethod
    def init_app(app):
        pass
