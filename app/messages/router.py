from flask import request, abort, g
from flask_restful import Resource
from marshmallow import ValidationError

from app.auth import token_auth
from app.messages.schema import MessageSchema
from app.messages.service import MessageService, MessageServiceInterface
from app.messages.repository import MessageRepository
from app.users.repository import UserRepository


class MessagesAPI(Resource):
    method_decorators = [token_auth.login_required]

    service: MessageServiceInterface

    def __init__(self):
        self.service = MessageService(MessageRepository(), UserRepository())

    def get(self):
        """Получение списка сообщений диалога"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 6, type=int), 100)
        username = request.args.get('username')
        return self.service.get_messages(username, page, per_page)

    def post(self):
        """Отправка сообщения"""
        if not request.json:
            abort(400)
        data = dict(request.json)
        try:
            data = MessageSchema().load(data)
            response: dict = self.service.add_message(data)
            return {'data_message': response}
        except ValidationError as err:
            abort(422, err.messages)
