from flask_restful import Api
from flask import jsonify, make_response
from app.resources.users import TokenAPI, UserAPI, UsersAPI, FriendsAPI
from app.resources.posts import PostAPI, PostsAPI, LikesAPI


class FlyApi(Api):

    def handle_error(self, e):
        responses = {
            400: 'При запросе произошла ошибка',
            404: 'Страница не найдена',
            401: 'У Вас нет прав для доступа к этому ресурсу',
            403: e.description,
            422: e.description,
            405: 'Метод запроса не поддерживается',
            415: 'Запрос не поддерживается',
        }
        for code, response in responses.items():
            if code == e.code:
                return make_response(jsonify(error=response), code)

    def initialize_routes(self):
        self.add_resource(TokenAPI, '/token', endpoint='token')
        self.add_resource(UserAPI, '/user/<string:username>', endpoint='user')
        self.add_resource(UsersAPI, '/users', endpoint='users')
        self.add_resource(FriendsAPI, '/friends/<string:username>', endpoint='friends')
        self.add_resource(PostsAPI, '/posts', endpoint='posts')
        self.add_resource(PostAPI, '/post/<int:post_id>', endpoint='post')
        self.add_resource(LikesAPI, '/like/<int:post_id>', endpoint='like')
