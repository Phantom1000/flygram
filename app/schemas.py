from marshmallow import Schema, fields, validate, ValidationError
from datetime import date

from marshmallow.validate import Validator


def validate_after_now(check_date):
    if check_date > date.today():
        raise ValidationError("Дата рождения не может быть больше текущей")


class NotSpaces(Validator):
    message = "Поле не должно содержать пробелы"

    def __init__(self, message):
        self.message = message

    def __call__(self, string):
        if " " in string:
            raise ValidationError(self.message)


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


class UserSchema(Schema):
    username = fields.Str(
        required=True, validate=[validate.Length(
            min=3, max=32, error="Длина имени пользователя должна быть больше 3 и меньше 32 символов"),
            NotSpaces(message="Имя пользователя не должно содержать пробелы")],
        error_messages={"required": "Введите имя пользователя",
                        "null": "Введите имя пользователя", "invalid": "Проверьте имя пользователя"}
    )
    password = fields.Str(required=True, validate=[validate.Length(
        min=8, max=32, error="Длина пароля должна быть больше 8 и меньше 32 символов"),
        NotSpaces(message="Пароль не должен содержать пробелы")],
                          error_messages={"required": "Введите пароль", "null": "Введите пароль",
                                          "invalid": "Проверьте пароль"}, load_only=True
                          )
    email = fields.Email(
        required=True, validate=validate.Length(
            min=5, max=100, error="Длина email должна быть больше 5 и меньше 100 символов"),
        error_messages={"required": "Введите имя email", "null": "Введите email", "invalid": "Проверьте email"}
    )
    firstname = fields.Str(
        required=True, validate=validate.Length(
            min=2, max=32, error="Длина имени должна быть больше 2 и меньше 32 символов"),
        error_messages={"required": "Введите Ваше имя",
                        "null": "Введите Ваше имя", "invalid": "Проверьте имя"}
    )
    lastname = fields.Str(
        required=True, validate=validate.Length(
            min=2, max=32, error="Длина фамилии должна быть больше 2 и меньше 32 символов"),
        error_messages={"required": "Введите Вашу фамилию",
                        "null": "Введите Вашу фамилию", "invalid": "Проверьте фамилию"}
    )
    phone_number = fields.Str(allow_none=True,
                              validate=validate.Regexp(
                                  regex=r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?['
                                        r'0-9]{2}$', error="Проверьте номер телефона")
                              )
    date_birth = fields.Date(allow_none=True, validate=validate_after_now,
                             error_messages={"invalid": "Проверьте дату рождения"})
    city = fields.Str(allow_none=True,
                      validate=validate.Length(max=100, error="Длина названия города не может быть больше 100 символов")
                      )
    address = fields.Str(allow_none=True,
                         validate=validate.Length(max=100, error="Длина адреса не может быть больше 100 символов")
                         )
    education = fields.Str(allow_none=True,
                           validate=validate.Length(max=100,
                                                    error="Информация об образовании не может содержать больше 100 "
                                                          "символов")
                           )
    career = fields.Str(allow_none=True,
                        validate=validate.Length(max=100,
                                                 error="Информация о карьере не может содержать больше 100 символов")
                        )
    hobbies = fields.Str(allow_none=True,
                         validate=validate.Length(max=500,
                                                  error="Информация об увлечениях не может содержать больше 500 "
                                                        "символов")
                         )


class UserUpdateSchema(UserSchema):
    username = fields.Str(
        required=False, validate=[validate.Length(
            min=3, max=32, error="Длина имени пользователя должна быть больше 3 и меньше 32 символов"),
            NotSpaces(message="Имя пользователя не должно содержать пробелы")],
        error_messages={"required": "Введите имя пользователя",
                        "null": "Введите имя пользователя", "invalid": "Проверьте имя пользователя"}
    )
    email = fields.Email(
        required=False, validate=validate.Length(
            min=5, max=100, error="Длина email должна быть больше 5 и меньше 100 символов"),
        error_messages={"required": "Введите имя email", "null": "Введите email", "invalid": "Проверьте email"}
    )
    firstname = fields.Str(
        required=False, validate=validate.Length(
            min=2, max=32, error="Длина имени должна быть больше 2 и меньше 32 символов"),
        error_messages={"required": "Введите Ваше имя",
                        "null": "Введите Ваше имя", "invalid": "Проверьте имя"}
    )
    lastname = fields.Str(
        required=False, validate=validate.Length(
            min=2, max=32, error="Длина фамилии должна быть больше 2 и меньше 32 символов"),
        error_messages={"required": "Введите Вашу фамилию",
                        "null": "Введите Вашу фамилию", "invalid": "Проверьте фамилию"}
    )


class PostSchema(Schema):
    text = fields.Str(required=True, validate=[validate.Length(
        min=3, max=500, error="Длина текста не может быть меньше 3 или больше 500 символов")],
                      error_messages={"required": "Введите текст новости",
                                      "null": "Введите текст новости", "invalid": "Проверьте текст новости"})
    hashtags = fields.Str(required=True, validate=[validate.Length(
        min=3, max=100, error="Длина хэштегов не может быть меньше 3 или больше 100 символов")],
                          error_messages={"required": "Введите хэштеги",
                                          "null": "Введите хэштеги", "invalid": "Проверьте хэштеги"})
    by_user = fields.Bool(load_default=True, error_messages={"invalid": "Некорректное значение"}),
    user_id = fields.Integer(error_messages={"invalid": "Проверьте автора"})
