from flask_restful import Api
from flask import jsonify, make_response
from app.auth.router import TokenAPI
from app.users.router import UsersAPI, UserAPI, FriendsAPI
from app.posts.router import PostAPI, PostsAPI, LikesAPI
from app.comments.router import CommentsAPI, CommentAPI
from app.communities.router import CommunitiesAPI, CommunityAPI, MembersAPI
from app.messages.router import MessagesAPI
from app.vacancies.router import VacanciesAPI, VacancyApi


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
            500: 'Произошла непредвиденная ошибка'
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
        self.add_resource(CommentsAPI, '/comments', endpoint='comments')
        self.add_resource(CommentAPI, '/comment/<int:comment_id>', endpoint='comment')
        self.add_resource(CommunitiesAPI, '/communities', endpoint='communities')
        self.add_resource(CommunityAPI, '/community/<int:community_id>', endpoint='community')
        self.add_resource(MembersAPI, '/members/<int:community_id>', endpoint='members')
        self.add_resource(MessagesAPI, '/messages', endpoint='messages')
        self.add_resource(VacanciesAPI, '/vacancies', endpoint='vacancies')
        self.add_resource(VacancyApi, '/vacancy/<int:vacancy_id>', endpoint='vacancy')
