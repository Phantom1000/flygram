import jwt
from datetime import datetime, timezone, timedelta
from app import app


def generate_token(user_id: int, expires: int) -> str:
    return jwt.encode(
        {"id": user_id, "exp": datetime.now(timezone.utc) + timedelta(minutes=expires)},
        app.config["SECRET_KEY"], algorithm="HS256"
    )
