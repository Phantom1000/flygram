import math

from flask import current_app as app, url_for, g
import sqlalchemy as sa
from flask_sqlalchemy.pagination import Pagination

from app import db
from app.models import User


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_similarity_vector() -> list[dict]:
    """Построение вектора сходства"""
    users: list[User] = db.session.scalars(sa.select(User)).all()
    similarity_vector = []
    liked_posts = db.session.scalars(g.current_user.liked_posts.select()).all()
    count_liked_posts = db.session.scalar(
        sa.select(sa.func.count()).select_from(g.current_user.liked_posts.select().subquery()))
    for user in users:
        if user != g.current_user:
            user_liked_posts = db.session.scalars(user.liked_posts.select()).all()
            count_user_liked_posts = db.session.scalar(
                sa.select(sa.func.count()).select_from(user.liked_posts.select().subquery()))
            count_posts = 0
            for post in user_liked_posts:
                if post in liked_posts:
                    count_posts += 1
            div = count_liked_posts + count_user_liked_posts - count_posts
            if div == 0:
                div = 1
            similarity_vector.append(
                {"user": user,
                 "similarity": count_posts / div})
    similarity_vector.sort(key=lambda el: el["similarity"], reverse=True)
    return similarity_vector[:20]


def paginate(query, entity: db.Model, repo, filters: dict, page: int, per_page: int, endpoint: str, order=None,
             **kwargs) -> dict:
    """Универсальный метод для разделения данных по страницам"""
    for field, value in filters.items():
        query = query.where(sa.func.lower(getattr(entity, field)).like(f'%{value.lower()}%'))
    if order:
        query = query.order_by(sa.desc(order))
    total_items: int = db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))
    resources: Pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return {
        'items': [repo.model_to_dict(item) for item in resources.items],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total_items / per_page),
            'total_items': total_items
        },
        'links': {
            'self': url_for(endpoint, page=page, per_page=per_page, **filters, **kwargs),
            'next': url_for(
                endpoint, page=resources.next_num, per_page=per_page, **filters,
                **kwargs) if resources.has_next else None,
            'prev': url_for(
                endpoint, page=resources.prev_num, per_page=per_page, **filters,
                **kwargs) if resources.has_prev else None
        }
    }
