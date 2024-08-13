import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from abc import ABC, abstractmethod

from app import db
from app.models import Session, User
from app.utils import paginate


class SessionRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, session_id: uuid.UUID) -> Session:
        pass

    @abstractmethod
    def add(self, user_id: int, platform: str, ip: str) -> Session:
        pass

    @abstractmethod
    def refresh(self, session: Session) -> str:
        pass

    @abstractmethod
    def paginate(self, page: int, per_page: int, user: User,
                 query: sa.Select[tuple[Session]] = sa.select(Session)) -> dict:
        pass

    @abstractmethod
    def model_to_dict(self, model: Session):
        pass

    @abstractmethod
    def delete(self, session: Session) -> None:
        pass

    @abstractmethod
    def delete_all(self, user: User) -> None:
        pass


class SessionRepository(SessionRepositoryInterface):
    def add(self, user_id: int, platform: str, ip: str) -> Session:
        session: Session = Session(user_id=user_id, platform=platform, ip=ip)
        db.session.add(session)
        db.session.commit()
        return session

    def paginate(self, page: int, per_page: int, user: User,
                 query: sa.Select[tuple[Session]] = sa.select(Session)) -> dict:
        query = query.filter_by(user_id=user.id).options(so.joinedload(Session.user))
        return paginate(query, Session, self, {}, page, per_page, 'sessions', Session.created_at)

    def refresh(self, session: Session) -> str:
        session.id = uuid.uuid4()
        db.session.commit()
        db.session.refresh(session)
        return str(session.id)

    def get_by_id(self, session_id: uuid.UUID) -> Session:
        return db.get_or_404(Session, session_id)

    def model_to_dict(self, model: Session) -> dict:
        data = {
            'id': model.id,
            'platform': model.platform,
            'created_at': str(model.created_at or ''),
            'ip': model.ip,
            'user': model.user.username
        }
        return data

    def delete(self, session: Session) -> None:
        db.session.delete(session)
        db.session.commit()

    def delete_all(self, user: User) -> None:
        db.session.execute(sa.delete(Session).filter_by(user_id=user.id))
        db.session.commit()
