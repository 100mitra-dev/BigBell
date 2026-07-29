import random
from typing import Optional

from src.core.models import Creator, CreatorStatus
from src.utils.helpers import load_creators, save_creators, search_creators, filter_by_status


class CreatorService:
    def __init__(self):
        self._creators: list[Creator] = []

    @property
    def creators(self) -> list[Creator]:
        if not self._creators:
            self._creators = load_creators()
        return self._creators

    def refresh(self):
        self._creators = load_creators()

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        for c in self.creators:
            if c.id == creator_id:
                return c
        return None

    def search(self, query: str = "") -> list[Creator]:
        if not query:
            return self.creators
        return search_creators(self.creators, query)

    def filter_by_status(self, status: str) -> list[Creator]:
        return filter_by_status(self.creators, status)

    def filter_by_niche(self, niche: str) -> list[Creator]:
        return [
            c
            for c in self.creators
            if c.primary_niche.lower() == niche.lower()
            or any(n.lower() == niche.lower() for n in c.secondary_niches)
        ]

    def filter_by_language(self, language: str) -> list[Creator]:
        return [
            c
            for c in self.creators
            if c.primary_language.lower() == language.lower()
            or any(l.lower() == language.lower() for l in c.secondary_languages)
        ]

    def get_pending_count(self) -> int:
        return len(self.filter_by_status("pending"))

    def get_onboarding_count(self) -> int:
        return len(self.filter_by_status("onboarding"))

    def get_active_count(self) -> int:
        return len(self.filter_by_status("active"))

    def get_inactive_count(self) -> int:
        return len(self.filter_by_status("inactive"))

    def update_status(self, creator_id: str, status: CreatorStatus):
        creator = self.get_by_id(creator_id)
        if creator:
            creator.status = status
            save_creators(self.creators)

    def update_profile_completeness(self, creator_id: str, value: float):
        creator = self.get_by_id(creator_id)
        if creator:
            creator.profile_completeness = value
            save_creators(self.creators)

    def get_niche_distribution(self) -> dict[str, int]:
        dist = {}
        for c in self.creators:
            dist[c.primary_niche] = dist.get(c.primary_niche, 0) + 1
        return dict(sorted(dist.items(), key=lambda x: -x[1]))

    def get_language_distribution(self) -> dict[str, int]:
        dist = {}
        for c in self.creators:
            dist[c.primary_language] = dist.get(c.primary_language, 0) + 1
        return dict(sorted(dist.items(), key=lambda x: -x[1]))

    def get_random_pending(self, count: int = 5) -> list[Creator]:
        pending = self.filter_by_status("pending")
        return random.sample(pending, min(count, len(pending)))
