from marshmallow import Schema, fields, validate


class CommentSchema(Schema):
    text = fields.Str(required=True, validate=[validate.Length(
        min=3, max=500, error="Длина комментария не может быть меньше 3 или больше 500 символов")],
                      error_messages={"required": "Введите текст комментария",
                                      "null": "Введите текст комментария", "invalid": "Проверьте текст комментария"})
    user_id = fields.Integer(error_messages={"invalid": "Проверьте автора"})
    post_id = fields.Integer(error_messages={"invalid": "Проверьте публикацию"})
