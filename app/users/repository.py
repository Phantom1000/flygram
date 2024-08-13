from abc import ABC, abstractmethod
import sqlalchemy as sa
from flask import g, url_for
from app.models import User, friends
from app.utils import paginate
from app import db
from datetime import datetime, timezone
from app.users.utils import set_password
import sqlalchemy.orm as so


class UserRepositoryInterface(ABC):
    @abstractmethod
    def add(self, data: dict, password: str) -> User:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    def get_users(self) -> list[User]:
        pass

    @abstractmethod
    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[User]] = sa.select(User),
            endpoint='users', **kwargs) -> dict:
        pass

    @abstractmethod
    def get_by_username(self, username: str, error: bool = True) -> User | None:
        pass

    @abstractmethod
    def delete_by_username(self, username: str) -> None:
        pass

    @abstractmethod
    def get_by_email(self, email: str, error: bool = True) -> User | None:
        pass

    @abstractmethod
    def get_by_username_or_email(self, username: str, email: str, error: bool = True) -> User | None:
        pass

    @abstractmethod
    def update_last_seen(self, user: User) -> None:
        pass

    @abstractmethod
    def get_followers_without_friends(self, user: User) -> sa.Select[tuple[User]]:
        pass

    @abstractmethod
    def get_following_without_friends(self, user: User) -> sa.Select[tuple[User]]:
        pass

    @abstractmethod
    def get_friends(self, user: User) -> sa.Select[tuple[User]]:
        pass

    @abstractmethod
    def get_following_count(self, user: User) -> int:
        pass

    @abstractmethod
    def get_followers_count(self, user: User) -> int:
        pass

    @abstractmethod
    def get_friends_count(self, user: User) -> int:
        pass

    @abstractmethod
    def is_following(self, user: User, following: User) -> bool:
        pass

    @abstractmethod
    def is_friend(self, user: User, friend: User) -> bool:
        pass

    @abstractmethod
    def follow(self, user: User, following: User) -> None:
        pass

    @abstractmethod
    def unfollow(self, user: User, following: User) -> None:
        pass

    @abstractmethod
    def model_to_dict(self, model: User) -> dict:
        pass

    @abstractmethod
    def update_model_from_dict(self, model: User, data: dict) -> None:
        pass

    @abstractmethod
    def update_avatar_url(self, user: User, avatar_url: str) -> None:
        pass

    @abstractmethod
    def verify_email(self, user: User) -> None:
        pass

    @abstractmethod
    def enable_two_factor(self, user: User) -> None:
        pass

    @abstractmethod
    def disable_two_factor(self, user: User) -> None:
        pass


