import uuid
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from datetime import datetime, timezone
from flask import url_for, current_app as app, g
from werkzeug.security import generate_password_hash, check_password_hash
import math
import jwt
import time
import os
from werkzeug.utils import secure_filename
from hashlib import md5


class Base(so.DeclarativeBase):
    pass


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, total_items, page, per_page, endpoint, **kwargs):
        resources = db.session.scalars(query).all()
        data = {
            'items': [item.to_dict() for item in resources],
            'meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': math.ceil(total_items / per_page),
                'total_items': total_items
            },
            'links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if page * per_page < total_items else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if (page - 1) * per_page > 0 else None
            }
        }
        return data


friends = db.Table(
    "friends",
    db.Model.metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete='cascade'), primary_key=True),
    sa.Column("friend_id", sa.Integer, sa.ForeignKey("user.id", ondelete='cascade'), primary_key=True),
    sa.Column("add_date", sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc)),
)

likes = db.Table(
    "likes",
    db.Model.metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete='cascade'), primary_key=True),
    sa.Column("post_id", sa.Integer, sa.ForeignKey("post.id", ondelete='cascade'), primary_key=True),
    sa.Column("date", sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc)),
)


class User(db.Model, PaginatedAPIMixin):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(32), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(100), index=True, unique=True)
    firstname: so.Mapped[str] = so.mapped_column(sa.String(32))
    lastname: so.Mapped[str] = so.mapped_column(sa.String(32))
    phone_number: so.Mapped[Optional[str]] = so.mapped_column(sa.String(20))
    date_birth: so.Mapped[Optional[datetime]] = so.mapped_column(sa.Date)
    avatar_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    city: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    address: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    education: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    career: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    hobbies: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    register_date: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    last_seen: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author', passive_deletes=True)
    liked_posts: so.WriteOnlyMapped['Post'] = so.relationship(secondary=likes,
                                                              back_populates='liked_users', passive_deletes=True)
    following: so.WriteOnlyMapped['User'] = so.relationship(secondary=friends, primaryjoin=(id == friends.c.user_id),
                                                            secondaryjoin=(id == friends.c.friend_id),
                                                            back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(secondary=friends, primaryjoin=(id == friends.c.friend_id),
                                                            secondaryjoin=(id == friends.c.user_id),
                                                            back_populates='following')

    def followers_without_friends(self):
        # follower = so.aliased(User)
        # following = so.aliased(User)
        # query = (sa.select(User).join(User.following.of_type(following)).join(
        #     User.followers.of_type(follower), isouter=True).where(
        #     sa.and_(follower.id == None, following.id == self.id)))
        followers = so.aliased(friends)
        following = so.aliased(friends)
        query = sa.select(User).join(
            following, sa.and_(following.c.user_id == User.id, following.c.friend_id == self.id)).join(
            followers, sa.and_(followers.c.friend_id == User.id, followers.c.user_id == self.id), isouter=True).where(
            followers.c.user_id == None)
        return query

    def following_without_friends(self):
        # follower = so.aliased(User)
        # following = so.aliased(User)
        # query = (sa.select(User).join(User.following.of_type(following), isouter=True).join(
        #     User.followers.of_type(follower)).where(
        #     sa.and_(self.id == follower.id, following.id == None)))
        followers = so.aliased(friends)
        following = so.aliased(friends)
        query = sa.select(User).join(
            following, sa.and_(following.c.user_id == User.id, following.c.friend_id == self.id), isouter=True).join(
            followers, sa.and_(followers.c.friend_id == User.id, followers.c.user_id == self.id)).where(
            following.c.user_id == None)
        return query
        return query

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers_without_friends().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following_without_friends().subquery())
        return db.session.scalar(query)

    def friends(self):
        follower = so.aliased(User)
        following = so.aliased(User)
        query = (sa.select(User).join(User.following.of_type(following)).join(User.followers.of_type(follower)).where(
            sa.and_(self.id == follower.id, self.id == following.id)))
        return query

    def friends_count(self):
        query = sa.select(sa.func.count()).select_from(self.friends().subquery())
        return query

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def is_friend(self, user):
        return self.is_following(user) and user.is_following(self)

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def following_posts(self):
        author = so.aliased(User)
        followers = so.aliased(User)
        query = (sa.select(Post).join(Post.author.of_type(author)).join(User.followers.of_type(followers)).
                 where(followers.id == self.id))
        return query

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, expires):
        return jwt.encode(
            {"id": self.id, "expires": time.time() + expires}, app.config["SECRET_KEY"], algorithm="HS256")

    def upload_avatar(self, avatar):
        filename = secure_filename(avatar.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        # filename = f'{str(uuid.uuid4())}.{extension}'
        filename = f'{md5(self.username.encode('utf-8')).hexdigest()}.{extension}'
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.mkdir(app.config['UPLOAD_FOLDER'])
        avatar.save(avatar_path)
        self.avatar_url = f'/static/images/{filename}'

    def to_dict(self, current_user=None):
        data = {
            'username': self.username,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'phone_number': self.phone_number,
            'date_birth': str(self.date_birth or ''),
            'city': self.city,
            'address': self.address,
            'education': self.education,
            'career': self.career,
            'hobbies': self.hobbies,
            'register_date': str(self.register_date or ''),
            'is_follower': g.current_user.is_following(self),
            'is_following': self.is_following(g.current_user),
            'is_friend': g.current_user.is_friend(self),
            'following_count': str(self.following_count()),
            'followers_count': str(self.followers_count()),
            'friends_count': str(db.session.scalar(self.friends_count())),
            'links': {
                'self': url_for('user', username=self.username),
                'avatar': self.avatar_url
            }
        }
        return data

    def from_dict(self, data):
        for field in ['username', 'email', 'firstname', 'lastname', 'phone_number', 'date_birth', 'city',
                      'address', 'education', 'career', 'hobbies']:
            if field in data:
                setattr(self, field, data[field])


class Post(db.Model, PaginatedAPIMixin):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    text: so.Mapped[str] = so.mapped_column(sa.String(500))
    image_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    hashtags: so.Mapped[str] = so.mapped_column(sa.String(100))
    by_user: so.Mapped[bool] = so.mapped_column(default=True)
    publication_date: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    author: so.Mapped[User] = so.relationship(back_populates='posts')
    liked_users: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=likes, back_populates='liked_posts', passive_deletes=True)

    def is_liked(self, user):
        query = self.liked_users.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def likes_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.liked_users.select().subquery())
        return db.session.scalar(query)

    def like(self, user):
        if not self.is_liked(user):
            self.liked_users.add(user)

    def unlike(self, user):
        if self.is_liked(user):
            self.liked_users.remove(user)

    def upload_image(self, image):
        filename = secure_filename(image.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        filename = f'{str(uuid.uuid4())}.{extension}'
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.mkdir(app.config['UPLOAD_FOLDER'])
        image.save(image_path)
        self.image_url = f'/static/images/{filename}'

    def to_dict(self):
        data = {
            'id': self.id,
            'text': self.text,
            'hashtags': self.hashtags,
            'publication_date': str(self.publication_date or ''),
            'author': db.get_or_404(User, self.user_id).username,
            'by_user': self.by_user,
            'likes_count': self.likes_count(),
            'is_liked': self.is_liked(g.current_user),
            'links': {
                'self': url_for('post', post_id=self.id),
                'image': self.image_url
            }
        }
        return data

    def from_dict(self, data):
        for field in ['hashtags', 'text', 'publication_date', 'author_id', 'by_user']:
            if field in data:
                setattr(self, field, data[field])
