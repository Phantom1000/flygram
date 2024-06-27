import os
from unittest import TestCase, main

import jwt

from app import app, db
from app.auth.repository import SessionRepository
from app.auth.service import AuthService
from app.auth.utils import generate_token
from app.models import Session, User
from app.users.repository import UserRepository
from app.users.utils import set_password

os.environ['DATABASE_URI'] = 'sqlite://'


class AuthModelCase(TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.service = AuthService(UserRepository(), SessionRepository())
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_generate_token(self):
        exp = 60
        user: User = User(username="test", email="test@example.com", firstname="Иван", lastname="Петров")
        set_password(user, "123123123")
        db.session.add(user)
        db.session.commit()
        token: str = generate_token(user.id, exp)
        payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
        self.assertEqual(payload['id'], 1)

    def test_login(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="test", email="test@example.com", firstname="Иван", lastname="Петров")
            set_password(user, "123123123")
            db.session.add(user)
            db.session.commit()
            data: dict = self.service.login("test", "123123123", False, 'test_platform', '1.1.1.2')
            self.assertEqual(data['message'], 'Вы успешно вошли')
            self.assertEqual(data['user']['username'], 'test')
            self.assertEqual(data['user']['firstname'], 'Иван')
            self.assertEqual(data['user']['lastname'], 'Петров')
            self.assertEqual(data['user']['email'], 'test@example.com')
            self.assertEqual(data['access_token'], generate_token(user.id, app.config.get('TOKEN_LIFETIME')))
            session: Session = db.session.scalar(user.sessions.select())
            self.assertEqual(session, None)
            self.assertEqual(data['refresh_token'], None)
            data: dict = self.service.login("test", "123123123", True, 'test_agent', '1.1.1.1')
            self.assertEqual(data['message'], 'Вы успешно вошли и система Вас запомнила')
            self.assertEqual(data['user']['username'], 'test')
            self.assertEqual(data['user']['firstname'], 'Иван')
            self.assertEqual(data['user']['lastname'], 'Петров')
            self.assertEqual(data['user']['email'], 'test@example.com')
            self.assertEqual(data['access_token'], generate_token(user.id, app.config.get('TOKEN_LIFETIME')))
            session: Session = db.session.scalar(user.sessions.select())
            self.assertEqual(session.platform, 'test_agent')
            self.assertEqual(session.ip, '1.1.1.1')
            self.assertEqual(data['refresh_token'], str(session.id))

    def test_refresh(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="test", email="test@example.com", firstname="Иван", lastname="Петров")
            set_password(user, "123123123")
            db.session.add(user)
            db.session.commit()
            token: str = self.service.login("test", "123123123", True, 'test_agent', '1.1.1.1')['refresh_token']
            data: dict = self.service.refresh(token)
            self.assertEqual(data['user']['username'], 'test')
            self.assertEqual(data['user']['firstname'], 'Иван')
            self.assertEqual(data['user']['lastname'], 'Петров')
            self.assertEqual(data['user']['email'], 'test@example.com')
            self.assertEqual(data['token'], generate_token(user.id, app.config.get('TOKEN_LIFETIME')))

    def test_logout(self):
        with app.app_context(), app.test_request_context():
            user: User = User(username="test", email="test@example.com", firstname="Иван", lastname="Петров")
            set_password(user, "123123123")
            db.session.add(user)
            db.session.commit()
            token: str = self.service.login("test", "123123123", True, 'test_agent', '1.1.1.1')['refresh_token']
            data: dict = self.service.logout(token)
            self.assertEqual(data['message'], 'Вы успешно вышли из аккаунта')
            session: Session = db.session.scalar(user.sessions.select())
            self.assertEqual(session, None)


if __name__ == '__main__':
    main(verbosity=2)
