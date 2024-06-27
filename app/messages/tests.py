import os
from unittest import TestCase, main

from flask import g

from app import app, db
from app.messages.repository import MessageRepository
from app.messages.service import MessageService
from app.models import User, Message
from app.users.repository import UserRepository

os.environ['DATABASE_URI'] = 'sqlite://'


class MessageModelCase(TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.service = MessageService(MessageRepository(), UserRepository())
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_messages(self):
        with app.app_context(), app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            user3: User = User(username="alex", email="alex@example.com", firstname="Алексей", lastname="Иванов")
            user1.following.add(user2)
            user2.following.add(user1)
            user1.following.add(user3)
            user3.following.add(user1)
            message1: Message = Message(body="Привет")
            message1.sender = user1
            message1.recipient = user2
            message2: Message = Message(body="Здравствуйте")
            message2.sender = user2
            message2.recipient = user1
            message3: Message = Message(body="Добрый день")
            message3.sender = user3
            message3.recipient = user1
            db.session.add_all([user1, user2, user3, message1, message2, message3])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_messages('petr', 1, 3)
            self.assertEqual(len(result["items"]), 2)
            self.assertEqual(result["items"][0]["body"], "Привет")
            self.assertEqual(result["items"][0]["recipient"], "petr")
            self.assertEqual(result["items"][1]["body"], "Здравствуйте")
            self.assertEqual(result["items"][1]["recipient"], "ivan")
            result: dict = self.service.get_messages('alex', 1, 3)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["sender"], "alex")
            g.current_user = user3
            result: dict = self.service.get_messages('ivan', 1, 3)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["recipient"], "ivan")

    def test_add_message(self):
        with app.app_context(), app.test_request_context():
            sender: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            recipient: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            sender.following.add(recipient)
            recipient.following.add(sender)
            db.session.add_all([sender, recipient])
            db.session.commit()
            g.current_user = sender
            result: dict = self.service.add_message(
                {"body": "Привет", "recipient": recipient.username}
            )
            message: Message = db.session.get(Message, result["id"])
            self.assertEqual(message.body, "Привет")


if __name__ == '__main__':
    main(verbosity=2)
