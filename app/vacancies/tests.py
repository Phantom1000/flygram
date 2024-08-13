from unittest import TestCase, main
from app.models import User, Vacancy
from app.vacancies.repository import VacancyRepository
from app.users.repository import UserRepository
from app.vacancies.service import VacancyService
from app import create_app, db
from flask import g

from config import TestConfig


class MyTestCase(TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.service = VacancyService(VacancyRepository(), UserRepository())
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_vacancies(self):
        with self.app.app_context(), self.app.test_request_context():
            user1: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            vacancy1: Vacancy = Vacancy(description="В компанию требуется программист")
            vacancy1.employer = user1
            user2: User = User(username="petr", email="petr@example.com", firstname="Петр", lastname="Иванов")
            vacancy2: Vacancy = Vacancy(description="В компанию требуется тестировщик")
            vacancy2.employer = user2
            db.session.add_all([user1, user2, vacancy1, vacancy2])
            db.session.commit()
            g.current_user = user1
            result: dict = self.service.get_vacancies("ivan", {}, 1, 3, False)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["description"], "В компанию требуется программист")
            result: dict = self.service.get_vacancies("petr", {}, 1, 3, False)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["description"], "В компанию требуется тестировщик")
            result: dict = self.service.get_vacancies(None, {"description": "тест"}, 1, 3, False)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["description"], "В компанию требуется тестировщик")
            result: dict = self.service.get_vacancies(None, {}, 1, 3, False)
            self.assertEqual(len(result["items"]), 2)

    def test_add_vacancy(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            db.session.add(user)
            db.session.commit()
            g.current_user = user
            result: dict = self.service.add_vacancy(
                {"description": "Ищем продавца", "user_id": user.id}
            )
            vacancy: Vacancy = db.session.get(Vacancy, result["id"])
            self.assertEqual(vacancy.description,  "Ищем продавца")
            self.assertEqual(vacancy.employer, user)

    def test_update_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            vacancy: Vacancy = Vacancy(description="Ищем продавца")
            vacancy.employer = user
            db.session.add_all([user, vacancy])
            db.session.commit()
            g.current_user = user
            result: dict = self.service.update_vacancy(vacancy.id, {"description": "Требуется работник склада"})
            vacancy: Vacancy = db.session.get(Vacancy, result["id"])
            self.assertEqual(vacancy.description, "Требуется работник склада")

    def test_delete_community(self):
        with self.app.app_context(), self.app.test_request_context():
            user: User = User(username="ivan", email="ivan@example.com", firstname="Иван", lastname="Петров")
            vacancy: Vacancy = Vacancy(description="Ищем продавца")
            vacancy.employer = user
            db.session.add_all([user, vacancy])
            db.session.commit()
            g.current_user = user
            self.service.delete_vacancy(vacancy.id)
            result: Vacancy | None = db.session.get(Vacancy, 1)
            self.assertEqual(result, None)


if __name__ == '__main__':
    main(verbosity=2)
