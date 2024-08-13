import os
from unittest import TestCase, main

from flask import g

from app import create_app, db
from app.models import Post, User, Comment
from app.posts.repository import PostRepository
from app.users.repository import UserRepository
from app.comments.repository import CommentRepository
from app.comments.service import CommentService
from config import TestConfig


class CommentModelCase(TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.service = CommentService(CommentRepository(), PostRepository(), UserRepository())
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_comments(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Петров")
            post1: Post = Post(hashtags="новости", text="тестирование публикации")
            post1.author = user1
            comment1: Comment = Comment(text="Тестовый комментарий")
            comment2: Comment = Comment(text="Ответ на комментарий")
            comment1.post = post1
            comment1.author = user2
            comment2.post = post1
            comment2.author = user1
            db.session.add_all([post1, user1, user2, comment1, comment2])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_comments(1, 1, 3)
            self.assertEqual(len(result["items"]), 2)
            self.assertEqual(result["items"][1]["text"], "Тестовый комментарий")
            self.assertEqual(result["items"][1]["author"], "petr")

    def test_add_comment(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            db.session.add_all([user, post])
            db.session.commit()
            g.current_user = user
            result: dict = self.service.add_comment(
                {"text": "комментарий новостей", "user_id": user.id, "post_id": post.id}
            )
            self.assertEqual(result["text"], "комментарий новостей")

    def test_update_post(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            comment: Comment = Comment(text="Тестовый комментарий")
            comment.author = user
            comment.post = post
            db.session.add_all([post, user, comment])
            db.session.commit()
            g.current_user = user
            result: dict = self.service.update_comment(comment.id, {"text": "обновленный комментарий"})
            self.assertEqual(result["text"], "обновленный комментарий")

    def test_delete_comment(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            post: Post = Post(hashtags="новости", text="тестирование публикации")
            post.author = user
            comment: Comment = Comment(text="Тестовый комментарий")
            comment.author = user
            comment.post = post
            db.session.add_all([post, user, comment])
            db.session.commit()
            g.current_user = user
            self.service.delete_comment(comment.id)
            result: Comment | None = db.session.get(Comment, 1)
            self.assertEqual(result, None)


if __name__ == '__main__':
    main(verbosity=2)
