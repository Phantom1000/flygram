import math
from abc import ABC, abstractmethod
from hashlib import md5

import sqlalchemy as sa
from flask import g, abort, current_app as app
from werkzeug.utils import secure_filename
import os
from app.communities.repository import CommunityRepositoryInterface
from app.models import Post, Community, User
from app.posts.repository import PostRepositoryInterface
from app.users.repository import UserRepositoryInterface
from app import db
from app.utils import get_similarity_vector

SUBSCRIPTION_WEIGHT = 5
LIKED_POST_WEIGHT = 3
SIMILARITY_COEFFICIENT = 2


class CommunityServiceInterface(ABC):
    community_repository: CommunityRepositoryInterface
    post_repository: PostRepositoryInterface
    user_repository: UserRepositoryInterface

    @abstractmethod
    def get_communities(self, user_id: int | None, community_type: str, filters: dict, page: int,
                        per_page: int) -> dict:
        pass

    @abstractmethod
    def get_community(self, community_id: int):
        pass

    @abstractmethod
    def add_community(self, data: dict) -> dict:
        pass

    @abstractmethod
    def update_community(self, community_id: int, data: dict) -> dict:
        pass

    @abstractmethod
    def delete_community(self, community_id: int) -> None:
        pass

    @abstractmethod
    def upload_image(self, post: Post, image) -> None:
        pass

    @abstractmethod
    def join_community(self, community_id: int) -> None:
        pass

    @abstractmethod
    def leave_community(self, community_id: int) -> None:
        pass

    @abstractmethod
    def get_members(self, community_id: int, filters: dict, page: int, per_page: int) -> dict:
        pass

    @abstractmethod
    def get_recommended_communities(self, page: int, per_page: int):
        pass


class CommunityService(CommunityServiceInterface):
    def __init__(self, community_repository: CommunityRepositoryInterface, user_repository: UserRepositoryInterface):
        self.community_repository = community_repository
        self.user_repository = user_repository

    def upload_image(self, community: Community, image) -> None:
        filename = secure_filename(image.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        filename = f'{md5(community.owner.username.encode('utf-8')).hexdigest()}.{extension}'
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'communities', filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.mkdir(app.config['UPLOAD_FOLDER'])
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'communities')):
            os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], 'communities'))
        image.save(image_path)
        image_url: str = f'/static/images/communities/{filename}'
        self.community_repository.update_image_url(community, image_url)

    def add_community(self, data: dict) -> dict:
        owner_id = data.get('user_id')
        if not owner_id or self.user_repository.get_by_id(int(owner_id)) != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        image = data.get("image")
        if image:
            del data["image"]
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        community: Community = self.community_repository.add(data)
        self.community_repository.join(community, g.current_user)
        if image:
            self.upload_image(community, image)
        return self.community_repository.model_to_dict(community)

    def update_community(self, community_id: int, data: dict) -> dict:
        community: Community = self.community_repository.get_by_id(community_id)
        if community.owner != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        image = data.get("image")
        if image:
            del data["image"]
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        self.community_repository.update_model_from_dict(community, data)
        if image:
            self.upload_image(community, image)
        return self.community_repository.model_to_dict(community)

    def get_communities(self, username: str | None, community_type: str | None, filters: dict, page: int,
                        per_page: int) -> dict:
        query = sa.select(Community)
        if username:
            user: User = self.user_repository.get_by_username(username)
            if community_type == 'admin':
                query = user.own_communities.select()
            else:
                query = user.communities.select()
        if community_type == 'recommended':
            return self.get_recommended_communities(page, per_page)
        return self.community_repository.paginate_by_filters(
            {field: value for field, value in filters.items() if value}, page, per_page, query)

    def get_recommended_communities(self, page: int, per_page: int) -> dict:
        user_subscriptions = db.session.scalars(g.current_user.following.select()).all()
        user_communities = db.session.scalars(g.current_user.communities.select()).all()
        liked_posts = db.session.scalars(g.current_user.liked_posts.select()).all()
        similarity_vector = get_similarity_vector()
        filtered_communities = [{"community": community, "weight": 0} for community in
                                self.community_repository.get_communities() if community not in user_communities]
        for item in filtered_communities:
            members = db.session.scalars(item["community"].members.select()).all()
            for member in members:
                if member in user_subscriptions:
                    item["weight"] += SUBSCRIPTION_WEIGHT
            community_posts = db.session.scalars(item["community"].community_posts.select()).all()
            for post in community_posts:
                if post in liked_posts:
                    item["weight"] += LIKED_POST_WEIGHT
            for element in similarity_vector:
                if element["user"] in members:
                    item["weight"] += element["similarity"] * SIMILARITY_COEFFICIENT
        filtered_communities.sort(key=lambda el: el["weight"], reverse=True)
        page -= 1
        total_items = len(filtered_communities)
        recommended_communities = [self.community_repository.model_to_dict(item["community"]) for item in
                                   filtered_communities][page * per_page:(page + 1) * per_page]
        return {
            "items": recommended_communities,
            'meta': {
                'page': page + 1,
                'per_page': per_page,
                'total_pages': math.ceil(total_items / per_page),
                'total_items': total_items
            },
        }

    def get_community(self, community_id: int):
        return self.community_repository.model_to_dict(self.community_repository.get_by_id(community_id))

    def delete_community(self, community_id: int) -> None:
        community: Community = self.community_repository.get_by_id(community_id)
        if community.owner != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        self.community_repository.delete(community)

    def join_community(self, community_id: int) -> None:
        community: Community = self.community_repository.get_by_id(community_id)
        if not self.community_repository.is_member(community, g.current_user):
            self.community_repository.join(community, g.current_user)

    def leave_community(self, community_id: int) -> None:
        community: Community = self.community_repository.get_by_id(community_id)
        if self.community_repository.is_member(community, g.current_user) and community.owner != g.current_user:
            self.community_repository.leave(community, g.current_user)

    def get_members(self, community_id: int, filters: dict, page: int, per_page: int) -> dict:
        community: Community = self.community_repository.get_by_id(community_id)
        return self.user_repository.paginate_by_filters(
            {field: value for field, value in filters.items() if value},
            page, per_page, community.members.select(), 'members', community_id=community_id
        )
