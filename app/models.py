import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app as app

from app import db

likes = db.Table(
    "likes",
    db.Model.metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete='cascade'), primary_key=True),
    sa.Column("post_id", sa.Integer, sa.ForeignKey("post.id", ondelete='cascade'), primary_key=True),
    sa.Column("date", sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc)),
)

friends = db.Table(
    "friends",
    db.Model.metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete='cascade'), primary_key=True),
    sa.Column("friend_id", sa.Integer, sa.ForeignKey("user.id", ondelete='cascade'), primary_key=True),
    sa.Column("add_date", sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc)),
)

community_user = db.Table(
    "community_user",
    db.Model.metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete='cascade'), primary_key=True),
    sa.Column("community_id", sa.Integer, sa.ForeignKey("community.id", ondelete='cascade'), primary_key=True),
    sa.Column("join_date", sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc)),
)


class Message(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(200))
    date: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id", ondelete='cascade'), index=True)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id", ondelete='cascade'), index=True)
    sender: so.Mapped['User'] = so.relationship(back_populates='sent_messages',
                                                primaryjoin="Message.sender_id == User.id")
    recipient: so.Mapped['User'] = so.relationship(back_populates='received_messages',
                                                   primaryjoin="Message.recipient_id == User.id")


class User(db.Model):
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
    skills: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
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
                                                            back_populates='followers', passive_deletes=True)
    followers: so.WriteOnlyMapped['User'] = so.relationship(secondary=friends, primaryjoin=(id == friends.c.friend_id),
                                                            secondaryjoin=(id == friends.c.user_id),
                                                            back_populates='following', passive_deletes=True)
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='author', passive_deletes=True)
    sessions: so.WriteOnlyMapped['Session'] = so.relationship(back_populates='user', passive_deletes=True)
    communities: so.WriteOnlyMapped['Community'] = so.relationship(
        secondary=community_user, back_populates='members', passive_deletes=True)
    own_communities: so.WriteOnlyMapped['Community'] = so.relationship(back_populates='owner', passive_deletes=True)
    received_messages: so.WriteOnlyMapped['Message'] = so.relationship(back_populates='recipient', passive_deletes=True,
                                                                       primaryjoin=(id == Message.recipient_id))
    sent_messages: so.WriteOnlyMapped['Message'] = so.relationship(back_populates='sender', passive_deletes=True,
                                                                   primaryjoin=(id == Message.sender_id))
    vacancies: so.WriteOnlyMapped['Vacancy'] = so.relationship(back_populates='employer', passive_deletes=True)


class Community(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[int] = so.mapped_column(sa.String(32), index=True)
    description: so.Mapped[str] = so.mapped_column(sa.String(500))
    register_date: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    image_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete='cascade'), index=True)
    owner: so.Mapped[User] = so.relationship(back_populates='own_communities')
    members: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=community_user, back_populates='communities', passive_deletes=True)
    community_posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='community', passive_deletes=True)


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    text: so.Mapped[str] = so.mapped_column(sa.String(500))
    image_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    hashtags: so.Mapped[str] = so.mapped_column(sa.String(100))
    publication_date: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.ForeignKey(User.id, ondelete='cascade'), index=True, nullable=True)
    community_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.ForeignKey(Community.id, ondelete='cascade'), index=True, nullable=True)
    author: so.Mapped['User'] = so.relationship(back_populates='posts')
    community: so.Mapped['Community'] = so.relationship(back_populates='community_posts')
    liked_users: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=likes, back_populates='liked_posts', passive_deletes=True)
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='post', passive_deletes=True)


class Comment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    text: so.Mapped[str] = so.mapped_column(sa.String(500))
    date: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete='cascade'), index=True)
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Post.id, ondelete='cascade'), index=True)
    author: so.Mapped[User] = so.relationship(back_populates='comments')
    post: so.Mapped[Post] = so.relationship(back_populates='comments')


class Session(db.Model):
    id: so.Mapped[uuid.UUID] = so.mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4, index=True)
    platform: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    ip: so.Mapped[str] = so.mapped_column(sa.String(100))
    expires: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(
        timezone.utc) + timedelta(days=app.config.get('SESSION_LIFETIME')))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete='cascade'), index=True)
    user: so.Mapped[User] = so.relationship(back_populates='sessions')


class Vacancy(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    skills: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    description: so.Mapped[str] = so.mapped_column(sa.String(500))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete='cascade'), index=True)
    employer: so.Mapped[User] = so.relationship(back_populates='vacancies')
    date: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
