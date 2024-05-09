from flask_restful import Resource
from flask import request, abort, jsonify, g
from werkzeug.utils import secure_filename

from app.auth import token_auth
from app.models import Post, User
from app import db
from marshmallow import ValidationError
from app.schemas import PostSchema
import sqlalchemy as sa
from app.utils import allowed_file


class PostsAPI(Resource):
    method_decorators = [token_auth.login_required]

    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        hashtag = request.args.get('hashtag')
        author_name = request.args.get('author')
        type = request.args.get('type')
        query = sa.select(Post)
        if hashtag:
            like_hashtag = f'%{hashtag.lower()}%'
            query = sa.select(Post).where(Post.hashtags.like(like_hashtag))
        if author_name:
            author: User = db.first_or_404(sa.select(User).where(User.username == author_name))
            query = author.posts.select()
        if type:
            if type == 'liked':
                query = g.current_user.liked_posts.select()
            if type == 'recommended':
                query = g.current_user.following_posts()
        total_items = db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))
        query = query.order_by(sa.desc(Post.publication_date)).offset((page - 1) * per_page).limit(per_page)
        data = Post.to_collection_dict(query, total_items, page, per_page, 'users')
        return jsonify(data)

    def post(self):
        if not request.form:
            abort(400)
        data = dict(request.form)
        # if 'user_id' not in data.keys():
        #     data['user_id'] = g.current_user.id
        if not request.form.get('user_id'):
            data['user_id'] = g.current_user.id
        if int(data['user_id']) != g.current_user.id:
            abort(403, 'У Вас нет прав доступа')
        try:
            data = PostSchema().load(data)
            for key, value in data.items():
                if type(value) is str:
                    data[key] = value.strip()
            data['hashtags'] = data['hashtags'].lower().replace(" ", "")
            post: Post = Post(**data)
            if request.files:
                image = request.files['image']
                filename = secure_filename(image.filename)
                if image and filename != '':
                    if allowed_file(filename):
                        post.upload_image(image)
                    else:
                        abort(400)
            db.session.add(post)
            db.session.commit()
            return {'message': 'Новость опубликована', 'post': post.to_dict()}
        except ValidationError as err:
            abort(422, err.messages)


class PostAPI(Resource):
    method_decorators = [token_auth.login_required]

    def get(self, post_id):
        post = db.get_or_404(Post, post_id)
        return post.to_dict()

    def put(self, post_id):
        if not request.form:
            abort(400)
        data = dict(request.form)
        post = db.get_or_404(Post, post_id)
        if 'user_id' not in data.keys():
            data['user_id'] = g.current_user.id
        if int(data['user_id']) != g.current_user.id or post.user_id != g.current_user.id:
            abort(403, 'У Вас нет прав доступа')
        try:
            data = PostSchema().load(data)
            for key, value in data.items():
                if type(value) is str:
                    data[key] = value.strip()
            data['hashtags'] = data['hashtags'].lower().replace(" ", "")
            post.from_dict(data)
            if request.files:
                image = request.files['image']
                filename = secure_filename(image.filename)
                if image and filename != '':
                    if allowed_file(filename):
                        post.upload_image(image)
                    else:
                        abort(400)
            db.session.add(post)
            db.session.commit()
            return {'message': 'Изменения сохранены', 'post': post.to_dict()}
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self, post_id):
        post = db.get_or_404(Post, post_id)
        if post.user_id != g.current_user.id:
            abort(403, 'У Вас нет прав доступа')
        db.session.delete(post)
        db.session.commit()
        return {'message': 'Запись успешно удалена'}


class LikesAPI(Resource):
    method_decorators = [token_auth.login_required]

    def post(self, post_id):
        post = db.get_or_404(Post, post_id)
        post.like(g.current_user)
        db.session.commit()
        return {}, 201

    def delete(self, post_id):
        post = db.get_or_404(Post, post_id)
        post.unlike(g.current_user)
        db.session.commit()
        return {}, 201