class UserRepository(UserRepositoryInterface):
    def get_users(self) -> list[User]:
        query = sa.select(User)
        return db.session.scalars(query).all()

    def get_by_id(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)

    def add(self, data: dict, password: str) -> User:
        user: User = User(**data)
        set_password(user, password)
        db.session.add(user)
        db.session.commit()
        return user

    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[User]] = sa.select(User),
            endpoint='users', **kwargs) -> dict:
        return paginate(query, User, self, filters, page, per_page, endpoint, None, **kwargs)

    def get_followers_without_friends(self, user: User) -> sa.Select[tuple[User]]:
        followers = so.aliased(friends)
        following = so.aliased(friends)
        query = sa.select(User).join(
            following, sa.and_(following.c.user_id == User.id, following.c.friend_id == user.id)).join(
            followers, sa.and_(followers.c.friend_id == User.id, followers.c.user_id == user.id), isouter=True).where(
            followers.c.user_id == None)
        return query

    def get_following_without_friends(self, user: User) -> sa.Select[tuple[User]]:
        followers = so.aliased(friends)
        following = so.aliased(friends)
        query = sa.select(User).join(
            following, sa.and_(following.c.user_id == User.id, following.c.friend_id == user.id), isouter=True).join(
            followers, sa.and_(followers.c.friend_id == User.id, followers.c.user_id == user.id)).where(
            following.c.user_id == None)
        return query

    def get_followers_count(self, user: User) -> int:
        query = sa.select(sa.func.count()).select_from(
            self.get_followers_without_friends(user).subquery())
        return db.session.scalar(query)

    def get_following_count(self, user: User) -> int:
        query = sa.select(sa.func.count()).select_from(
            self.get_following_without_friends(user).subquery())
        return db.session.scalar(query)

    def get_friends(self, user: User) -> sa.Select[tuple[User]]:
        follower = so.aliased(User)
        following = so.aliased(User)
        query = (sa.select(User).join(User.following.of_type(following)).join(User.followers.of_type(follower)).where(
            sa.and_(user.id == follower.id, user.id == following.id)))
        return query

    def get_friends_count(self, user: User) -> int:
        query = sa.select(sa.func.count()).select_from(self.get_friends(user).subquery())
        return db.session.scalar(query)

    def is_following(self, user: User, following: User) -> bool:
        query = user.following.select().where(User.id == following.id)
        return db.session.scalar(query) is not None

    def is_friend(self, user: User, friend: User) -> bool:
        return self.is_following(user, friend) and self.is_following(friend, user)

    def follow(self, user: User, following: User) -> None:
        if not self.is_following(user, following):
            user.following.add(following)
            db.session.commit()

    def unfollow(self, user: User, following: User) -> None:
        if self.is_following(user, following):
            user.following.remove(following)
            db.session.commit()

    def get_by_username_or_email(self, username: str, email: str, error: bool = True) -> User | None:
        query = sa.select(User).where(sa.or_(
            User.username == username, User.email == email)).limit(1)
        if error:
            user = db.first_or_404(query)
        else:
            user = db.session.scalar(query)
        return user

    def get_by_username(self, username: str, error: bool = True) -> User | None:
        query = sa.select(User).where(User.username == username).limit(1)
        if error:
            user = db.first_or_404(query)
        else:
            user = db.session.scalar(query)
        return user

    def delete_by_username(self, username: str) -> None:
        user: User = self.get_by_username(username)
        db.session.delete(user)
        db.session.commit()

    def get_by_email(self, email: str, error: bool = True) -> User | None:
        query = sa.select(User).where(User.email == email).limit(1)
        if error:
            user = db.first_or_404(query)
        else:
            user = db.session.scalar(query)
        return user

    def update_last_seen(self, user: User) -> None:
        user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

    def update_avatar_url(self, user: User, avatar_url: str) -> None:
        user.avatar_url = avatar_url
        db.session.commit()

    def model_to_dict(self, model: User) -> dict:
        data: dict = {
            'username': model.username,
            'firstname': model.firstname,
            'lastname': model.lastname,
            'email': model.email,
            'phone_number': model.phone_number,
            'date_birth': str(model.date_birth or ''),
            'city': model.city,
            'address': model.address,
            'education': model.education,
            'career': model.career,
            'skills': model.skills,
            'hobbies': model.hobbies,
            'register_date': str(model.register_date or ''),
            'is_follower': self.is_following(g.current_user, model),
            'is_following': self.is_following(model, g.current_user),
            'is_friend': self.is_friend(g.current_user, model),
            'following_count': str(self.get_following_count(model)),
            'followers_count': str(self.get_followers_count(model)),
            'friends_count': str(self.get_friends_count(model)),
            'verified_email': model.verified_email,
            'two_factor_enabled': model.two_factor_enabled,
            'links': {
                'self': url_for('user', username=model.username),
                'avatar': model.avatar_url
            }
        }
        return data

    def update_model_from_dict(self, model: User, data: dict) -> None:
        for field in ['username', 'email', 'firstname', 'lastname', 'phone_number', 'date_birth', 'city',
                      'address', 'education', 'career', 'skills', 'hobbies', 'two_factor_code']:
            if field in data:
                setattr(model, field, data[field])
        db.session.commit()

    def verify_email(self, user: User) -> None:
        user.verified_email = True
        db.session.commit()

    def enable_two_factor(self, user: User) -> None:
        user.two_factor_enabled = True
        db.session.commit()

    def disable_two_factor(self, user: User) -> None:
        user.two_factor_enabled = False
        db.session.commit()
