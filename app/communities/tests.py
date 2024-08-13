from unittest import TestCase, main

from flask import g

from app import create_app, db
from app.communities.repository import CommunityRepository
from app.communities.service import CommunityService
from app.models import User, Community
from app.users.repository import UserRepository
from config import TestConfig


class CommunityModelCase(TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.service = CommunityService(CommunityRepository(), UserRepository())
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            community: Community = Community(name="сообщество программистов", description="создаем приложения")
            community.owner = user
            db.session.add_all([user, community])
            db.session.commit()
            g.current_user = user
            result: dict = self.service.get_community(community.id)
            self.assertEqual(result["name"], community.name)

    def test_get_communities(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            community1: Community = Community(name="сообщество тестировщиков", description="проверяем приложения")
            community1.owner = user1
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            community2: Community = Community(name="сообщество программистов", description="создаем приложения")
            community2.owner = user2
            community1.members.add_all([user1, user2])
            community2.members.add(user2)
            db.session.add_all([user1, user2, community1, community2])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_communities("ivan", None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["name"], "сообщество тестировщиков")
            self.assertEqual(result["items"][0]["description"], "проверяем приложения")
            result: dict = self.service.get_communities(None, None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 2)
            self.assertEqual(result["items"][0]["name"], "сообщество программистов")
            self.assertEqual(result["items"][0]["description"], "создаем приложения")
            result: dict = self.service.get_communities(None, None, {"name": "тест"}, 1, 3)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["name"], "сообщество тестировщиков")
            self.assertEqual(result["items"][0]["description"], "проверяем приложения")

    def test_add_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            db.session.add(user)
            db.session.commit()
            g.current_user = user
            result: dict = self.service.add_community(
                {"name": "сообщество по интересам", "description": "у нас интересно", "user_id": user.id}
            )
            community: Community = db.session.get(Community, result["id"])
            self.assertEqual(community.name, "сообщество по интересам")
            self.assertEqual(community.description,  "у нас интересно")
            self.assertEqual(community.owner, user)

    def test_update_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            community: Community = Community(name="сообщество программистов", description="создаем приложения")
            community.owner = user
            db.session.add_all([user, community])
            db.session.commit()
            g.current_user = user
            result: dict = self.service.update_community(community.id, {"description": "программируем"})
            community: Community = db.session.get(Community, result["id"])
            self.assertEqual(community.description, "программируем")

    def test_delete_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            community: Community = Community(name="сообщество программистов", description="создаем приложения")
            community.owner = user
            db.session.add_all([user, community])
            db.session.commit()
            g.current_user = user
            self.service.delete_community(community.id)
            result: Community | None = db.session.get(Community, 1)
            self.assertEqual(result, None)

    def test_join_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            community: Community = Community(name="сообщество программистов", description="создаем приложения")
            community.owner = user
            db.session.add_all([user, community])
            db.session.commit()
            g.current_user = user
            self.service.join_community(community.id)
            result: list[User] = db.session.scalars(community.members.select()).all()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].username, "ivan")

    def test_leave_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            community: Community = Community(name="сообщество программистов", description="создаем приложения")
            community.owner = user1
            community.members.add_all([user1, user2])
            db.session.add_all([user1, user2, community])
            db.session.commit()
            g.current_user = user2
            self.service.leave_community(community.id)
            result: list[User] = db.session.scalars(community.members.select()).all()
            self.assertEqual(len(result), 1)

    def test_get_members(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            community: Community = Community(name="сообщество программистов", description="создаем приложения")
            community.owner = user1
            community.members.add_all([user1, user2])
            db.session.add_all([user1, user2, community])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_members(community.id, {}, 1, 3)
            self.assertEqual(len(result["items"]), 2)


if __name__ == '__main__':
    main(verbosity=2)
