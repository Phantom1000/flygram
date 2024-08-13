from flask import request, abort, g
from flask.views import MethodView
from marshmallow import ValidationError

from app import cache
from app.auth import token_auth
from app.vacancies.schema import VacancySchema
from app.vacancies.service import VacancyServiceInterface


class VacanciesAPI(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: VacancyServiceInterface

    def __init__(self, service: VacancyServiceInterface):
        self.service = service

    @cache.cached(timeout=120)
    def get(self):
        """Получение списка вакансий"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 4, type=int), 100)
        username = request.args.get('username')
        description = request.args.get('description')
        recommended = request.args.get('type') == 'recommended'
        return self.service.get_vacancies(username, {"description": description}, page, per_page, recommended)

    def post(self):
        """Создание новой вакансии"""
        if not request.json:
            abort(400)
        data = dict(request.json)
        if not request.json.get('user_id'):
            data['user_id'] = g.current_user.id
        try:
            data = VacancySchema().load(data)
            response: dict = self.service.add_vacancy(data)
            return {'message': 'Вакансия успешно опубликована', 'community': response}
        except ValidationError as err:
            abort(422, err.messages)


class VacancyApi(MethodView):
    init_every_request = False
    decorators = [token_auth.login_required]

    service: VacancyServiceInterface

    def __init__(self, service: VacancyServiceInterface):
        self.service = service

    def get(self, vacancy_id):
        """Получение отдельной вакансии по идентификатору"""
        return self.service.get_vacancy(vacancy_id)

    def put(self, vacancy_id):
        """Редактирование вакансии"""
        if not request.json:
            abort(400)
        data = dict(request.json)
        try:
            data = VacancySchema().load(data)
            response: dict = self.service.update_vacancy(vacancy_id, data)
            return {'message': 'Изменения сохранены', 'vacancy': response}
        except ValidationError as err:
            abort(422, err.messages)

    def delete(self, vacancy_id):
        """Удаление вакансии"""
        self.service.delete_vacancy(vacancy_id)
        return {'message': 'Вакансия успешно удалена'}
