import os
from unittest import TestCase, main

from flask import g

from app import app, db
from app.models import Post, User, Community
from app.posts.repository import PostRepository
from app.users.repository import UserRepository
from app.communities.repository import CommunityRepository
from app.posts.service import PostService
from datetime import datetime


os.environ['DATABASE_URI'] = 'sqlite://'


class PostModelCase(TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.service = PostService(PostRepository(), UserRepository(), CommunityRepository())
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_post(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            db.session.add_all([post, user])
            db.session.commit()
            g.current_user = user
            result: dict = self.service.get_post(post.id)
            self.assertEqual(result["hashtags"], "новости")
            self.assertEqual(result["text"], "тестирование публикации")

    def test_get_posts(self):
        with app.app_context(), app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Петров")
            post1: Post = Post(hashtags="новости", text="тестирование публикации")
            post2: Post = Post(hashtags="путешествия", text="поездка на отдых")
            post3: Post = Post(hashtags="новости", text="новость дня")
            post1.author = user1
            post2.author = user2
            post3.author = user1
            db.session.add_all([post1, post2, post3, user1, user2])
            post3.liked_users.add(user2)
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_posts(None, None, None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 3)
            result: dict = self.service.get_posts("ivan", None, None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 2)
            self.assertEqual(result["items"][0]["hashtags"], "новости")
            self.assertEqual(result["items"][0]["text"], "тестирование публикации")
            result: dict = self.service.get_posts("petr", None, None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["hashtags"], "путешествия")
            self.assertEqual(result["items"][0]["text"], "поездка на отдых")
            result: dict = self.service.get_posts(None, None, None, {"hashtags": "нов"}, 1, 3)
            self.assertEqual(len(result["items"]), 2)
            self.assertEqual(result["items"][0]["hashtags"], "новости")
            self.assertEqual(result["items"][0]["text"], "новость дня")
            self.assertEqual(result["items"][1]["hashtags"], "новости")
            self.assertEqual(result["items"][1]["text"], "тестирование публикации")
            g.current_user = user2
            result: dict = self.service.get_posts(None, None, "liked", {}, 1, 3)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["hashtags"], "новости")
            self.assertEqual(result["items"][0]["text"], "новость дня")

    def test_get_community_posts(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            community: Community = Community(name="новости", description="самые последние новости")
            community.owner = user
            post1: Post = Post(hashtags="новости", text="тестирование публикации")
            post2: Post = Post(hashtags="путешествия", text="поездка на отдых")
            post3: Post = Post(hashtags="новости", text="новость дня")
            post1.community = community
            post2.community = community
            post3.author = user
            db.session.add_all([post1, post2, post3, user, community])
            post3.liked_users.add(user)
            db.session.commit()
            g.current_user = user
            result: dict = self.service.get_posts(None, None, None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 3)
            result: dict = self.service.get_posts("ivan", None, None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["hashtags"], "новости")
            self.assertEqual(result["items"][0]["text"], "новость дня")
            result: dict = self.service.get_posts(None, 1, None, {}, 1, 3)
            self.assertEqual(len(result["items"]), 2)
            self.assertEqual(result["items"][0]["hashtags"], "новости")
            self.assertEqual(result["items"][0]["text"], "тестирование публикации")

    def test_add_post(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            db.session.add(user)
            db.session.commit()
            g.current_user = user
            result: dict = self.service.add_post(
                {"hashtags": "новости", "text": "тестирование публикации", "user_id": 1}
            )
            self.assertEqual(result["hashtags"], "новости")
            self.assertEqual(result["text"], "тестирование публикации")

    def test_update_post(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            db.session.add_all([post, user])
            db.session.commit()
            g.current_user = user
            result: dict = self.service.update_post(post.id, {
                "hashtags": " ПРИКЛЮЧЕНИЯ  ,новости", "text": "Новый текст"})
            self.assertEqual(result["hashtags"], "приключения,новости")
            self.assertEqual(result["text"], "Новый текст")

    def test_like_post(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            db.session.add_all([post, user])
            db.session.commit()
            g.current_user = user
            self.service.like_post(post.id)
            result: dict = self.service.get_post(post.id)
            self.assertEqual(result["is_liked"], True)
            self.assertEqual(result["likes_count"], 1)

    def test_unlike_post(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            post.liked_users.add(user)
            db.session.add_all([post, user])
            db.session.commit()
            g.current_user = user
            self.service.unlike_post(post.id)
            result: dict = self.service.get_post(post.id)
            self.assertEqual(result["is_liked"], False)
            self.assertEqual(result["likes_count"], 0)

    def test_delete_post(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            db.session.add_all([post, user])
            db.session.commit()
            g.current_user = user
            self.service.delete_post(post.id)
            result: Post | None = db.session.get(Post, 1)
            self.assertEqual(result, None)

    def test_get_recommended_posts(self):
        with app.app_context(), app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Петров")
            user3: User = User(username="alex", email="alex@example.com", firstname="Александр", lastname="Сидоров")
            user4: User = User(username="anna", email="ann@example.com", firstname="Анна", lastname="Варварова")
            user5: User = User(username="ilya", email="ilya@example.com", firstname="Илья", lastname="Иванов")
            user6: User = User(username="test", email="test@example.com", firstname="Илья", lastname="Иванов")
            post1: Post = Post(hashtags="новости", text="тестирование публикации")
            post2: Post = Post(hashtags="путешествия", text="поездка на отдых")
            post3: Post = Post(hashtags="новости, еда", text="новость дня")
            post4: Post = Post(hashtags="готовка, еда", text="приготовление картошки")
            post5: Post = Post(hashtags="развлечения, игры", text="играем в видеоигру")
            post6: Post = Post(hashtags="развлечения, еда", text="обедаю в кафе")
            db.session.add_all([post1, post2, post3, post4, post5, post6, user1, user2, user3, user4, user5, user6])
            post1.author = user6
            post2.author = user6
            post3.author = user6
            post4.author = user6
            post5.author = user6

            post1.liked_users.add_all([user2, user4, user5])
            post2.liked_users.add_all([user1, user2, user4])
            post3.liked_users.add_all([user1, user3, user5])
            post4.liked_users.add_all([user2, user4])
            post5.liked_users.add_all([user4, user5])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_recommended_posts(1, 3)
            self.assertEqual(len(result["items"]), 3)
            self.assertEqual(result["items"][0]["text"], "тестирование публикации")


if __name__ == '__main__':
    main(verbosity=2)
