import math
from abc import ABC, abstractmethod

import sqlalchemy as sa
from flask import g, abort

from app.vacancies.repository import VacancyRepositoryInterface
from app.models import Vacancy, User
from app.users.repository import UserRepositoryInterface


class VacancyServiceInterface(ABC):
    vacancy_repository: VacancyRepositoryInterface
    user_repository: UserRepositoryInterface

    @abstractmethod
    def get_vacancy(self, vacancy_id: int) -> dict:
        pass

    @abstractmethod
    def get_vacancies(self, user_id: int | None, filters: dict, page: int, per_page: int, recommended: bool) -> dict:
        pass

    @abstractmethod
    def add_vacancy(self, data: dict) -> dict:
        pass

    @abstractmethod
    def update_vacancy(self, vacancy_id: int, data: dict) -> dict:
        pass

    @abstractmethod
    def delete_vacancy(self, vacancy_id: int) -> None:
        pass

    @abstractmethod
    def get_recommended_vacancies(self, page: int, per_page: int) -> dict:
        pass


SKILL_WEIGHT = 5


class VacancyService(VacancyServiceInterface):
    def __init__(self, vacancy_repository: VacancyRepositoryInterface, user_repository: UserRepositoryInterface):
        self.vacancy_repository = vacancy_repository
        self.user_repository = user_repository

    def get_vacancy(self, vacancy_id: int) -> dict:
        vacancy: Vacancy = self.vacancy_repository.get_by_id(vacancy_id)
        return self.vacancy_repository.model_to_dict(vacancy)

    def add_vacancy(self, data: dict) -> dict:
        employer_id = data.get('user_id')
        if not employer_id or self.user_repository.get_by_id(int(employer_id)) != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        vacancy: Vacancy = self.vacancy_repository.add(data)
        return self.vacancy_repository.model_to_dict(vacancy)

    def update_vacancy(self, vacancy_id: int, data: dict) -> dict:
        vacancy: Vacancy = self.vacancy_repository.get_by_id(vacancy_id)
        if vacancy.employer != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        for key, value in data.items():
            if type(value) is str:
                data[key] = value.strip()
        self.vacancy_repository.update_model_from_dict(vacancy, data)
        return self.vacancy_repository.model_to_dict(vacancy)

    def get_vacancies(self, username: str | None, filters: dict, page: int, per_page: int, recommended: bool) -> dict:
        query = sa.select(Vacancy)
        if username:
            user: User = self.user_repository.get_by_username(username)
            query = user.vacancies.select()
        if recommended and g.current_user.skills:
            return self.get_recommended_vacancies(page, per_page)
        return self.vacancy_repository.paginate_by_filters(
            {field: value for field, value in filters.items() if value}, page, per_page, query)

    def get_recommended_vacancies(self, page: int, per_page: int) -> dict:
        user_skills = g.current_user.skills.split(",")
        vacancies = [{"vacancy": vacancy, "weight": 0} for vacancy in self.vacancy_repository.get_vacancies()]
        for item in vacancies:
            if item["vacancy"].skills:
                skills = item["vacancy"].skills.split(",")
                for skill in skills:
                    if skill in user_skills:
                        item["weight"] += SKILL_WEIGHT
        vacancies.sort(key=lambda el: el["weight"], reverse=True)
        page -= 1
        total_items = len(vacancies)
        recommended_vacancies = [self.vacancy_repository.model_to_dict(item["vacancy"]) for item in vacancies][
                                page * per_page:(page + 1) * per_page]
        return {
            "items": recommended_vacancies,
            'meta': {
                'page': page + 1,
                'per_page': per_page,
                'total_pages': math.ceil(total_items / per_page),
                'total_items': total_items
            },
        }

    def delete_vacancy(self, vacancy_id: int) -> None:
        vacancy: Vacancy = self.vacancy_repository.get_by_id(vacancy_id)
        if vacancy.employer != g.current_user:
            abort(403, 'У Вас нет прав доступа')
        self.vacancy_repository.delete(vacancy)
