import jwt
import sqlalchemy as sa
from flask import request, current_app as app
from flask.views import MethodView
from flask_socketio import send, join_room, leave_room

from app import socketio, db
from app.auth import token_auth
from app.messages.repository import MessageRepository
from app.messages.service import MessageServiceInterface
from app.models import User, Message
from app.users.repository import UserRepository


@socketio.on('joined', namespace='/chat')
def joined(data):
    sender: User = db.session.scalars(sa.select(User).filter_by(username=data["sender"])).first()
    recipient: User = db.session.scalars(sa.select(User).filter_by(username=data["recipient"])).first()
    repo = UserRepository()
    friends = db.session.scalars(repo.get_friends(sender)).all()
    if recipient and recipient in friends:
        to_room: str = f"{sender.username}:{recipient.username}"
        from_room: str = f"{recipient.username}:{sender.username}"
        join_room(to_room)
        join_room(from_room)


@socketio.on('message', namespace='/chat')
def send_message(data):
    if data:
        token = data.get("token")
        if token:
            try:
                payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=["HS256"])
                repo = UserRepository()
                sender: User = repo.get_by_id(payload["id"])
            except jwt.DecodeError:
                return False
            except jwt.ExpiredSignatureError:
                return False
            except jwt.InvalidTokenError:
                return False
            # sender: User = db.session.scalars(sa.select(User).filter_by(username=data["sender"])).first()
            recipient: User = db.session.scalars(sa.select(User).filter_by(username=data["recipient"])).first()
            body: str = data["body"]
            repo = MessageRepository()
            message: Message = Message(recipient_id=recipient.id, sender_id=sender.id, body=body)
            db.session.add(message)
            db.session.commit()
            response: dict = repo.model_to_dict(message)
            if message:
                room: str = f"{sender.username}:{recipient.username}"
                send({'data_message': response}, to=room)


@socketio.on('left', namespace='/chat')
def left(data):
    sender: User = db.session.scalars(sa.select(User).filter_by(username=data["sender"])).first()
    recipient: User = db.session.scalars(sa.select(User).filter_by(username=data["recipient"])).first()
    to_room: str = f"{sender.username}:{recipient.username}"
    from_room: str = f"{recipient.username}:{sender.username}"
    leave_room(to_room)
    leave_room(from_room)


class MessagesAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: MessageServiceInterface

    def __init__(self, service: MessageServiceInterface):
        self.service = service

    def get(self):
        """Получение списка сообщений диалога"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 6, type=int), 100)
        username = request.args.get('username')
        return self.service.get_messages(username, page, per_page)
