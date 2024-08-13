import os
from unittest import TestCase, main

from flask import g

from app import create_app, db
from app.models import User
from app.users.repository import UserRepository
from app.users.service import UserService
from app.users.utils import set_password, check_password
from config import TestConfig


class UserModelCase(TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.service = UserService(UserRepository())
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_user(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="test", email="test@example.com", firstname="Иван", lastname="Петров")
            set_password(user, "123123123")
            db.session.add(user)
            db.session.commit()
            g.current_user = user
            result: dict = self.service.get_user(user.username)
            self.assertEqual(result["email"], user.email)

    def test_get_users(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            set_password(user1, "123123123")
            set_password(user2, "123123123")
            db.session.add_all([user1, user2])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_users({}, 1, 2)
            self.assertEqual(result["items"][0]["email"], user1.email)
            self.assertEqual(result["items"][1]["email"], user2.email)
            result: dict = self.service.get_users({"firstname": "вА"}, 1, 2)
            self.assertEqual(len(result["items"]), 1)

    def test_update_password(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            set_password(user, "123123123")
            db.session.add(user)
            db.session.commit()
            g.current_user = user
            self.service.update_password("ivan", "123123123", "000000000")
            self.assertFalse(check_password(user, "123123123"))
            self.assertTrue(check_password(user, "000000000"))

    def test_update_user(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            set_password(user, "123123123")
            db.session.add(user)
            db.session.commit()
            g.current_user = user
            self.service.update_user("ivan", {"username": "new_ivan", "lastname": "Сидоров"})
            self.assertEqual(user.username, "new_ivan")
            self.assertEqual(user.firstname, "Иван")
            self.assertEqual(user.lastname, "Сидоров")
            self.assertNotEqual(user.lastname, "Петров")

    def test_add_user(self):
        with self.app.app_context(), self.app.test_request_context():
            result: dict = self.service.add_user({
                "username": "petr",
                "email": "petr@example.com",
                "firstname": "Петр",
                "lastname": "Иванов",
                "password": "123456789",
            })
            user: User = db.session.get(User, 1)
            self.assertEqual(user.username, result["username"])
            self.assertEqual(user.email, result["email"])
            self.assertEqual(user.firstname, result["firstname"])
            self.assertEqual(user.lastname, result["lastname"])
            self.assertTrue(check_password(user, "123456789"))

    def test_delete_user(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            set_password(user, "123123123")
            db.session.add(user)
            db.session.commit()
            self.service.delete_user("ivan")
            user: User = db.session.get(User, 1)
            self.assertEqual(user, None)

    def test_get_friends(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            user3: User = User(username="cat", email="cat@example.com", firstname="Катя", lastname="Сидорова")
            set_password(user1, "123123123")
            set_password(user2, "123123123")
            set_password(user3, "123123123")
            db.session.add_all([user1, user2, user3])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_friends("ivan", {}, 1, 3, "")
            self.assertEqual(result["items"], [])
            user1.following.add(user2)
            user1_following: dict = self.service.get_friends("ivan", {}, 1, 3, "following")
            self.assertEqual(user1_following["items"][0]["username"], "petr")
            user1_friends: dict = self.service.get_friends("ivan", {}, 1, 3, "")
            self.assertEqual(user1_friends["items"], [])
            user2_followers: dict = self.service.get_friends("petr", {}, 1, 3, "followers")
            self.assertEqual(user2_followers["items"][0]["username"], "ivan")
            user2.following.add(user1)
            user1_friends: dict = self.service.get_friends("ivan", {}, 1, 3, "")
            self.assertEqual(user1_friends["items"][0]["username"], "petr")
            user2_friends: dict = self.service.get_friends("petr", {}, 1, 3, "")
            self.assertEqual(user2_friends["items"][0]["username"], "ivan")
            user1.following.add(user3)
            user3.following.add(user1)
            db.session.commit()
            user1_filter_friends: dict = self.service.get_friends("ivan", {}, 1, 1, None)
            self.assertEqual(user1_filter_friends["items"][0]["username"], "petr")
            self.assertEqual(len(user1_filter_friends["items"]), 1)
            user1_filter_friends: dict = self.service.get_friends("ivan", {}, 2, 1, None)
            self.assertEqual(user1_filter_friends["items"][0]["username"], "cat")
            self.assertEqual(len(user1_filter_friends["items"]), 1)

    def test_add_friend(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            set_password(user1, "123123123")
            set_password(user2, "123123123")
            db.session.add_all([user1, user2])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_friends("ivan", {}, 1, 3, "following")
            self.assertEqual(result["items"], [])
            self.service.add_friend("petr")
            user1_following: dict = self.service.get_friends("ivan", {}, 1, 3, "following")
            self.assertEqual(user1_following["items"][0]["username"], "petr")
            user2_followers: dict = self.service.get_friends("petr", {}, 1, 3, "followers")
            self.assertEqual(user2_followers["items"][0]["username"], "ivan")

    def test_accept_friend(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            set_password(user1, "123123123")
            set_password(user2, "123123123")
            db.session.add_all([user1, user2])
            db.session.commit()
            g.current_user = user1
            self.service.add_friend("petr")
            g.current_user = user2
            self.service.accept_friend("ivan")
            user1_following: dict = self.service.get_friends("ivan", {}, 1, 3, "following")
            self.assertEqual(user1_following["items"], [])
            user1_friends: dict = self.service.get_friends("ivan", {}, 1, 3, None)
            self.assertEqual(user1_friends["items"][0]["username"], "petr")

    def test_delete_friend(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            set_password(user1, "123123123")
            set_password(user2, "123123123")
            db.session.add_all([user1, user2])
            db.session.commit()
            g.current_user = user1
            self.service.add_friend("petr")
            g.current_user = user2
            self.service.accept_friend("ivan")
            self.service.delete_friend("ivan")
            user1_friends: dict = self.service.get_friends("ivan", {}, 1, 3, None)
            self.assertEqual(len(user1_friends["items"]), 0)


if __name__ == '__main__':
    main(verbosity=2)
