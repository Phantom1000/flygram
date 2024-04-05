from app import app
from flask import jsonify, request


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
    errors = []
    username = request.form['username']
    password = request.form['password']
    if username is None or username == '':
        errors.append('Введите имя пользователя')
    if len(username) > 32:
        errors.append('Слишком длинное имя пользователя')
    if password is None or password == '':
        errors.append('Введите пароль')
    if len(password) > 32:
        errors.append('Слишком длинный пароль')
    if len(errors) > 0:
        return jsonify(errors=errors)
    else:
        if username == 'test' and password == '123':
            return jsonify(message='Вы успешно вошли')
        else:
            return jsonify(message='Проверьте имя пользователя и пароль'), 403
