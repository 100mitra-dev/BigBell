from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic, List
from pathlib import Path
import json
import threading

from creo.models import Creator, Campaign, Payment, CampaignAssignment, FollowUpNote


T = TypeVar("T")


class JsonFileRepository(Generic[T]):
    """Generic JSON file-backed repository with atomic writes and thread safety."""

    def __init__(self, file_path: Path, model_cls: type[T], id_field: str = "id"):
        self.file_path = file_path
        self.model_cls = model_cls
        self.id_field = id_field
        self._lock = threading.RLock()
        self._cache: List[T] | None = None

    def _load(self) -> List[T]:
        if not self.file_path.exists():
            return []
        with self.file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [self.model_cls(**item) for item in data]

    def _save(self, items: List[T]) -> None:
        # Atomic write via temp file
        import stat
        tmp_path = self.file_path.with_suffix(".tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in items], f, indent=2)
            tmp_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            tmp_path.replace(self.file_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    def list_all(self) -> List[T]:
        with self._lock:
            if self._cache is None:
                self._cache = self._load()
            return list(self._cache)

    def get_by_id(self, item_id: str) -> Optional[T]:
        for item in self.list_all():
            if getattr(item, self.id_field) == item_id:
                return item
        return None

    def add(self, item: T) -> None:
        with self._lock:
            items = self.list_all()
            items.append(item)
            self._save(items)
            self._cache = list(items)

    def delete(self, item_id: str) -> None:
        with self._lock:
            items = [i for i in self.list_all() if getattr(i, self.id_field) != item_id]
            self._save(items)
            self._cache = list(items)

    def save_all(self, items: List[T]) -> None:
        with self._lock:
            self._save(items)
            self._cache = list(items)


class DbRepository(Generic[T]):
    """Generic SQLAlchemy repository (placeholder - requires SQLAlchemy models)."""

    def __init__(self, session_factory, orm_cls, model_cls: type[T]):
        self.session_factory = session_factory
        self.orm_cls = orm_cls
        self.model_cls = model_cls

    def list_all(self) -> List[T]:
        with self.session_factory() as session:
            return [self._orm_to_model(o) for o in session.query(self.orm_cls).all()]

    def get_by_id(self, item_id: str) -> Optional[T]:
        with self.session_factory() as session:
            orm = session.query(self.orm_cls).filter_by(id=item_id).first()
            return self._orm_to_model(orm) if orm else None

    def add(self, item: T) -> None:
        with self.session_factory() as session:
            session.add(self._model_to_orm(item))
            session.commit()

    def delete(self, item_id: str) -> None:
        with self.session_factory() as session:
            orm = session.query(self.orm_cls).filter_by(id=item_id).first()
            if orm:
                session.delete(orm)
                session.commit()

    def save_all(self, items: List[T]) -> None:
        with self.session_factory() as session:
            session.query(self.orm_cls).delete()
            for item in items:
                session.add(self._model_to_orm(item))
            session.commit()

    def _orm_to_model(self, orm) -> T:
        raise NotImplementedError

    def _model_to_orm(self, model: T):
        raise NotImplementedError


class CreatorRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Creator]: ...

    @abstractmethod
    def get_by_id(self, creator_id: str) -> Optional[Creator]: ...

    @abstractmethod
    def add(self, creator: Creator): ...

    @abstractmethod
    def delete(self, creator_id: str): ...

    @abstractmethod
    def save_all(self, creators: list[Creator]): ...


class CampaignRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Campaign]: ...

    @abstractmethod
    def get_by_id(self, campaign_id: str) -> Optional[Campaign]: ...

    @abstractmethod
    def add(self, campaign: Campaign): ...

    @abstractmethod
    def delete(self, campaign_id: str): ...

    @abstractmethod
    def save_all(self, campaigns: list[Campaign]): ...


class PaymentRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Payment]: ...

    @abstractmethod
    def get_by_id(self, payment_id: str) -> Optional[Payment]: ...

    @abstractmethod
    def add(self, payment: Payment): ...

    @abstractmethod
    def delete(self, payment_id: str): ...

    @abstractmethod
    def save_all(self, payments: list[Payment]): ...


class FollowUpNoteRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[FollowUpNote]: ...

    @abstractmethod
    def get_by_id(self, note_id: str) -> Optional[FollowUpNote]: ...

    @abstractmethod
    def get_for_campaign(self, campaign_id: str) -> list[FollowUpNote]: ...

    @abstractmethod
    def add(self, note: FollowUpNote): ...

    @abstractmethod
    def delete(self, note_id: str): ...

    @abstractmethod
    def save_all(self, notes: list[FollowUpNote]): ...


class AssignmentRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[CampaignAssignment]: ...

    @abstractmethod
    def get_by_id(self, assignment_id: str) -> Optional[CampaignAssignment]: ...

    @abstractmethod
    def get_for_campaign(self, campaign_id: str) -> list[CampaignAssignment]: ...

    @abstractmethod
    def get_for_creator(self, creator_id: str) -> list[CampaignAssignment]: ...

    @abstractmethod
    def add(self, assignment: CampaignAssignment): ...

    @abstractmethod
    def delete(self, assignment_id: str): ...

    @abstractmethod
    def save_all(self, assignments: list[CampaignAssignment]): ...