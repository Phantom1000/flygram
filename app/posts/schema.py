from marshmallow import Schema, fields, validate


class PostSchema(Schema):
    text = fields.Str(required=True, validate=[validate.Length(
        min=3, max=500, error="Длина текста не может быть меньше 3 или больше 500 символов")],
                      error_messages={"required": "Введите текст новости",
                                      "null": "Введите текст новости", "invalid": "Проверьте текст новости"})
    hashtags = fields.Str(required=True, validate=[validate.Length(
        min=3, max=100, error="Длина хэштегов не может быть меньше 3 или больше 100 символов")],
                          error_messages={"required": "Введите хэштеги",
                                          "null": "Введите хэштеги", "invalid": "Проверьте хэштеги"})
    user_id = fields.Integer(error_messages={"invalid": "Проверьте автора"})
    community_id = fields.Integer(error_messages={"invalid": "Проверьте сообщество"})
