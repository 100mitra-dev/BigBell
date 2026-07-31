import logging
from typing import Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CachedRepositoryService(Generic[T]):
    """Lazily loads and caches a repository's records behind a domain service."""

    def __init__(self):
        self._items: list[T] = []
        self.repo = self._make_repo()

    def _make_repo(self):
        raise NotImplementedError

    @property
    def items(self) -> list[T]:
        if not self._items:
            self._items = self.repo.list_all()
        return self._items

    def refresh(self):
        self._items = self.repo.list_all()

    def get_by_id(self, item_id: str) -> Optional[T]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def add(self, item: T):
        self.repo.add(item)
        self.refresh()
        logger.info("Added %s (id=%s)", type(item).__name__, item.id)

    def delete(self, item_id: str):
        self.repo.delete(item_id)
        self.refresh()
        logger.info("Deleted %s (id=%s)", type(self).__name__, item_id)
