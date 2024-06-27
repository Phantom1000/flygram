from flask import request, abort, g
from flask_restful import Resource
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

from app.auth import token_auth
from app.communities.repository import CommunityRepository
from app.communities.schema import CommunitySchema
from app.communities.service import CommunityService, CommunityServiceInterface
from app.users.repository import UserRepository
from app.utils import allowed_file


class CommunitiesAPI(Resource):
    method_decorators = [token_auth.login_required]

    service: CommunityServiceInterface

    def __init__(self):
        self.service = CommunityService(CommunityRepository(), UserRepository())

    def get(self):
        """Получение списка сообществ"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        name = request.args.get('name')
        username = request.args.get('username')
        community_type = request.args.get('type')
        return self.service.get_communities(username, community_type, {"name": name}, page, per_page)

    def post(self):
        """Создание нового сообщества"""
        if not request.form:
            abort(400)
        data = dict(request.form)
        if not request.form.get('user_id'):
            data['user_id'] = g.current_user.id
        try:
            data = CommunitySchema().load(data)
            image = request.files.get('image')
            if image:
                filename = secure_filename(image.filename)
                if image and filename != '':
                    if allowed_file(filename):
                        data.update({"image": image})
                    else:
                        abort(400)
            response: dict = self.service.add_community(data)
            return {'message': 'Сообщество создано', 'community': response}
        except ValidationError as err:
            abort(422, err.messages)


class CommunityAPI(Resource):
    method_decorators = [token_auth.login_required]

    service: CommunityServiceInterface

    def __init__(self):
        self.service = CommunityService(CommunityRepository(), UserRepository())

    def get(self, community_id):
        """Получение сообщества по идентификатору"""
        return self.service.get_community(community_id)

    def put(self, community_id):
        """Редактирование сообщества"""
        if not request.form:
            abort(400)
        data = dict(request.form)
        try:
            data = CommunitySchema().load(data)
            image = request.files.get('image')
            if image:
                filename = secure_filename(image.filename)
                if image and filename != '':
                    if allowed_file(filename):
                        data.update({"image": image})
                    else:
                        abort(400)
            response: dict = self.service.update_community(community_id, data)
            return {'message': 'Изменения сохранены', 'community': response}
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self, community_id):
        """Удаление сообщества"""
        self.service.delete_community(community_id)
        return {'message': 'Сообщество успешно удалено'}


class MembersAPI(Resource):
    method_decorators = [token_auth.login_required]

    service: CommunityServiceInterface

    def __init__(self):
        self.service = CommunityService(CommunityRepository(), UserRepository())

    def get(self, community_id):
        """Получение списка участников сообщества"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        firstname = request.args.get('firstname')
        lastname = request.args.get('lastname')
        city = request.args.get('city')
        education = request.args.get('education')
        career = request.args.get('career')
        data: dict = self.service.get_members(community_id, {
            "firstname": firstname,
            "lastname": lastname,
            "city": city,
            "education": education,
            "career": career
        }, page, per_page)
        return data

    def post(self, community_id):
        """Вступление в сообщество"""
        self.service.join_community(community_id)
        return {'message': 'Вы успешно присоединились к сообществу'}, 201

    def delete(self, community_id):
        """Выход из сообщества"""
        self.service.leave_community(community_id)
        return {'message': 'Вы успешно покинули сообщество'}, 201
