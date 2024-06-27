from datetime import timedelta
from flask_restful import Resource
from flask import request, abort, make_response, Response, current_app as app
from app.auth.repository import SessionRepository
from app.auth.service import AuthInterface, AuthService
from app.auth.schema import LoginSchema
from marshmallow import ValidationError
from app.users.repository import UserRepository


class TokenAPI(Resource):
    service: AuthInterface

    def __init__(self):
        self.service = AuthService(UserRepository(), SessionRepository())

    def get(self):
        """Обновление access токена"""
        refresh_token: str | None = request.cookies.get('refresh_token')
        if not refresh_token:
            abort(403, 'Время сессии истекло, авторизуйтесь заново')
        response = self.service.refresh(refresh_token)
        return response

    def post(self):
        """Аутентификация в приложении"""
        if not request.json:
            abort(400)
        try:
            data = LoginSchema().load(request.json)
            login_data: dict = self.service.login(
                data["username"],
                data["password"],
                data["remember_me"],
                request.headers.get('user-agent'),
                request.headers.get("x-real-ip", request.remote_addr)
            )
            refresh_token = login_data.pop('refresh_token')
            response: Response = make_response(login_data)
            if refresh_token:
                response.set_cookie('refresh_token', refresh_token,
                                    max_age=timedelta(days=app.config.get('SESSION_LIFETIME')), httponly=True)
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
