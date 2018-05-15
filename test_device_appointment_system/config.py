import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '%$D2LxZ&K6JLtM%?N4@Rs5wC9cqj$syCm&W7'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RECAPTCHA_PUBLIC_KEY = '6LdIRz8UAAAAAJYJRrZuKDlRQTehaRE9uTcVsO9A'
    RECAPTCHA_PRIVATE_KEY = '6LdIRz8UAAAAAOjNSx8JsZtZtpdTMRyWelAvYSIY'
    ADMIN = 'harold@harold.com'
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = 'NAMIHK'
    MAIL_SENDER = 'NAMIHK'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              ('mysql://flask_test:123456@localhost/device_appointment_system')


class TestingConfig(Config):
    TESTING = True
    RECAPTCHA_DISABLE = True
    WTF_CSRF_METHODS = []  # This is the magic
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              ('mysql://flask_test:123456@localhost/device_appointment_system')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              ('mysql://flask_test:123456@localhost/device_appointment_system')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': TestingConfig
}
