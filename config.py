import logging
import os
from logging.handlers import RotatingFileHandler, SMTPHandler

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class BaseConfig:
    APP_NAME = os.environ.get('APP_NAME', 'flygram')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key')
    SESSION_LIFETIME = int(os.environ.get('SESSION_LIFETIME') or 30)
    TOKEN_LIFETIME = int(os.environ.get('TOKEN_LIFETIME') or 10)
    PASSWORD_TOKEN_LIFETIME = int(os.environ.get('PASSWORD_TOKEN_LIFETIME') or 600)
    EMAIL_TOKEN_LIFETIME = int(os.environ.get('EMAIL_TOKEN_LIFETIME') or 600)

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    ADMINS = ['develop.nikita@yandex.ru']

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    APP_URL = os.environ.get('APP_URL') or 'http://localhost'
    REDIS_URL = os.environ.get('REDIS_URL', "redis://localhost")

    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', os.environ.get('UPLOAD_FOLDER') or 'images')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    CACHE_TYPE = 'redis'
    CACHE_IGNORE_ERRORS = False
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

    TWO_FACTOR_MIN_CODE = int(os.environ.get('TWO_FACTOR_MIN_CODE') or 1000)
    TWO_FACTOR_MAX_CODE = int(os.environ.get('TWO_FACTOR_MAX_CODE') or 9999)

    VK_OAUTH2_ID = os.environ.get('VK_OAUTH2_ID')
    VK_OAUTH2_KEY = os.environ.get('VK_OAUTH2_KEY')
    VK_OAUTH_REDIRECT_URL = os.environ.get('VK_OAUTH_REDIRECT_URL')
    VK_OAUTH_CODE_VERIFIER = os.environ.get('VK_OAUTH_CODE_VERIFIER')
    VK_OAUTH_CODE_CHALLENGE = os.environ.get('VK_OAUTH_CODE_CHALLENGE')
    VK_OAUTH_STATE = os.environ.get('VK_OAUTH_STATE')

    @staticmethod
    def init_app(app):
        pass


class TestConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    DEVELOPMENT = False
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"
    ELASTICSEARCH_URL = None


class DevelopmentConfig(BaseConfig):
    TESTING = False
    DEBUG = True
    DEVELOPMENT = True
    # SQLALCHEMY_ECHO = True


class ProductionConfig(BaseConfig):
    TESTING = False
    DEBUG = False
    DEVELOPMENT = False
    CACHE_IGNORE_ERRORS = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    @classmethod
    def init_app(cls, app):
        BaseConfig.init_app(app)
        if not app.debug:
            if cls.MAIL_SERVER:
                auth = None
                if cls.MAIL_USERNAME or cls.MAIL_PASSWORD:
                    auth = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
                secure = None
                if cls.MAIL_USE_TLS:
                    secure = ()
                mail_handler = SMTPHandler(
                    mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
                    # fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                    fromaddr=cls.MAIL_USERNAME,
                    toaddrs=cls.ADMINS, subject='Ошибки в блоге',
                    credentials=auth, secure=secure
                )
                mail_handler.setLevel(logging.ERROR)
                app.logger.addHandler(mail_handler)

            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/flygram.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Блог запущен')


def get_config_class():
    config = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "test": TestConfig,
        "default": ProductionConfig,
    }
    config_class = os.environ.get('CONFIG', 'default')
    return config[config_class]
