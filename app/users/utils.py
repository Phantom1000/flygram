from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User


def set_password(user: User, password: str):
    user.password_hash = generate_password_hash(password)
    db.session.commit()


def check_password(user: User, password: str):
    return check_password_hash(user.password_hash, password)
