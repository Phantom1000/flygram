import math
import os
import uuid
from abc import ABC, abstractmethod
from app.utils import get_similarity_vector

import sqlalchemy as sa
from flask import g, current_app as app, abort
from werkzeug.utils import secure_filename

from app.models import Post, Community
from app.models import User
from app.posts.repository import PostRepositoryInterface
from app.users.repository import UserRepositoryInterface
from app.communities.repository import CommunityRepositoryInterface
from datetime import datetime
from app import db

FRIEND_LIKE_WEIGHT = 5
AUTHOR_FRIEND_WEIGHT = 10
HASHTAG_LIKE_WEIGHT = 2
COMMUNITY_WEIGHT = 1
SIMILARITY_COEFFICIENT = 2


class PostServiceInterface(ABC):
    user_repository: UserRepositoryInterface
    post_repository: PostRepositoryInterface
    community_repository: CommunityRepositoryInterface

    @abstractmethod
    def get_post(self, post_id: int) -> dict:
        pass

    @abstractmethod
    def get_posts(
            self, author_name: str | None, community_id: int | None,
            posts_type: str | None, filters: dict, page: int, per_page: int) -> dict:
        pass

    @abstractmethod
    def add_post(self, data: dict) -> dict:
        pass

    @abstractmethod
    def update_post(self, post_id: int, data: dict) -> dict:
        pass

    @abstractmethod
    def delete_post(self, post_id: int) -> None:
        pass

    @abstractmethod
    def upload_image(self, post: Post, image) -> None:
        pass

    @abstractmethod
    def like_post(self, post_id: int) -> None:
        pass

    @abstractmethod
    def unlike_post(self, post_id: int) -> None:
        pass

    @abstractmethod
    def get_recommended_posts(self, page: int, per_page: int) -> dict:
        pass


