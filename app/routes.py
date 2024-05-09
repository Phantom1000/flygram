from app import app, db
from flask import jsonify, make_response, g
from datetime import datetime, timezone


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Ivan'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    # return 'Не удалось загрузить посты', 500
    return jsonify(user=user, posts=posts)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(error='Страница не найдена'), 404)

