from flask import Blueprint, jsonify
from werkzeug.exceptions import HTTPException

from app import db


bp = Blueprint('errors', __name__)


def error_response(status_code, message=None):
    payload = {}
    if message:
        payload = {'error': message}
    return jsonify(payload), status_code


def bad_request(message):
    return error_response(400, message)


@bp.app_errorhandler(HTTPException)
def handle_exception(e):
    return error_response(e.code)


@bp.app_errorhandler(400)
def not_found_error(error):
    return error_response(400, 'При запросе произошла ошибка')


@bp.app_errorhandler(401)
def unauthorized_error(error):
    return error_response(401, 'У Вас нет прав для доступа к этому ресурсу')


@bp.app_errorhandler(403)
def forbidden_error(error):
    return error_response(403, error.description)


@bp.app_errorhandler(405)
def method_not_allowed_error(error):
    return error_response(405, 'Метод запроса не поддерживается')


@bp.app_errorhandler(415)
def unsupported_media_type_error(error):
    return error_response(415, 'Запрос не поддерживается')


@bp.app_errorhandler(422)
def validation_error(error):
    return error_response(422, error.description)


@bp.app_errorhandler(404)
def not_found_error(error):
    return error_response(404, 'Страница не найдена')


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return error_response(500, 'Произошла непредвиденная ошибка')
