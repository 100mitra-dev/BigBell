import logging

from creo.storage.factories import get_campaign_repo
from creo.models import Campaign
from creo.services.base import CachedRepositoryService

logger = logging.getLogger(__name__)


class CampaignService(CachedRepositoryService[Campaign]):
    def __init__(self):
        super().__init__()
        logger.debug("CampaignService initialized")

    def _make_repo(self):
        return get_campaign_repo()

    @property
    def campaigns(self) -> list[Campaign]:
        return self.items


    def get_active_count(self) -> int:
        return len(self.filter_by_status("active"))

    def get_completed_count(self) -> int:
        return len(self.filter_by_status("completed"))

    def get_total_budget(self) -> float:
        return sum(c.budget for c in self.campaigns if c.status == "active")

    def get_active_campaigns(self) -> list[Campaign]:
        return self.filter_by_status("active")

    def get_budget_range(self) -> tuple[float, float]:
        active = self.get_active_campaigns()
        if not active:
            return (0, 0)
        return (min(c.budget for c in active), max(c.budget for c in active))
