from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_mail import Mail
import flask_monitoringdashboard as dashboard


scheduler = APScheduler()
bootstrap = Bootstrap()
db = SQLAlchemy()
mail = Mail()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


dashboard.config.init_from(file='dashboard_config.cfg')


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    db.app = app
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    dashboard.bind(app)
    scheduler.init_app(app)
    scheduler.start()

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .appointment import appointment as appointment_blueprint
    app.register_blueprint(appointment_blueprint, url_prefix='/appointment')

    from .form import form as form_blueprint
    app.register_blueprint(form_blueprint, url_prefix='/form')

    from .apply import apply as apply_blueprint
    app.register_blueprint(apply_blueprint, url_prefix='/apply')

    from .analysis import analysis as analysis_blueprint
    app.register_blueprint(analysis_blueprint, url_prefix='/analysis')

    try:
        return app
    except:
        scheduler.shutdown()
