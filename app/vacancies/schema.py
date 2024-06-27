from marshmallow import Schema, fields, validate


class VacancySchema(Schema):
    description = fields.Str(required=True, validate=[validate.Length(
        min=1, max=500, error="Длина описания не может быть меньше 1 или больше 500 символов")],
                      error_messages={"required": "Введите описание вакансии",
                                      "null": "Введите описание вакансии", "invalid": "Проверьте описание вакансии"})
    skills = fields.Str(allow_none=True,
                        validate=validate.Length(max=100,
                                                 error="Информация о навыках не может содержать больше 500 "
                                                       "символов")
                        )
    user_id = fields.Integer(error_messages={"invalid": "Проверьте работодателя"})
