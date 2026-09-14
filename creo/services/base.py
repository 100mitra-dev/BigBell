from __future__ import annotations
import logging
from typing import Any, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CachedRepositoryService(Generic[T]):
    """Lazily loads and caches a repository's records behind a domain service."""

    def __init__(self):
        self._items: list[T] = []
        self.repo = self._make_repo()

    def _make_repo(self):
        raise NotImplementedError(f"{type(self).__name__} must implement _make_repo()")

    @property
    def items(self) -> list[T]:
        if not self._items:
            self._items = self.repo.list_all()
        return self._items

    def refresh(self):
        self._items = self.repo.list_all()

    def get_by_id(self, item_id: str) -> Optional[T]:
        for item in self.items:
            if getattr(item, "id", None) == item_id:
                return item
        return None

    def _str(self, value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value or "")

    def _texts(self, item: T) -> list[str]:
        texts: list[str] = []
        for key in ("name", "title", "brand", "description", "email",
                    "primary_niche", "primary_language", "question", "answer", "category"):
            value = getattr(item, key, None)
            if value:
                texts.append(self._str(value).lower())
        for key in ("secondary_niches", "secondary_languages", "target_niches",
                    "target_languages", "requirements"):
            for value in getattr(item, key, None) or []:
                texts.append(self._str(value).lower())
        return texts

    def search(self, query: str = "") -> list[T]:
        if not query:
            return self.items
        q = query.lower()
        return [item for item in self.items if any(q in text for text in self._texts(item))]

    def filter_by_status(self, status: str) -> list[T]:
        wanted = self._str(status).lower()
        return [item for item in self.items
                if self._str(getattr(item, "status", "")).lower() == wanted]

    def filter_by_niche(self, niche: str) -> list[T]:
        wanted = niche.lower()
        out = []
        for item in self.items:
            niches = [self._str(getattr(item, "primary_niche", "")).lower()]
            niches += [self._str(n).lower() for n in getattr(item, "secondary_niches", None) or []]
            niches += [self._str(n).lower() for n in getattr(item, "target_niches", None) or []]
            if wanted in niches:
                out.append(item)
        return out

    def get_for_campaign(self, campaign_id: str) -> list[T]:
        direct = [item for item in self.items if getattr(item, "campaign_id", None) == campaign_id]
        if direct:
            return direct
        return [item for item in self.items if campaign_id in (getattr(item, "assigned_creators", None) or [])]

    def get_for_creator(self, creator_id: str) -> list[T]:
        direct = [item for item in self.items if getattr(item, "creator_id", None) == creator_id]
        if direct:
            return direct
        return [item for item in self.items if creator_id in (getattr(item, "assigned_creators", None) or [])]

    def export_models(self) -> list[dict]:
        return [item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in self.items]

    def import_models(self, data: list[dict], model_cls=None) -> None:
        items = [model_cls(**d) for d in data] if model_cls else data
        self.repo.save_all(items)
        self.refresh()

    def add(self, item: T):
        self.repo.add(item)
        self.refresh()
        logger.info("Added %s (id=%s)", type(item).__name__, getattr(item, "id", "?"))

    def delete(self, item_id: str):
        self.repo.delete(item_id)
        self.refresh()
        logger.info("Deleted %s (id=%s)", type(self).__name__, item_id)
