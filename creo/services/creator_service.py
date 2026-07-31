import logging
import random

from creo.storage.factories import get_creator_repo
from creo.models import Creator, CreatorStatus
from creo.services.base import CachedRepositoryService

logger = logging.getLogger(__name__)


class CreatorService(CachedRepositoryService[Creator]):
    def __init__(self):
        super().__init__()
        logger.debug("CreatorService initialized")

    def _make_repo(self):
        return get_creator_repo()

    @property
    def creators(self) -> list[Creator]:
        return self.items

    def search(self, query: str = "") -> list[Creator]:
        if not query:
            return self.creators
        q = query.lower()
        return [c for c in self.creators if q in c.name.lower() or q in c.primary_niche.lower() or q in c.primary_language.lower() or q in c.email.lower()]

    def filter_by_status(self, status: str) -> list[Creator]:
        return [c for c in self.creators if c.status.value == status]

    def filter_by_niche(self, niche: str) -> list[Creator]:
        return [c for c in self.creators if c.primary_niche.lower() == niche.lower() or any(n.lower() == niche.lower() for n in c.secondary_niches)]

    def filter_by_language(self, language: str) -> list[Creator]:
        return [c for c in self.creators if c.primary_language.lower() == language.lower() or any(l.lower() == language.lower() for l in c.secondary_languages)]

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
            self.repo.save_all(self.creators)
            logger.info("Updated creator %s status to %s", creator_id, status.value)

    def update_profile_completeness(self, creator_id: str, value: float):
        creator = self.get_by_id(creator_id)
        if creator:
            creator.profile_completeness = value
            self.repo.save_all(self.creators)

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
