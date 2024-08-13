from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from celery import Celery, Task
from config import get_config_class, BaseConfig
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
cache = Cache()
cors = CORS()
mail = Mail()


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.name, task_cls=FlaskTask)
    celery.config_from_object(app.config['CELERY'])
    celery.set_default()
    app.extensions['celery'] = celery
    return celery


def create_app(config_class: BaseConfig = get_config_class()) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.from_mapping(
        CELERY={
            "broker_url": app.config['REDIS_URL'],
            "result_backend": app.config['REDIS_URL'],
            "task_ignore_results": True,
            "broker_connection_retry_on_startup": True,
            "broker_transport_options": {
                'visibility_timeout': 3600,
                'fanout_prefix': True,
                'fanout_patterns': True,
                'max_connections': 1,
                'password': app.config['REDIS_PASSWORD']
            }
        }
    )
    config_class.init_app(app)
    cors.init_app(app, origins=[app.config['APP_URL']], supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins=app.config['APP_URL'])
    cache.init_app(app)
    mail.init_app(app)
    app.config.from_prefixed_env()
    celery_init_app(app)
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    prefix = "/api"

    from app.auth.view import TokenAPI, PasswordAPI, SessionsAPI, SessionAPI, EmailAPI, TwoFactorAPI
    from app.comments.view import CommentsAPI, CommentAPI
    from app.communities.view import CommunitiesAPI, CommunityAPI, MembersAPI
    from app.users.view import UsersAPI, UserAPI, FriendsAPI
    from app.vacancies.view import VacancyApi, VacanciesAPI
    from app.messages.view import MessagesAPI
    from app.posts.view import PostAPI, PostsAPI, LikesAPI

    from app.auth.service import AuthService
    from app.comments.repository import CommentRepository
    from app.comments.service import CommentService
    from app.communities.service import CommunityService
    from app.messages.repository import MessageRepository
    from app.messages.service import MessageService
    from app.users.repository import UserRepository
    from app.posts.repository import PostRepository
    from app.communities.repository import CommunityRepository
    from app.posts.service import PostService
    from app.users.service import UserService
    from app.vacancies.repository import VacancyRepository
    from app.vacancies.service import VacancyService
    from app.auth.repository import SessionRepository

    message_repo = MessageRepository()
    user_repo = UserRepository()
    post_repo = PostRepository()
    community_repo = CommunityRepository()
    comment_repo = CommentRepository()
    session_repo = SessionRepository()
    vacancy_repo = VacancyRepository()

    app.user_repo = user_repo

    message_service = MessageService(message_repo, user_repo)
    post_service = PostService(post_repo, user_repo, community_repo)
    user_service = UserService(user_repo)
    comment_service = CommentService(comment_repo, post_repo, user_repo)
    auth_service = AuthService(user_repo, session_repo)
    vacancy_servie = VacancyService(vacancy_repo, user_repo)
    community_service = CommunityService(community_repo, user_repo)

    app.add_url_rule(f"{prefix}/messages", view_func=MessagesAPI.as_view("messages", message_service))
    app.add_url_rule(f"{prefix}/posts", view_func=PostsAPI.as_view("posts", post_service))
    app.add_url_rule(f"{prefix}/posts/<int:post_id>", view_func=PostAPI.as_view("post", post_service))
    app.add_url_rule(f"{prefix}/likes/<int:post_id>", view_func=LikesAPI.as_view("like", post_service))

    app.add_url_rule(f"{prefix}/token", view_func=TokenAPI.as_view("token", auth_service))
    app.add_url_rule(f"{prefix}/password", view_func=PasswordAPI.as_view("password", auth_service))
    app.add_url_rule(f"{prefix}/users", view_func=UsersAPI.as_view("users", user_service))
    app.add_url_rule(f"{prefix}/users/<string:username>", view_func=UserAPI.as_view("user", user_service))
    app.add_url_rule(f"{prefix}/friends/<string:username>", view_func=FriendsAPI.as_view("friends", user_service))

    app.add_url_rule(f"{prefix}/comments", view_func=CommentsAPI.as_view("comments", comment_service))
    app.add_url_rule(f"{prefix}/comments/<int:comment_id>", view_func=CommentAPI.as_view("comment", comment_service))
    app.add_url_rule(f"{prefix}/communities", view_func=CommunitiesAPI.as_view("communities", community_service))
    app.add_url_rule(f"{prefix}/communities/<int:community_id>",
                     view_func=CommunityAPI.as_view("community", community_service))

    app.add_url_rule(f"{prefix}/vacancies", view_func=VacanciesAPI.as_view("vacancies", vacancy_servie))
    app.add_url_rule(f"{prefix}/vacancies/<int:vacancy_id>", view_func=VacancyApi.as_view("vacancy", vacancy_servie))
    app.add_url_rule(f"{prefix}/members/<int:community_id>", view_func=MembersAPI.as_view("members", community_service))
    app.add_url_rule(f"{prefix}/sessions", view_func=SessionsAPI.as_view("sessions", auth_service))
    app.add_url_rule(f"{prefix}/sessions/<session_id>", view_func=SessionAPI.as_view("session", auth_service))
    app.add_url_rule(f"{prefix}/email", view_func=EmailAPI.as_view("email", auth_service))
    app.add_url_rule(f"{prefix}/two-factor", view_func=TwoFactorAPI.as_view("two-factor", auth_service))

    return app
