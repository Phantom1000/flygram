from abc import ABC, abstractmethod

import sqlalchemy as sa
from flask import url_for

from app import db
from app.models import Community, User
from app.utils import paginate
from flask import g


class CommunityRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, community_id: int) -> Community:
        pass

    @abstractmethod
    def get_communities(self) -> list[Community]:
        pass

    @abstractmethod
    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[Community]] = sa.select(Community)
    ) -> dict:
        pass

    @abstractmethod
    def add(self, data: dict) -> Community:
        pass

    @abstractmethod
    def update_model_from_dict(self, model: Community, data: dict):
        pass

    @abstractmethod
    def delete(self, community: Community) -> None:
        pass

    @abstractmethod
    def model_to_dict(self, model: Community) -> dict:
        pass

    @abstractmethod
    def update_image_url(self, community: Community, image_url: str) -> None:
        pass

    @abstractmethod
    def is_member(self, community: Community, user: User) -> bool:
        pass

    @abstractmethod
    def join(self, community: Community, user: User) -> None:
        pass

    @abstractmethod
    def leave(self, community: Community, user: User) -> None:
        pass

    @abstractmethod
    def get_members_count(self, community: Community) -> int:
        pass


class CommunityRepository(CommunityRepositoryInterface):
    def get_by_id(self, community_id: int) -> Community:
        return db.get_or_404(Community, community_id)

    def get_communities(self) -> list[Community]:
        query = sa.select(Community)
        return db.session.scalars(query).all()

    def add(self, data: dict) -> Community:
        community: Community = Community(**data)
        db.session.add(community)
        db.session.commit()
        return community

    def paginate_by_filters(
            self, filters: dict, page: int, per_page: int, query: sa.Select[tuple[Community]] = sa.select(Community)
    ) -> dict:
        return paginate(query, Community, self, filters, page, per_page, 'communities', Community.register_date)

    def delete(self, community: Community) -> None:
        db.session.delete(community)
        db.session.commit()

    def update_image_url(self, community: Community, image_url: str) -> None:
        community.image_url = image_url
        db.session.commit()

    def update_model_from_dict(self, model: Community, data: dict):
        for field in ['name', 'description']:
            if field in data:
                setattr(model, field, data[field])
        db.session.commit()

    def model_to_dict(self, model: Community) -> dict:
        data = {
            'id': model.id,
            'name': model.name,
            'description': model.description,
            'register_date': str(model.register_date or ''),
            'owner': model.owner.username,
            'is_member': self.is_member(model, g.current_user),
            'members_count': self.get_members_count(model),
            'links': {
                'self': url_for('community', community_id=model.id),
                'image': model.image_url
            }
        }
        return data

    def is_member(self, community: Community, user: User) -> bool:
        query = community.members.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def join(self, community: Community, user: User) -> None:
        community.members.add(user)
        db.session.commit()

    def leave(self, community: Community, user: User) -> None:
        community.members.remove(user)
        db.session.commit()

    def get_members_count(self, community: Community) -> int:
        query = sa.select(sa.func.count()).select_from(community.members.select().subquery())
        return db.session.scalar(query)
