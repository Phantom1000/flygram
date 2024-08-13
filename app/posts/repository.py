from abc import ABC, abstractmethod
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from app.models import Post, User, likes
from app.utils import paginate
from flask import g, url_for
from datetime import datetime


class PostRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, post_id: int) -> Post:
        pass

    @abstractmethod
    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[Post]] = sa.select(Post)) -> dict:
        pass

    @abstractmethod
    def get_following_posts(self, user: User) -> sa.Select[tuple[Post]]:
        pass

    @abstractmethod
    def add(self, data: dict) -> Post:
        pass

    @abstractmethod
    def update_model_from_dict(self, model: Post, data: dict):
        pass

    @abstractmethod
    def delete(self, post: Post) -> None:
        pass

    @abstractmethod
    def update_image_url(self, post: Post, image_url: str) -> None:
        pass

    @abstractmethod
    def is_liked(self, post: Post, user: User) -> bool:
        pass

    @abstractmethod
    def like_post(self, post: Post, user: User) -> None:
        pass

    @abstractmethod
    def unlike_post(self, post: Post, user: User) -> None:
        pass

    @abstractmethod
    def model_to_dict(self, model: Post) -> dict:
        pass

    @abstractmethod
    def likes_count(self, post: Post) -> int:
        pass

    @abstractmethod
    def get_posts_by_date_and_rating(self, date: datetime, rating: int):
        pass


class PostRepository(PostRepositoryInterface):
    def get_by_id(self, post_id: int) -> Post:
        return db.get_or_404(Post, post_id)

    def add(self, data: dict) -> Post:
        post: Post = Post(**data)
        db.session.add(post)
        db.session.commit()
        return post

    def update_image_url(self, post: Post, image_url: str) -> None:
        post.image_url = image_url
        db.session.commit()

    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[Post]] = sa.select(Post)) -> dict:
        return paginate(query.options(so.joinedload(Post.author)), Post, self, filters, page, per_page, 'posts',
                        Post.publication_date)

    def get_following_posts(self, user: User) -> sa.Select[tuple[Post]]:
        author = so.aliased(User)
        follower = so.aliased(User)
        query = (sa.select(Post).join(
            Post.author.of_type(author)).join(User.followers.of_type(follower)).where(follower.id == user.id))
        return query

    def delete(self, post: Post) -> None:
        db.session.delete(post)
        db.session.commit()

    def update_model_from_dict(self, model: Post, data: dict):
        for field in ['hashtags', 'text']:
            if field in data:
                setattr(model, field, data[field])
        db.session.commit()

    def is_liked(self, post: Post, user: User) -> bool:
        query = post.liked_users.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def like_post(self, post: Post, user: User) -> None:
        post.liked_users.add(user)
        db.session.commit()

    def unlike_post(self, post: Post, user: User) -> None:
        post.liked_users.remove(user)
        db.session.commit()

    def likes_count(self, post: Post) -> int:
        query = sa.select(sa.func.count()).select_from(post.liked_users.select().subquery())
        return db.session.scalar(query)

    def get_posts_by_date_and_rating(self, date: datetime, rating: int):
        query = sa.select(Post).join(likes, likes.c.post_id == Post.id, isouter=True).where(
            sa.and_(Post.publication_date > date, sa.not_(Post.user_id == g.current_user.id))).group_by(
            Post.id).having(
            sa.and_(sa.func.count(likes.c.user_id) >= rating))
        # sa.not_(likes.c.user_id == g.current_user.id)
        result = db.session.scalars(query).all()
        return result

    def model_to_dict(self, model: Post) -> dict:
        data = {
            'id': model.id,
            'text': model.text,
            'hashtags': model.hashtags,
            'publication_date': str(model.publication_date or ''),
            'author': model.author.username if model.author else None,
            'community': model.community_id,
            'likes_count': self.likes_count(model),
            'is_liked': self.is_liked(model, g.current_user),
            'links': {
                'self': url_for('post', post_id=model.id),
                'image': model.image_url
            }
        }
        return data
