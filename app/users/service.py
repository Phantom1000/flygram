import math
import os
from abc import ABC, abstractmethod
from hashlib import md5

from flask import g, current_app as app, abort
from werkzeug.utils import secure_filename

from app.auth.repository import SessionRepositoryInterface
from app.models import User, Vacancy
from app.users.repository import UserRepositoryInterface
from app.users.utils import check_password, set_password
from app.utils import get_similarity_vector
from app import db

SUBSCRIPTION_WEIGHT = 3
SAME_ATTRIBUTES_WEIGHT = 2
SAME_COMMUNITY_WEIGHT = 2
SIMILARITY_COEFFICIENT = 2
SKILL_WEIGHT = 5


class UserServiceInterface(ABC):
    session_repository: SessionRepositoryInterface
    users_repository: UserRepositoryInterface

    @abstractmethod
    def get_user(self, username: str) -> dict:
        pass

    @abstractmethod
    def get_users(self, filters: dict, page: int, per_page: int, vacancy_id: int, recommended: bool = False) -> dict:
        pass

    @abstractmethod
    def update_password(self, username: str, password: str, new_password: str) -> dict:
        pass

    @abstractmethod
    def add_user(self, data: dict) -> dict:
        pass

    @abstractmethod
    def update_user(self, username: str, data: dict) -> dict:
        pass

    @abstractmethod
    def upload_avatar(self, user: User, file) -> None:
        pass

    @abstractmethod
    def delete_user(self, username: str) -> None:
        pass

    @abstractmethod
    def get_friends(self, username: str, filters: dict, page: int, per_page: int, relation: str | None) -> dict:
        pass

    @abstractmethod
    def add_friend(self, username: str) -> None:
        pass

    @abstractmethod
    def accept_friend(self, username: str) -> bool:
        pass

    @abstractmethod
    def delete_friend(self, username: str) -> None:
        pass

    @abstractmethod
    def get_recommended_friends(self, page: int, per_page: int) -> dict:
        pass

    @abstractmethod
    def get_recommended_employees(self, vacancy_id: int, page: int, per_page: int) -> dict:
        pass


