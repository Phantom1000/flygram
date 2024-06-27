from marshmallow import Schema, fields, validate


class CommunitySchema(Schema):
    name = fields.Str(
        required=True, validate=[validate.Length(
            min=3, max=32, error="Длина названия сообщества должна быть больше 3 и меньше 32 символов")],
        error_messages={"required": "Введите название сообщества",
                        "null": "Введите название сообщества", "invalid": "Проверьте название сообщества"}
    )
    description = fields.Str(required=True, validate=[validate.Length(
        min=1, max=500, error="Длина описания не может быть меньше 1 или больше 500 символов")],
                      error_messages={"required": "Введите описание сообщества",
                                      "null": "Введите описание сообщества", "invalid": "Проверьте описание сообщества"})
    user_id = fields.Integer(error_messages={"invalid": "Проверьте владельца"})
