from abc import ABC, abstractmethod
from flask import g, abort

from app.messages.repository import MessageRepositoryInterface
from app.models import Message, User
from app.users.repository import UserRepositoryInterface


class MessageServiceInterface(ABC):
    message_repository: MessageRepositoryInterface
    user_repository: UserRepositoryInterface

    @abstractmethod
    def get_messages(self, username: str, page: int, per_page: int) -> dict:
        pass

    @abstractmethod
    def add_message(self, data: dict) -> dict:
        pass


class MessageService(MessageServiceInterface):
    def __init__(self, message_repository: MessageRepositoryInterface, user_repository: UserRepositoryInterface):
        self.message_repository = message_repository
        self.user_repository = user_repository

    def add_message(self, data: dict) -> dict:
        recipient: User = self.user_repository.get_by_username(data.get('recipient'))
        if not self.user_repository.is_friend(g.current_user, recipient):
            abort(403, 'У Вас нет прав доступа')
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        del data['recipient']
        data.update({'recipient_id': recipient.id, 'sender_id': g.current_user.id})
        message: Message = self.message_repository.add(data)
        return self.message_repository.model_to_dict(message)

    def get_messages(self, username: str, page: int, per_page: int) -> dict:
        user: User = self.user_repository.get_by_username(username)
        if not self.user_repository.is_friend(g.current_user, user):
            abort(403, 'У Вас нет прав доступа')
        return self.message_repository.paginate_by_filters(page, per_page,
                                                           self.message_repository.get_messages(g.current_user, user))
