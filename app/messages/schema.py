from marshmallow import Schema, fields, validate


class MessageSchema(Schema):
    body = fields.Str(required=True, validate=[validate.Length(
        min=3, max=200, error="Длина сообщения не может быть меньше 3 или больше 200 символов")],
                      error_messages={"required": "Введите сообщение",
                                      "null": "Введите сообщение", "invalid": "Проверьте сообщение"})
    recipient = fields.Str(required=True,
                           error_messages={"required": "Не указан получатель", "null": "Не указан получатель"})
