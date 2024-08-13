from flask import request, abort, g
from flask.views import MethodView
from marshmallow import ValidationError

from app.auth import token_auth
from app.comments.schema import CommentSchema
from app.comments.service import CommentServiceInterface


class CommentsAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: CommentServiceInterface

    def __init__(self, service: CommentServiceInterface):
        self.service = service

    def get(self):
        """Получение списка комментариев к публикации"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        post_id = request.args.get('post_id', type=int)
        return self.service.get_comments(post_id, page, per_page)

    def post(self):
        """Создание нового комментария"""
        if not request.json:
            abort(400)
        data = dict(request.json)
        if not request.json.get('user_id'):
            data['user_id'] = g.current_user.id
        try:
            data = CommentSchema().load(data)
            response: dict = self.service.add_comment(data)
            return {'message': 'Комментарий отправлен', 'comment': response}
        except ValidationError as err:
            abort(422, err.messages)


class CommentAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: CommentServiceInterface

    def __init__(self, service: CommentServiceInterface):
        self.service = service

    def put(self, comment_id):
        """Редактирование комментария"""
        if not request.json:
            abort(400)
        data = dict(request.json)
        if not request.json.get('user_id'):
            data['user_id'] = g.current_user.id
        try:
            data = CommentSchema().load(data)
            response: dict = self.service.update_comment(comment_id, data)
            return {'message': 'Изменения сохранены', 'comment': response}
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self, comment_id):
        """Удаление комментария"""
        self.service.delete_comment(comment_id)
        return {'message': 'Комментарий успешно удален'}
