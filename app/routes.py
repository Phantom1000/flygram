from app import app
from flask import jsonify, request

from app.models import User


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


@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    remember_me = request.json['rememberMe']
    user = User(username, password)
    validate, errors = user.login_validate()
    if validate:
        if username == 'test' and password == '123':
            return jsonify(message=f'Вы успешно вошли {"и система Вас запомнила!" if remember_me else ""}')
        else:
            return jsonify(errors=['Проверьте имя пользователя и пароль']), 403
    else:
        return jsonify(errors=errors), 422

