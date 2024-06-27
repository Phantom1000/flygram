from abc import ABC, abstractmethod

import sqlalchemy as sa

from app import db
from app.models import Comment, User
from app.utils import paginate


class CommentRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, comment_id: int) -> Comment:
        pass

    @abstractmethod
    def paginate_by_filters(
            self, page: int, per_page: int, query: sa.Select[tuple[Comment]] = sa.select(Comment)) -> dict:
        pass

    @abstractmethod
    def add(self, data: dict) -> Comment:
        pass

    @abstractmethod
    def update_model_from_dict(self, model: Comment, data: dict):
        pass

    @abstractmethod
    def delete(self, comment: Comment) -> None:
        pass

    @abstractmethod
    def model_to_dict(self, model: Comment) -> dict:
        pass


class CommentRepository(CommentRepositoryInterface):
    def get_by_id(self, comment_id: int) -> Comment:
        return db.get_or_404(Comment, comment_id)

    def add(self, data: dict) -> Comment:
        comment: Comment = Comment(**data)
        db.session.add(comment)
        db.session.commit()
        return comment

    def paginate_by_filters(
            self, page: int, per_page: int, query: sa.Select[tuple[Comment]] = sa.select(Comment)) -> dict:
        return paginate(query, Comment, self, {}, page, per_page, 'comments', Comment.date)

    def delete(self, comment: Comment) -> None:
        db.session.delete(comment)
        db.session.commit()

    def update_model_from_dict(self, model: Comment, data: dict):
        for field in ['text']:
            if field in data:
                setattr(model, field, data[field])
        db.session.commit()

    def model_to_dict(self, model: Comment) -> dict:
        data = {
            'id': model.id,
            'text': model.text,
            'date': str(model.date or ''),
            'author': model.author.username,
            'post': model.post_id,
        }
        return data
