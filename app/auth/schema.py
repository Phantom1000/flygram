from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    username = fields.Str(
        required=True, validate=validate.Length(
            min=3, max=32, error="Длина имени должна быть больше 3 и меньше 32 символов"),
        error_messages={"required": "Введите имя пользователя",
                        "null": "Введите имя пользователя", "invalid": "Проверьте имя пользователя"}
    )
    password = fields.Str(required=True, validate=validate.Length(
        min=8, max=32, error="Длина пароля должна быть больше 8 и меньше 32 символов"),
                          error_messages={"required": "Введите пароль", "null": "Введите пароль",
                                          "invalid": "Проверьте пароль"}
                          )
    remember_me = fields.Bool(load_default=False, error_messages={"invalid": "Некорректное значение"})


class CodeSchema(Schema):
    code = fields.Integer(required=True, validate=validate.Range(
        min=100_000, max=999_999, error="Код должен содержать 6 цифр"),
                          error_messages={"required": "Введите код", "null": "Введите код",
                                          "invalid": "Проверьте код"}
                          )
    remember_me = fields.Bool(load_default=False, error_messages={"invalid": "Некорректное значение"})
