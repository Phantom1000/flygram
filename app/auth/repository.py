import uuid
from abc import ABC, abstractmethod

from app import db
from app.models import Session


class SessionRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, session_id: uuid.UUID) -> Session:
        pass

    @abstractmethod
    def add(self, user_id: int, platform: str, ip: str) -> Session:
        pass

    @abstractmethod
    def delete(self, session: Session) -> None:
        pass


class SessionRepository(SessionRepositoryInterface):
    def add(self, user_id: int, platform: str, ip: str) -> Session:
        session: Session = Session(user_id=user_id, platform=platform, ip=ip)
        db.session.add(session)
        db.session.commit()
        return session

    def get_by_id(self, session_id: uuid.UUID) -> Session:
        return db.get_or_404(Session, session_id)

    def delete(self, session: Session) -> None:
        db.session.delete(session)
        db.session.commit()
