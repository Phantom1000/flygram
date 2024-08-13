import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import jwt

from app.tasks import send_email
from flask import g, current_app as app, abort, render_template
from enum import Enum
from app.auth.repository import SessionRepositoryInterface
from app.auth.utils import generate_token
from app.models import User, Session
from app.users.repository import UserRepositoryInterface
from app.users.utils import check_password, set_password
import secrets


class TokenType(str, Enum):
    reset_password = 'reset_password'
    verify_email = 'verify_email'
    two_factor = 'two_factor'


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

    @abstractmethod
    def send_password_reset_email(self, email: str):
        pass

    @abstractmethod
    def reset_password(self, token, new_password):
        pass

    @abstractmethod
    def get_sessions(self, page: int, per_page: int) -> dict:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        pass

    @abstractmethod
    def delete_sessions(self) -> None:
        pass

    @abstractmethod
    def request_verify_email(self) -> None:
        pass

    @abstractmethod
    def verify_email(self, token: str) -> None:
        pass

    @abstractmethod
    def enable_two_factor(self) -> None:
        pass

    @abstractmethod
    def disable_two_factor(self) -> None:
        pass

    @abstractmethod
    def send_two_factor_code(self) -> None:
        pass

    @abstractmethod
    def authenticate(self, user: User, remember_me: bool, user_agent: str, ip: str) -> dict:
        pass

    @abstractmethod
    def check_two_factor_code(self, code: int, token: str, remember_me: bool, user_agent: str, ip: str) -> dict:
        pass


class AuthService(AuthInterface):
    def __init__(self, users_repository: UserRepositoryInterface, session_repository: SessionRepositoryInterface):
        self.users_repository = users_repository
        self.session_repository = session_repository

    def authenticate(self, user: User, remember_me: bool, user_agent: str, ip: str) -> dict:
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

    def check_two_factor_code(self, code: int, token: str, remember_me: bool, user_agent: str, ip: str) -> dict:
        try:
            payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
            user = self.users_repository.get_by_id(payload["id"])
            if user and payload["type"] == TokenType.two_factor:
                if secrets.compare_digest(bytes(code), bytes(user.two_factor_code)):
                    g.current_user = user
                    return self.authenticate(user, remember_me, user_agent, ip)
                else:
                    abort(403, "У Вас нет прав доступа")
            else:
                abort(404)
        except (jwt.DecodeError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            abort(400)

    def login(self, username: str, password: str, remember_me: bool, user_agent: str, ip: str) -> dict:
        user: User = self.users_repository.get_by_username(username, False)
        if user and check_password(user, password):
            g.current_user = user
            if g.current_user.two_factor_enabled:
                self.send_two_factor_code()
                token = generate_token(g.current_user.id, app.config.get("EMAIL_TOKEN_LIFETIME"),
                                       type=TokenType.two_factor)
                return {
                    'message': 'Проверьте электронную почту',
                    'token': token
                }
            else:
                return self.authenticate(user, remember_me, user_agent, ip)
        else:
            abort(403, "Проверьте имя пользователя и пароль")

    def refresh(self, token: str) -> dict:
        try:
            session_id: uuid.UUID = uuid.UUID(token)
            session: Session = self.session_repository.get_by_id(session_id)
            if session.expires.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                g.current_user = session.user
                self.users_repository.update_last_seen(session.user)
                token_lifetime: int = int(app.config.get("TOKEN_LIFETIME"))
                refresh_token = self.session_repository.refresh(session)
                return {
                    'token': generate_token(session.user.id, token_lifetime),
                    'refresh_token': refresh_token,
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

    def send_password_reset_email(self, email: str):
        user = self.users_repository.get_by_email(email)
        if user:
            token = generate_token(user.id, app.config.get("PASSWORD_TOKEN_LIFETIME"), type=TokenType.reset_password)
            subject: str = "Сброс пароля"
            send_email.delay(
                subject,
                app.config['ADMINS'][0],
                [user.email],
                render_template('email/reset_password.txt', user=user, token=token),
                render_template('email/reset_password.html', user=user, token=token)
            )
        else:
            abort(404)

    def reset_password(self, token, new_password):
        try:
            payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
            user = self.users_repository.get_by_id(payload["id"])
            if user and payload["type"] == TokenType.reset_password:
                set_password(user, new_password)
            else:
                abort(404)
        except (jwt.DecodeError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            abort(400)

    def get_sessions(self, page: int, per_page: int) -> dict:
        return self.session_repository.paginate(page, per_page, g.current_user)

    def delete_sessions(self) -> None:
        self.session_repository.delete_all(g.current_user)

    def delete_session(self, session_id: str) -> None:
        try:
            session_id: uuid.UUID = uuid.UUID(session_id)
            session: Session = self.session_repository.get_by_id(session_id)
            if session.user == g.current_user:
                self.session_repository.delete(session)
            else:
                abort(403, "У Вас нет прав доступа")
        except ValueError:
            abort(400)

    def request_verify_email(self) -> None:
        token = generate_token(g.current_user.id, app.config.get("EMAIL_TOKEN_LIFETIME"), type=TokenType.verify_email)
        subject: str = "Подтверждение электронной почты"
        send_email.delay(
            subject,
            app.config['ADMINS'][0],
            [g.current_user.email],
            render_template('email/verify_email.txt', user=g.current_user, token=token),
            render_template('email/verify_email.html', user=g.current_user, token=token)
        )

    def verify_email(self, token: str) -> None:
        try:
            payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
            user = self.users_repository.get_by_id(payload["id"])
            if user and payload["type"] == TokenType.verify_email:
                self.users_repository.verify_email(user)
            else:
                abort(404)
        except (jwt.DecodeError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            abort(400)

    def enable_two_factor(self) -> None:
        if g.current_user.verified_email and not g.current_user.two_factor_enabled:
            self.users_repository.enable_two_factor(g.current_user)
        else:
            abort(400)

    def disable_two_factor(self) -> None:
        if g.current_user.verified_email and g.current_user.two_factor_enabled:
            self.users_repository.disable_two_factor(g.current_user)
        else:
            abort(400)

    def send_two_factor_code(self) -> None:
        if g.current_user.verified_email:
            code = secrets.choice(range(app.config['TWO_FACTOR_MIN_CODE'], app.config['TWO_FACTOR_MAX_CODE']))
            self.users_repository.update_model_from_dict(g.current_user, {"two_factor_code": code})
            subject: str = "Код авторизации"
            send_email.delay(
                subject,
                app.config['ADMINS'][0],
                [g.current_user.email],
                render_template('email/two_factor.txt', user=g.current_user, code=code),
                render_template('email/two_factor.html', user=g.current_user, code=code)
            )
        else:
            abort(400)
