from flask import request, abort, g
from flask.views import MethodView
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

from app.auth import token_auth
from app.posts.schema import PostSchema
from app.posts.service import PostServiceInterface
from app.utils import allowed_file
from app import cache


class PostsAPI(MethodView):
    init_every_request = False

    decorators = [token_auth.login_required]

    service: PostServiceInterface

    def __init__(self, service: PostServiceInterface):
        self.service = service

    @cache.cached(timeout=120)
    def get(self):
        """Получение списка публикаций"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        hashtag = request.args.get('hashtag')
        author_name = request.args.get('author')
        community_id = request.args.get('community')
        posts_type = request.args.get('type')
        search = request.args.get('search')
        return self.service.get_posts(
            author_name, community_id, posts_type, {"hashtags": hashtag, "text": search}, page, per_page)

    def post(self):
        """Создание новой публикации"""
        if not request.form:
            abort(400)
        data = dict(request.form)
        if not request.form.get('user_id'):
            data['user_id'] = g.current_user.id
        try:
            data = PostSchema().load(data)
            image = request.files.get('image')
            if image:
                filename = secure_filename(image.filename)
                if image and filename != '':
                    if allowed_file(filename):
                        data.update({"image": image})
                    else:
                        abort(400)
            post: dict = self.service.add_post(data)
            return {'message': 'Новость опубликована', 'post': post}
        except ValidationError as err:
            abort(422, err.messages)


class PostAPI(MethodView):
    init_every_request = False

    decorators = [token_auth.login_required]

    service: PostServiceInterface

    def __init__(self, service: PostServiceInterface):
        self.service = service

    def get(self, post_id):
        """Получение отдельной публикации по идентификатору"""
        return self.service.get_post(post_id)

    def put(self, post_id):
        """Редактирование публикации"""
        if not request.form:
            abort(400)
        data = dict(request.form)
        try:
            data = PostSchema().load(data)
            image = request.files.get('image')
            if image:
                filename = secure_filename(image.filename)
                if image and filename != '':
                    if allowed_file(filename):
                        data.update({"image": image})
                    else:
                        abort(400)
            post: dict = self.service.update_post(post_id, data)
            return {'message': 'Изменения сохранены', 'post': post}
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self, post_id):
        """Удаление публикации"""
        self.service.delete_post(post_id)
        return {'message': 'Запись успешно удалена'}


class LikesAPI(MethodView):
    init_every_request = False

    decorators = [token_auth.login_required]

    service: PostServiceInterface

    def __init__(self, service: PostServiceInterface):
        self.service = service

    def post(self, post_id):
        """Добавление оценки публикации"""
        self.service.like_post(post_id)
        return {}, 201

    def delete(self, post_id):
        """Удаление оценки публикации"""
        self.service.unlike_post(post_id)
        return {}, 201
