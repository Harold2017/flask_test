from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from config import Config


db = SQLAlchemy()
# need refer where tasks in to include...
celery = Celery('app', broker=Config.CELERY_BROKER_URL, include=['app.utils'])


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)

    db.init_app(app)

    celery.conf.update(app.config)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api_bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
