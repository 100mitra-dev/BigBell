import logging
import random
from dataclasses import dataclass
from typing import Optional

from creo.storage.factories import get_creator_repo
from creo.models import Creator, CreatorStatus
from creo.services.base import CachedRepositoryService

logger = logging.getLogger(__name__)


@dataclass
class CreatorSearchQuery:
    niche: Optional[str] = None
    language: Optional[str] = None
    region: Optional[str] = None
    min_followers: Optional[int] = None
    min_engagement: Optional[float] = None
    verified_only: bool = False
    tier: Optional[str] = None
    sort_by: str = "followers"  # followers | engagement | name
    sort_desc: bool = True
    page: int = 1
    page_size: int = 50


@dataclass
class PaginatedResult:
    items: list[Creator]
    total: int
    page: int
    page_size: int
    total_pages: int


class CreatorService(CachedRepositoryService[Creator]):
    def __init__(self):
        super().__init__()
        logger.debug("CreatorService initialized")

    def _make_repo(self):
        return get_creator_repo()

    @property
    def creators(self) -> list[Creator]:
        return self.items


    def get_pending_count(self) -> int:
        return len(self.filter_by_status("pending"))

    def get_onboarding_count(self) -> int:
        return len(self.filter_by_status("onboarding"))

    def get_active_count(self) -> int:
        return len(self.filter_by_status("active"))

    def get_inactive_count(self) -> int:
        return len(self.filter_by_status("inactive"))

    def update_status(self, creator_id: str, status: CreatorStatus) -> bool:
        creator = self.get_by_id(creator_id)
        if creator:
            creator.status = status
            self.repo.save_all(self.creators)
            logger.info("Updated creator %s status to %s", creator_id, status.value)
            return True
        return False
    def update_profile_completeness(self, creator_id: str, value: float) -> bool:
        creator = self.get_by_id(creator_id)
        if creator:
            creator.profile_completeness = min(max(value, 0.0), 100.0)
            self.repo.save_all(self.creators)
            return True
        return False
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

    def get_random_pending(self, count: int = 5, seed: Optional[int] = None) -> list[Creator]:
        pending = self.filter_by_status("pending")
        rng = random.Random(seed) if seed is not None else random
        return rng.sample(pending, min(count, len(pending)))

    def advanced_search(self, query: CreatorSearchQuery) -> PaginatedResult:
        results = self.creators

        if query.niche:
            results = [c for c in results if query.niche.lower() in [n.lower() for n in c.niches]]
        if query.language:
            results = [c for c in results if query.language.lower() in [l.lower() for l in c.languages]]
        if query.region:
            results = [c for c in results if query.region.lower() in (c.region or "").lower()]
        if query.min_followers:
            results = [c for c in results if c.total_followers >= query.min_followers]
        if query.min_engagement:
            results = [c for c in results if c.avg_engagement_rate >= query.min_engagement]
        if query.verified_only:
            results = [c for c in results if c.verified]
        if query.tier:
            results = [c for c in results if c.tier.lower() == query.tier.lower()]

        # Sorting
        reverse = query.sort_desc
        if query.sort_by == "followers":
            results.sort(key=lambda c: c.total_followers, reverse=reverse)
        elif query.sort_by == "engagement":
            results.sort(key=lambda c: c.avg_engagement_rate, reverse=reverse)
        elif query.sort_by == "name":
            results.sort(key=lambda c: c.name.lower(), reverse=reverse)
        else:
            results.sort(key=lambda c: c.total_followers, reverse=reverse)

        # Pagination
        total = len(results)
        page_size = max(1, query.page_size)
        page = max(1, query.page)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        items = results[start:end]

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def facet_values(self) -> dict[str, dict[str, int]]:
        niches = {}
        languages = {}
        regions = {}
        tiers = {}
        for c in self.creators:
            for n in c.niches:
                niches[n] = niches.get(n, 0) + 1
            for l in c.languages:
                languages[l] = languages.get(l, 0) + 1
            if c.region:
                regions[c.region] = regions.get(c.region, 0) + 1
            tiers[c.tier] = tiers.get(c.tier, 0) + 1
        return {
            "niches": dict(sorted(niches.items(), key=lambda x: -x[1])),
            "languages": dict(sorted(languages.items(), key=lambda x: -x[1])),
            "regions": dict(sorted(regions.items(), key=lambda x: -x[1])),
            "tiers": dict(sorted(tiers.items(), key=lambda x: -x[1])),
        }