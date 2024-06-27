from abc import ABC, abstractmethod

import sqlalchemy as sa

from app import db
from app.models import Message, User
from app.utils import paginate


class MessageRepositoryInterface(ABC):
    @abstractmethod
    def paginate_by_filters(
            self, page: int, per_page: int, query: sa.Select[tuple[Message]] = sa.select(Message)) -> dict:
        pass

    @abstractmethod
    def get_messages(self, user: User, friend: User) -> sa.Select[tuple[Message]]:
        pass

    @abstractmethod
    def add(self, data: dict) -> Message:
        pass

    @abstractmethod
    def model_to_dict(self, model: Message) -> dict:
        pass


class MessageRepository(MessageRepositoryInterface):
    def add(self, data: dict) -> Message:
        message: Message = Message(**data)
        db.session.add(message)
        db.session.commit()
        return message

    def get_messages(self, user: User, friend: User) -> sa.Select[tuple[Message]]:
        return sa.select(Message).where(sa.or_(sa.and_(Message.sender == user, Message.recipient == friend),
                                               sa.and_(Message.sender == friend, Message.recipient == user)))

    def paginate_by_filters(
            self, page: int, per_page: int, query: sa.Select[tuple[Message]] = sa.select(Message)) -> dict:
        return paginate(query, Message, self, {}, page, per_page, 'messages', Message.date)

    def model_to_dict(self, model: Message) -> dict:
        data = {
            'id': model.id,
            'body': model.body,
            'date': str(model.date or ''),
            'sender': model.sender.username,
            'recipient': model.recipient.username,
        }
        return data
