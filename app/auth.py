from flask_httpauth import HTTPTokenAuth
from app.models import User
from app import db
import jwt
from flask import current_app as app, abort, g
import time
from datetime import datetime, timezone

token_auth = HTTPTokenAuth(scheme='Bearer')


@token_auth.verify_token
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
        if payload["expires"] < time.time():
            return False
        user = db.session.get(User, payload["id"])
        g.current_user = user
        user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        return user
    except jwt.exceptions.DecodeError:
        return False


@token_auth.error_handler
def handle_error():
    abort(401)
