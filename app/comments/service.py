from abc import ABC, abstractmethod

import sqlalchemy as sa
from flask import g, abort

from app.comments.repository import CommentRepositoryInterface
from app.models import Post, Comment
from app.posts.repository import PostRepositoryInterface
from app.users.repository import UserRepositoryInterface


class CommentServiceInterface(ABC):
    comment_repository: CommentRepositoryInterface
    post_repository: PostRepositoryInterface
    user_repository: UserRepositoryInterface

    @abstractmethod
    def get_comments(self, post_id: int | None, page: int, per_page: int) -> dict:
        pass

    @abstractmethod
    def add_comment(self, data: dict) -> dict:
        pass

    @abstractmethod
    def update_comment(self, comment_id: int, data: dict) -> dict:
        pass

    @abstractmethod
    def delete_comment(self, comment_id: int) -> None:
        pass


class CommentService(CommentServiceInterface):
    def __init__(self, comment_repository: CommentRepositoryInterface,
                 post_repository: PostRepositoryInterface,
                 user_repository: UserRepositoryInterface):
        self.comment_repository = comment_repository
        self.post_repository = post_repository
        self.user_repository = user_repository

    def add_comment(self, data: dict) -> dict:
        author_id = data.get('user_id')
        if not author_id or self.user_repository.get_by_id(int(author_id)) != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        comment: Comment = self.comment_repository.add(data)
        return self.comment_repository.model_to_dict(comment)

    def update_comment(self, comment_id: int, data: dict) -> dict:
        comment: Comment = self.comment_repository.get_by_id(comment_id)
        if comment.author != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        self.comment_repository.update_model_from_dict(comment, data)
        return self.comment_repository.model_to_dict(comment)

    def get_comments(self, post_id: int | None, page: int, per_page: int) -> dict:
        query = sa.select(Comment)
        if post_id:
            post: Post = self.post_repository.get_by_id(post_id)
            query = post.comments.select()
        return self.comment_repository.paginate_by_filters(page, per_page, query)

    def get_comment(self, post_id: int) -> dict:
        return self.post_repository.model_to_dict(self.post_repository.get_by_id(post_id))

    def delete_comment(self, comment_id: int) -> None:
        comment: Comment = self.comment_repository.get_by_id(comment_id)
        if comment.author != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        self.comment_repository.delete(comment)
