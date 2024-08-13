import jwt
from datetime import datetime, timezone, timedelta
from flask import current_app as app


def generate_token(user_id: int, expires: int, **kwargs) -> str:
    return jwt.encode(
        {"id": user_id, **kwargs, "exp": datetime.now(timezone.utc) + timedelta(minutes=expires)},
        app.config["SECRET_KEY"], algorithm="HS256"
    )
