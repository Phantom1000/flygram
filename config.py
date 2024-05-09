from os import environ, path

basedir = path.abspath(path.dirname(__file__))


class Config:
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL') or 'sqlite:///' + path.join(basedir, 'app.db')
    TOKEN_LIFETIME = environ.get('TOKEN_LIFETIME') or 3600
    SECRET_KEY = environ.get('SECRET_KEY') or 'secret-key'
    APP_URL = environ.get('APP_URL') or 'http://localhost'
    UPLOAD_FOLDER = path.join(basedir, 'app', 'static', environ.get('UPLOAD_FOLDER') or 'images')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
