from flask_restful import Resource
from flask import request, abort, jsonify
from app.schemas import LoginSchema, UserSchema, UserUpdateSchema
from marshmallow import ValidationError
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, friends
from app import db
from app.auth import token_auth
from flask import current_app as app, g
from werkzeug.utils import secure_filename
from app.utils import allowed_file


class TokenAPI(Resource):
    def post(self):
        if not request.json:
            abort(400)
        try:
            data = LoginSchema().load(request.json)
            query = sa.select(User).where(User.username == data["username"]).limit(1)
            user = db.session.scalar(query)
            if user and user.check_password(data["password"]):
                token_lifetime = int(app.config.get("TOKEN_LIFETIME")) if data["remember_me"] else 3600
                return jsonify(message=f'Вы успешно вошли{" и система Вас запомнила" if data['remember_me'] else ""}',
                               token=user.generate_token(token_lifetime))
            else:
                abort(403, "Проверьте имя пользователя и пароль")
        except ValidationError as err:
            abort(422, err.messages)


class UserAPI(Resource):
    method_decorators = [token_auth.login_required]

    def get(self, username):
        if username == 'current':
            user = g.current_user
        else:
            query = sa.select(User).where(User.username == username).limit(1)
            user = db.first_or_404(query)
        return user.to_dict()

    def put(self, username):
        if not request.form:
            abort(400)
        try:
            if request.args and request.args['update'] == 'password':
                schema = UserUpdateSchema(only=['password'])
                data = schema.load({'password': request.form['new_password'].strip()})
                query = sa.select(User).where(User.username == username).limit(1)
                user = db.first_or_404(query)
                if user.check_password(request.form['password']):
                    user.set_password(data['password'])
                else:
                    abort(403, "Проверьте пароль")
            else:
                schema = UserUpdateSchema(exclude=['password'])
                data = schema.load(request.form)
                query = sa.select(User).where(User.username == username).limit(1)
                user = db.first_or_404(query)
                if 'username' in data and data['username'] != username:
                    query = sa.select(User).where(User.username == data["username"]).limit(1)
                    user_exist = db.session.scalar(query)
                    if user_exist:
                        abort(422, 'Пользователь с таким именем уже существует')
                if 'email' in data and data['email'] != user.email:
                    query = sa.select(User).where(User.email == data["email"]).limit(1)
                    user_exist = db.session.scalar(query)
                    if user_exist:
                        abort(422, 'Пользователь с таким email уже существует')
                for key, value in data.items():
                    if type(value) is str:
                        data[key] = value.strip()
                user.from_dict(data)
                if request.files:
                    avatar = request.files['avatar']
                    filename = secure_filename(avatar.filename)
                    if avatar and filename != '':
                        if allowed_file(filename):
                            user.upload_avatar(avatar)
                        else:
                            abort(400)
            db.session.commit()
            return {'message': 'Изменения сохранены', 'user': user.to_dict()}
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self, username):
        query = sa.select(User).where(User.username == username).limit(1)
        user = db.first_or_404(query)
        db.session.delete(user)
        db.session.commit()
        return {'message': 'Аккаунт успешно удален'}


def users_filters(query, total_items_query):
    firstname = request.args.get('firstname')
    if firstname:
        query = query.where(sa.func.lower(User.firstname).like(f'%{firstname.lower()}%'))
        total_items_query = total_items_query.where(sa.func.lower(User.firstname).like(f'%{firstname.lower()}%'))
    lastname = request.args.get('lastname')
    if lastname:
        query = query.where(sa.func.lower(User.lastname).like(f'%{lastname.lower()}%'))
        total_items_query = total_items_query.where(sa.func.lower(User.lastname).like(f'%{lastname.lower()}%'))
    city = request.args.get('city')
    if city:
        query = query.where(sa.func.lower(User.city).like(f'%{city.lower()}%'))
        total_items_query = total_items_query.where(sa.func.lower(User.city).like(f'%{city.lower()}%'))
    education = request.args.get('education')
    if education:
        query = query.where(sa.func.lower(User.education).like(f'%{education.lower()}%'))
        total_items_query = total_items_query.where(sa.func.lower(User.education).like(f'%{education.lower()}%'))
    career = request.args.get('career')
    if career:
        query = query.where(sa.func.lower(User.career).like(f'%{career.lower()}%'))
        total_items_query = total_items_query.where(sa.func.lower(User.career).like(f'%{career.lower()}%'))
    return query, total_items_query


class UsersAPI(Resource):
    method_decorators = [token_auth.login_required]

    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        query = sa.select(User)
        total_items_query = sa.select(sa.func.count(User.id))
        query, total_items_query = users_filters(query, total_items_query)
        query = query.offset((page - 1) * per_page).limit(per_page)
        total_items = db.session.scalar(total_items_query)
        data = User.to_collection_dict(query, total_items, page, per_page, 'users')
        return jsonify(data)

    def post(self):
        if not request.form:
            abort(400)
        try:
            data = UserSchema().load(request.form)
            query = sa.select(User).where(sa.or_(
                User.username == data["username"], User.email == data["email"])).limit(1)
            user_exist = db.session.scalar(query)
            if not user_exist:
                password = data['password']
                del data['password']
                for key, value in data.items():
                    if type(value) is str:
                        data[key] = value.strip()
                user: User = User(**data)
                user.set_password(password)
                if request.files:
                    avatar = request.files['avatar']
                    filename = secure_filename(avatar.filename)
                    if avatar and filename != '':
                        if allowed_file(filename):
                            user.upload_avatar(avatar)
                        else:
                            abort(400)
                db.session.add(user)
                db.session.commit()
                return {'message': 'Вы успешно зарегистрировались!'}, 201
            else:
                abort(422, 'Пользователь с таким именем или email уже существует!')
        except ValidationError as err:
            abort(422, err.messages)


class FriendsAPI(Resource):
    method_decorators = [token_auth.login_required]

    def get(self, username):
        user = db.first_or_404(sa.select(User).where(User.username == username))
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        query = user.friends()
        total_items_query = sa.select(sa.func.count())
        relation_type = request.args.get('type')
        if relation_type:
            if relation_type == 'followers':
                query = user.followers_without_friends()
                test = db.session.scalars(query).all()
            elif relation_type == 'following':
                query = user.following_without_friends()
        query, _ = users_filters(query, total_items_query)
        total_items_query = total_items_query.select_from(query.subquery())
        query = query.offset((page - 1) * per_page).limit(per_page)
        total_items = db.session.scalar(total_items_query)
        return User.to_collection_dict(query, total_items, page, per_page, 'users')

    def post(self, username):
        from_user: User = g.current_user
        to_user = db.first_or_404(sa.select(User).where(User.username == username))
        if from_user == to_user:
            return {"error": "Невозможно отправить заявку самому себе"}, 422
        from_user.follow(to_user)
        db.session.commit()
        return {"message": "Заявка отправлена"}

    def put(self, username):
        to_user: User = g.current_user
        from_user = db.first_or_404(sa.select(User).where(User.username == username))
        if from_user.is_following(to_user):
            to_user.follow(from_user)
            db.session.commit()
            return {"message": "Заявка принята"}
        else:
            abort(403, "У Вас нет прав доступа")

    def delete(self, username):
        from_user: User = g.current_user
        to_user = db.first_or_404(sa.select(User).where(User.username == username))
        from_user.unfollow(to_user)
        db.session.commit()
        return {"message": "Заявка отменена"}
