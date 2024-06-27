from abc import ABC, abstractmethod
import uuid
from datetime import datetime, timezone

import pytz
from app.users.utils import check_password
from app.auth.repository import SessionRepositoryInterface
from app.users.repository import UserRepositoryInterface
from app.models import User, Session
from flask import g, current_app as app, abort
from app.auth.utils import generate_token


class AuthInterface(ABC):
    session_repository: SessionRepositoryInterface
    users_repository: UserRepositoryInterface

    @abstractmethod
    def login(self, username: str, password: str, remember_me: bool, user_agent: str, ip: str) -> dict:
        pass

    @abstractmethod
    def refresh(self, token: str) -> dict:
        pass

    @abstractmethod
    def logout(self, token: str) -> dict:
        pass


class AuthService(AuthInterface):
    def __init__(self, users_repository: UserRepositoryInterface, session_repository: SessionRepositoryInterface):
        self.users_repository = users_repository
        self.session_repository = session_repository

    def login(self, username: str, password: str, remember_me: bool, user_agent: str, ip: str) -> dict:
        user: User = self.users_repository.get_by_username(username, False)
        if user and check_password(user, password):
            g.current_user = user
            self.users_repository.update_last_seen(user)
            token_lifetime: int = int(app.config.get("TOKEN_LIFETIME"))
            refresh_token: str | None = None
            if remember_me:
                session: Session = self.session_repository.add(user.id, user_agent, ip)
                refresh_token = str(session.id)
            return {
                'message': f'Вы успешно вошли{" и система Вас запомнила" if remember_me else ""}',
                'access_token': generate_token(user.id, token_lifetime),
                'user': self.users_repository.model_to_dict(user),
                'refresh_token': refresh_token
            }
        else:
            abort(403, "Проверьте имя пользователя и пароль")

    def refresh(self, token: str) -> dict:
        try:
            session_id: uuid.UUID = uuid.UUID(token)
            session: Session = self.session_repository.get_by_id(session_id)
            if pytz.UTC.localize(session.expires) > datetime.now(timezone.utc):
                g.current_user = session.user
                self.users_repository.update_last_seen(session.user)
                token_lifetime: int = int(app.config.get("TOKEN_LIFETIME"))
                return {
                    'token': generate_token(session.user.id, token_lifetime),
                    'user': self.users_repository.model_to_dict(session.user)
                }
            else:
                self.session_repository.delete(session)
                abort(403, 'Время сессии истекло, авторизуйтесь заново')
        except ValueError:
            abort(400)

    def logout(self, token: str) -> dict:
        try:
            session_id: uuid.UUID = uuid.UUID(token)
            session: Session = self.session_repository.get_by_id(session_id)
            self.session_repository.delete(session)
            return {
                'message': "Вы успешно вышли из аккаунта"
            }
        except ValueError:
            abort(400)
