from abc import ABC, abstractmethod

import sqlalchemy as sa

from app import db
from app.models import Vacancy
from app.utils import paginate


class VacancyRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, vacancy_id: int) -> Vacancy:
        pass

    @abstractmethod
    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[Vacancy]] = sa.select(Vacancy)
    ) -> dict:
        pass

    @abstractmethod
    def add(self, data: dict) -> Vacancy:
        pass

    @abstractmethod
    def update_model_from_dict(self, model: Vacancy, data: dict):
        pass

    @abstractmethod
    def delete(self, vacancy: Vacancy) -> None:
        pass

    @abstractmethod
    def model_to_dict(self, model: Vacancy) -> dict:
        pass

    @abstractmethod
    def get_vacancies(self) -> list[Vacancy]:
        pass


class VacancyRepository(VacancyRepositoryInterface):
    def get_by_id(self, community_id: int) -> Vacancy:
        return db.get_or_404(Vacancy, community_id)

    def get_vacancies(self) -> list[Vacancy]:
        query = sa.select(Vacancy)
        return db.session.scalars(query).all()

    def add(self, data: dict) -> Vacancy:
        vacancy: Vacancy = Vacancy(**data)
        db.session.add(vacancy)
        db.session.commit()
        return vacancy

    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[Vacancy]] = sa.select(Vacancy)
    ) -> dict:
        return paginate(query, Vacancy, self, filters, page, per_page, 'vacancies', Vacancy.date)

    def delete(self, vacancy: Vacancy) -> None:
        db.session.delete(vacancy)
        db.session.commit()

    def update_model_from_dict(self, model: Vacancy, data: dict):
        for field in ['skills', 'description']:
            if field in data:
                setattr(model, field, data[field])
        db.session.commit()

    def model_to_dict(self, model: Vacancy) -> dict:
        data = {
            'id': model.id,
            'skills': model.skills,
            'description': model.description,
            'date': str(model.date or ''),
            'employer': model.employer.username,
        }
        return data
