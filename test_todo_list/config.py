import os


BASEDIR = os.path.abspath(os.path.dirname(__file__))


def create_sqlite_url(db_name):
    return 'sqlite:///' + os.path.join(BASEDIR, db_name)


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = create_sqlite_url('todo_list-dev.db')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = create_sqlite_url('todo_list-test.db')
    WTF_CSRF_ENABLED = False
    import logging
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s'
    )
    logging.getLogger().setLevel(logging.DEBUG)


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = create_sqlite_url('todo_list.db')


config = {
    'development': DevelopmentConfig,
    'test': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