class PostService(PostServiceInterface):
    def __init__(self, post_repository: PostRepositoryInterface,
                 user_repository: UserRepositoryInterface, community_repository: CommunityRepositoryInterface):
        self.post_repository = post_repository
        self.user_repository = user_repository
        self.community_repository = community_repository

    def add_post(self, data: dict) -> dict:
        author_id = data.get('user_id')
        community_id = data.get('community_id')
        if author_id:
            if self.user_repository.get_by_id(int(author_id)) != g.current_user:
                abort(403, 'У Вас нет прав доступа')
        if community_id:
            if self.community_repository.get_by_id(int(community_id)).owner != g.current_user:
                abort(403, 'У Вас нет прав доступа')
        image = data.get("image")
        if image:
            del data["image"]
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        data['hashtags'] = data['hashtags'].lower().replace(" ", "")
        post: Post = self.post_repository.add(data)
        if image:
            self.upload_image(post, image)
        return self.post_repository.model_to_dict(post)

    def update_post(self, post_id: int, data: dict) -> dict:
        post: Post = self.post_repository.get_by_id(post_id)
        if ((post.user_id is not None and post.author != g.current_user)
                or (post.community_id is not None and post.community.owner != g.current_user)):
            abort(403, 'У Вас нет прав доступа')
        image = data.get("image")
        if image:
            del data["image"]
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        data['hashtags'] = data['hashtags'].lower().replace(" ", "")
        self.post_repository.update_model_from_dict(post, data)
        if image:
            self.upload_image(post, image)
        return self.post_repository.model_to_dict(post)

    def upload_image(self, post: Post, image) -> None:
        filename = secure_filename(image.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        filename = f'{str(uuid.uuid4())}.{extension}'
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.mkdir(app.config['UPLOAD_FOLDER'])
        image.save(image_path)
        image_url = f'/static/images/{filename}'
        self.post_repository.update_image_url(post, image_url)

    def get_posts(
            self, author_name: str | None, community_id: int | None,
            posts_type: str | None, filters: dict, page: int, per_page: int) -> dict:
        query = sa.select(Post)
        if author_name:
            author: User = self.user_repository.get_by_username(author_name)
            query = author.posts.select()
        if community_id:
            community: Community = self.community_repository.get_by_id(community_id)
            query = community.community_posts.select()
        if posts_type:
            if posts_type == 'liked':
                query = g.current_user.liked_posts.select()
            if posts_type == 'recommended':
                return self.get_recommended_posts(page, per_page)
        return self.post_repository.paginate_by_filters(
            {field: value for field, value in filters.items() if value}, page, per_page, query
        )

    def get_recommended_posts(self, page: int, per_page: int) -> dict:
        filtered_posts = self.post_repository.get_posts_by_date_and_rating(datetime(2024, 1, 1), 0)
        liked_posts = db.session.scalars(g.current_user.liked_posts.select()).all()
        liked_hashtags = set()
        communities = db.session.scalars(g.current_user.communities.select()).all()
        for post in liked_posts:
            liked_hashtags.update(post.hashtags.split(","))
        similarity_vector = get_similarity_vector()
        modified_posts = [{"post": post, "weight": 0} for post in filtered_posts if post not in liked_posts]
        for item in modified_posts:
            if (self.user_repository.is_following(g.current_user, item["post"].author) or
                    item["post"].community and
                    self.community_repository.is_member(item["post"].community, g.current_user)):
                item["weight"] += AUTHOR_FRIEND_WEIGHT
            if item["post"].author.city == g.current_user.city and g.current_user.city is not None:
                item["weight"] += AUTHOR_FRIEND_WEIGHT
            author_communities = db.session.scalars(item["post"].author.communities.select()).all()
            for community in author_communities:
                if community in communities:
                    item["weight"] += COMMUNITY_WEIGHT
            friends = db.session.scalars(g.current_user.following.select())
            liked_users = db.session.scalars(item["post"].liked_users.select()).all()
            item["likes"] = len(liked_users)
            for friend in friends:
                if friend in liked_users:
                    item["weight"] += FRIEND_LIKE_WEIGHT
            hashtags = item["post"].hashtags.split(",")
            for hashtag in hashtags:
                if hashtag in liked_hashtags:
                    item["weight"] += HASHTAG_LIKE_WEIGHT
            for element in similarity_vector:
                liked_posts = db.session.scalars(element["user"].liked_posts.select())
                if item["post"] in liked_posts:
                    item["weight"] += element["similarity"] * SIMILARITY_COEFFICIENT
        modified_posts.sort(key=lambda el: el["weight"], reverse=True)
        if modified_posts[0]["weight"] == 0:
            modified_posts.sort(key=lambda el: el["likes"], reverse=True)
        page -= 1
        total_items = len(modified_posts)
        recommended_posts = [self.post_repository.model_to_dict(item["post"]) for item in modified_posts][
                            page * per_page:(page + 1) * per_page]
        return {
            "items": recommended_posts,
            'meta': {
                'page': page + 1,
                'per_page': per_page,
                'total_pages': math.ceil(total_items / per_page),
                'total_items': total_items
            },
        }

    def get_post(self, post_id: int) -> dict:
        return self.post_repository.model_to_dict(self.post_repository.get_by_id(post_id))

    def delete_post(self, post_id: int) -> None:
        post: Post = self.post_repository.get_by_id(post_id)
        if ((post.user_id is not None and post.author != g.current_user)
                or (post.community_id is not None and post.community.owner != g.current_user)):
            abort(403, 'У Вас нет прав доступа')
        self.post_repository.delete(post)

    def like_post(self, post_id: int) -> None:
        post: Post = self.post_repository.get_by_id(post_id)
        if not self.post_repository.is_liked(post, g.current_user):
            self.post_repository.like_post(post, g.current_user)

    def unlike_post(self, post_id: int) -> None:
        post: Post = self.post_repository.get_by_id(post_id)
        if self.post_repository.is_liked(post, g.current_user):
            self.post_repository.unlike_post(post, g.current_user)