class UserService(UserServiceInterface):
    def __init__(self, users_repository: UserRepositoryInterface):
        self.users_repository = users_repository

    def get_user(self, username: str) -> dict:
        if username == 'current':
            user = g.current_user
        else:
            user = self.users_repository.get_by_username(username)
        return self.users_repository.model_to_dict(user)

    def get_users(self, filters: dict, page: int, per_page: int, vacancy_id: int, recommended: bool = False) -> dict:
        if recommended:
            return self.get_recommended_friends(page, per_page)
        if vacancy_id:
            return self.get_recommended_employees(vacancy_id, page, per_page)
        return self.users_repository.paginate_by_filters(
            {field: value for field, value in filters.items() if value}, page, per_page
        )

    def get_recommended_friends(self, page: int, per_page: int) -> dict:
        user_subscriptions = db.session.scalars(g.current_user.following.select()).all()
        user_communities = db.session.scalars(g.current_user.communities.select()).all()
        similarity_vector = get_similarity_vector()
        filtered_users = [{"user": user, "weight": 0} for user in self.users_repository.get_users() if
                          user not in user_subscriptions and user != g.current_user]
        for item in filtered_users:
            subscriptions = db.session.scalars(item["user"].following.select()).all()
            for subscription in subscriptions:
                if subscription in user_subscriptions:
                    item["weight"] += SUBSCRIPTION_WEIGHT
            if item["user"].city == g.current_user.city and g.current_user.city is not None:
                item["weight"] += SAME_ATTRIBUTES_WEIGHT
            communities = db.session.scalars(item["user"].communities.select()).all()
            for community in user_communities:
                if community in communities:
                    item["weight"] += SAME_COMMUNITY_WEIGHT
            for element in similarity_vector:
                item["weight"] += element["similarity"] * SIMILARITY_COEFFICIENT
        filtered_users.sort(key=lambda el: el["weight"], reverse=True)
        page -= 1
        total_items = len(filtered_users)
        recommended_friends = [self.users_repository.model_to_dict(item["user"]) for item in filtered_users][
                              page * per_page:(page + 1) * per_page]
        return {
            "items": recommended_friends,
            'meta': {
                'page': page + 1,
                'per_page': per_page,
                'total_pages': math.ceil(total_items / per_page),
                'total_items': total_items
            },
        }

    def get_recommended_employees(self, vacancy_id: int, page: int, per_page: int) -> dict:
        vacancy: Vacancy = db.session.get(Vacancy, vacancy_id)
        vacancy_skills = vacancy.skills.split(",")
        users = [{"user": user, "weight": 0} for user in self.users_repository.get_users()]
        for item in users:
            if item["user"].skills:
                skills = item["user"].skills.split(",")
                for skill in skills:
                    if skill in vacancy_skills:
                        item["weight"] += SKILL_WEIGHT
        users = [item for item in users if item["weight"] > 0]
        users.sort(key=lambda el: el["weight"], reverse=True)
        page -= 1
        total_items = len(users)
        recommended_employees = [self.users_repository.model_to_dict(item["user"]) for item in users][
                                page * per_page:(page + 1) * per_page]
        return {
            "items": recommended_employees,
            'meta': {
                'page': page + 1,
                'per_page': per_page,
                'total_pages': math.ceil(total_items / per_page),
                'total_items': total_items
            },
        }

    def update_password(self, username: str, password: str, new_password: str) -> dict:
        user = self.users_repository.get_by_username(username)
        if check_password(user, password):
            set_password(user, new_password)
        else:
            abort(422, "Проверьте пароль")
        return self.users_repository.model_to_dict(user)

    def update_user(self, username: str, data: dict) -> dict:
        user = self.users_repository.get_by_username(username)
        if 'username' in data and data['username'] != username:
            user_exist = self.users_repository.get_by_username(data["username"], False)
            if user_exist:
                abort(422, 'Пользователь с таким именем уже существует')
        if 'email' in data and data['email'] != user.email:
            user_exist = self.users_repository.get_by_email(data["email"], False)
            if user_exist:
                abort(422, 'Пользователь с таким email уже существует')
        avatar = data.get("avatar")
        if avatar:
            self.upload_avatar(user, avatar)
            del data["avatar"]
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        self.users_repository.update_model_from_dict(user, data)
        return self.users_repository.model_to_dict(user)

    def upload_avatar(self, user: User, file) -> None:
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        filename = f'{md5(user.username.encode('utf-8')).hexdigest()}.{extension}'
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.mkdir(app.config['UPLOAD_FOLDER'])
        file.save(avatar_path)
        avatar_url: str = f'/static/images/{filename}'
        self.users_repository.update_avatar_url(user, avatar_url)

    def add_user(self, data: dict) -> dict:
        user_exist = self.users_repository.get_by_username_or_email(data["username"], data["email"], False)
        if not user_exist:
            password = data['password']
            del data['password']
            avatar = data.get("avatar")
            if avatar:
                del data["avatar"]
            for key, value in data.items():
                if type(value) is str:
                    data[key] = value.strip()
            user: User = self.users_repository.add(data, password)
            if avatar:
                self.upload_avatar(user, avatar)
            g.current_user = user
            return self.users_repository.model_to_dict(user)
        else:
            abort(422, 'Пользователь с таким именем или email уже существует!')

    def delete_user(self, username: str) -> None:
        self.users_repository.delete_by_username(username)

    def get_friends(self, username: str, filters: dict, page: int, per_page: int, relation: str | None) -> dict:
        user: User = self.users_repository.get_by_username(username)
        query = self.users_repository.get_friends(user)
        if relation:
            if relation == 'followers':
                query = self.users_repository.get_followers_without_friends(user)
            elif relation == 'following':
                query = self.users_repository.get_following_without_friends(user)
        return self.users_repository.paginate_by_filters(
            {field: value for field, value in filters.items() if value}, page, per_page, query
        )

    def add_friend(self, username: str) -> None:
        user: User = self.users_repository.get_by_username(username)
        if g.current_user == user:
            abort(422, "Невозможно отправить заявку самому себе")
        self.users_repository.follow(g.current_user, user)

    def accept_friend(self, username: str) -> bool:
        user: User = self.users_repository.get_by_username(username)
        if self.users_repository.is_following(user, g.current_user):
            self.users_repository.follow(g.current_user, user)
            return True
        else:
            return False

    def delete_friend(self, username: str) -> None:
        user: User = self.users_repository.get_by_username(username)
        self.users_repository.unfollow(g.current_user, user)
