from flask import request, abort, g
from flask.views import MethodView
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

from app import cache
from app.auth import token_auth
from app.users.schema import UserSchema, UserUpdateSchema
from app.users.service import UserServiceInterface
from app.utils import allowed_file


class UserAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: UserServiceInterface

    def __init__(self, service: UserServiceInterface):
        self.service = service

    def get(self, username: str):
        """Запрос пользователя по имени в приложении"""
        return self.service.get_user(username)

    def put(self, username: str):
        """Обновление данных пользователя"""
        if not request.form:
            abort(400)
        if g.current_user.username != username:
            abort(403, 'У Вас нет прав доступа')
        try:
            if request.args and request.args['update'] == 'password':
                schema = UserUpdateSchema(only=['password'])
                password = request.form.get('new_password')
                if not password:
                    abort(400)
                data = schema.load({'password': password.strip()})
                response: dict = self.service.update_password(username, request.form.get('password'), data['password'])
            else:
                schema = UserUpdateSchema(exclude=['password'])
                data = schema.load(request.form)
                if request.files:
                    avatar = request.files['avatar']
                    filename = secure_filename(avatar.filename)
                    if avatar and filename != '':
                        if allowed_file(filename):
                            data.update({"avatar": avatar})
                        else:
                            abort(400)
                response: dict = self.service.update_user(username, data)
            return {'message': 'Изменения сохранены', 'user': response}
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self, username: str):
        """Удаление аккаунта"""
        self.service.delete_user(username)
        return {'message': 'Аккаунт успешно удален'}


class UsersAPI(MethodView):
    init_every_request = False
    service: UserServiceInterface

    def __init__(self, service: UserServiceInterface):
        self.service = service

    @cache.cached(timeout=120)
    @token_auth.login_required
    def get(self):
        """Получение списка пользователей"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        firstname = request.args.get('firstname')
        lastname = request.args.get('lastname')
        city = request.args.get('city')
        education = request.args.get('education')
        career = request.args.get('career')
        vacancy_id = request.args.get('vacancy', type=int)
        relation_type = request.args.get('type')
        data: dict = self.service.get_users({
            "firstname": firstname,
            "lastname": lastname,
            "city": city,
            "education": education,
            "career": career
        }, page, per_page, vacancy_id, relation_type == 'recommended')
        return data

    def post(self):
        """Регистрация в приложении"""
        if not request.form:
            abort(400)
        try:
            data = UserSchema().load(request.form)
            avatar = request.files.get('avatar')
            if avatar:
                filename = secure_filename(avatar.filename)
                if avatar and filename != '':
                    if allowed_file(filename):
                        data.update({"avatar": avatar})
                    else:
                        abort(400)
            user: dict = self.service.add_user(data)
            return {"message": "Вы успешно зарегистрировались", "user": user}
        except ValidationError as err:
            abort(422, err.messages)


class FriendsAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: UserServiceInterface

    def __init__(self, service: UserServiceInterface):
        self.service = service

    def get(self, username):
        """Получение списка друзей пользователя"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        firstname = request.args.get('firstname')
        lastname = request.args.get('lastname')
        city = request.args.get('city')
        education = request.args.get('education')
        career = request.args.get('career')
        relation_type = request.args.get('type')
        data: dict = self.service.get_friends(username, {
            "firstname": firstname,
            "lastname": lastname,
            "city": city,
            "education": education,
            "career": career
        }, page, per_page, relation_type)
        return data

    def post(self, username):
        """Отправление заявки в друзья"""
        self.service.add_friend(username)
        return {"message": "Заявка отправлена"}

    def put(self, username):
        """Подтверждение заявки"""
        if self.service.accept_friend(username):
            return {"message": "Заявка принята"}
        else:
            abort(403, "У Вас нет прав доступа")

    def delete(self, username):
        """Удаление из друзей или отмена заявки"""
        self.service.delete_friend(username)
        return {"message": "Заявка отменена"}
