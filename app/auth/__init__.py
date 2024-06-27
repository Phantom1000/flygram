from flask_httpauth import HTTPTokenAuth
from app.models import User
from app import db
import jwt
from flask import current_app as app, abort, g
from app.users.repository import UserRepository, UserRepositoryInterface

token_auth = HTTPTokenAuth(scheme='Bearer')


@token_auth.verify_token
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
        repository: UserRepositoryInterface = UserRepository()
        user: User = repository.get_by_id(payload["id"])
        if user:
            g.current_user = user
            repository.update_last_seen(user)
            return user
        else:
            return False
    except jwt.DecodeError:
        return False
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


@token_auth.error_handler
def handle_error():
    abort(401)
