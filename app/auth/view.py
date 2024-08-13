from datetime import timedelta

from flask import request, abort, make_response, Response, current_app as app, redirect
from flask.views import MethodView
from marshmallow import ValidationError

from app.auth import token_auth
from app.auth.schema import LoginSchema, CodeSchema
from app.auth.service import AuthInterface
from app.users.schema import UserUpdateSchema


class TwoFactorAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: AuthInterface

    def __init__(self, service: AuthInterface):
        self.service = service

    def post(self):
        """Включение двухфакторной аутентификации"""
        self.service.enable_two_factor()
        return {"message": "Вы успешно включили двухфакторную аутентификацию"}

    def delete(self):
        """Выключение двухфакторной аутентификации"""
        self.service.disable_two_factor()
        return {"message": "Вы успешно отключили двухфакторную аутентификацию"}


class SessionsAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: AuthInterface

    def __init__(self, service: AuthInterface):
        self.service = service

    def get(self):
        """Получение сеансов пользователя"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        return self.service.get_sessions(page, per_page)

    def delete(self):
        """Выход из всех устройств"""
        self.service.delete_sessions()
        return {"message": "Вы успешно вышли из всех устройств"}


class SessionAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: AuthInterface

    def __init__(self, service: AuthInterface):
        self.service = service

    def delete(self, session_id: str):
        """Удаление сеанса"""
        self.service.delete_session(session_id)
        return {"message": "Сеанс успешно удален"}


class EmailAPI(MethodView):
    init_every_request = False

    service: AuthInterface

    def __init__(self, service: AuthInterface):
        self.service = service

    def get(self):
        """Подтверждение электронной почты"""
        token = request.args.get('token')
        if not token:
            abort(400)
        self.service.verify_email(token)
        return redirect(f"{app.config["APP_URL"]}/security")

    @token_auth.login_required
    def post(self):
        """Запрос подтверждения электронной почты"""
        self.service.request_verify_email()
        return {"message": "Проверьте свою электронную почту"}


class PasswordAPI(MethodView):
    init_every_request = False

    service: AuthInterface

    def __init__(self, service: AuthInterface):
        self.service = service

    def post(self):
        """Запрос на сброс пароля"""
        if not request.json:
            abort(400)
        try:
            schema = UserUpdateSchema(only=['email'])
            email = request.json.get('email')
            if not email:
                abort(400)
            data = schema.load({'email': email.strip()})
            self.service.send_password_reset_email(data["email"])
            return {'message': 'Проверьте свою электронную почту'}
        except ValidationError as err:
            abort(422, err.messages)

    def put(self):
        token = request.headers.get('Token')
        if not request.json or not token:
            abort(400)
        try:
            schema = UserUpdateSchema(only=['password'])
            password = request.json.get('password')
            if not password:
                abort(400)
            data = schema.load({'password': password.strip()})
            self.service.reset_password(token, data["password"])
            return {'message': 'Пароль успешно сброшен'}
        except ValidationError as err:
            abort(422, err.messages)


class TokenAPI(MethodView):
    init_every_request = False

    service: AuthInterface

    def __init__(self, service: AuthInterface):
        self.service = service

    def get(self):
        """Обновление access токена"""
        refresh_token: str | None = request.cookies.get('refresh_token')
        if not refresh_token:
            abort(403, 'Время сессии истекло, авторизуйтесь заново')
        tokens = self.service.refresh(refresh_token)
        response: Response = make_response(tokens)
        refresh_token = tokens.get('refresh_token')
        if refresh_token:
            response.set_cookie('refresh_token', refresh_token,
                                max_age=timedelta(days=app.config.get('SESSION_LIFETIME')), httponly=True)
        return response

    def post(self):
        """Аутентификация в приложении"""
        if not request.json:
            abort(400)
        data = request.json
        two_factor: bool = request.json.get("two_factor", False)
        try:
            if two_factor:
                data.pop("two_factor")
                data = CodeSchema().load(data)
                login_data: dict = self.service.check_two_factor_code(
                    data["code"],
                    request.headers.get('token'),
                    data["remember_me"],
                    request.headers.get('user-agent'),
                    request.headers.get("x-real-ip", request.remote_addr)
                )
            else:
                data = LoginSchema().load(data)
                login_data: dict = self.service.login(
                    data["username"],
                    data["password"],
                    data["remember_me"],
                    request.headers.get('user-agent'),
                    request.headers.get("x-real-ip", request.remote_addr)
                )
            refresh_token = login_data.get('refresh_token')
            response: Response = make_response(login_data)
            if refresh_token:
                response.set_cookie('refresh_token', refresh_token,
                                    max_age=timedelta(days=app.config.get('SESSION_LIFETIME')), httponly=True)
                login_data.pop('refresh_token')
            return response
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self):
        """Выход из приложения"""
        refresh_token: str | None = request.cookies.get('refresh_token')
        if not refresh_token:
            abort(401)
        response: Response = make_response(self.service.logout(refresh_token))
        response.set_cookie('refresh_token', refresh_token, expires=0)
        return response
