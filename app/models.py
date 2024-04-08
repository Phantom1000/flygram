class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def login_validate(self):
        errors = {
            'username': [],
            'password': [],
        }
        if self.username is None or self.username == '':
            errors['username'].append('Введите имя пользователя')
        elif len(self.username) < 3:
            errors['username'].append('Слишком короткое имя пользователя')
        elif len(self.username) > 32:
            errors['username'].append('Слишком длинное имя пользователя')
        if self.password is None or self.password == '':
            errors['password'].append('Введите пароль')
        elif len(self.password) < 3:
            errors['password'].append('Слишком короткий пароль')
        elif len(self.password) > 32:
            errors['password'].append('Слишком длинный пароль')
        if len(errors['username']) > 0 or len(errors['password']) > 0:
            return False, errors
        return True, errors
