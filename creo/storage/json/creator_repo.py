from typing import Optional

from creo.storage.base import CreatorRepository
from creo.models import Creator
from creo.utils.helpers import load_creators, save_creators


class JsonCreatorRepository(CreatorRepository):
    def list_all(self) -> list[Creator]:
        return load_creators()

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        for c in self.list_all():
            if c.id == creator_id:
                return c
        return None

    def add(self, creator: Creator):
        creators = self.list_all()
        creators.append(creator)
        save_creators(creators)

    def delete(self, creator_id: str):
        creators = self.list_all()
        creators = [c for c in creators if c.id != creator_id]
        save_creators(creators)

    def save_all(self, creators: list[Creator]):
        save_creators(creators)
