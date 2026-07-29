from typing import Optional

from src.core.models import Campaign
from src.utils.helpers import load_campaigns, search_campaigns, filter_by_status


class CampaignService:
    def __init__(self):
        self._campaigns: list[Campaign] = []

    @property
    def campaigns(self) -> list[Campaign]:
        if not self._campaigns:
            self._campaigns = load_campaigns()
        return self._campaigns

    def refresh(self):
        self._campaigns = load_campaigns()

    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        for c in self.campaigns:
            if c.id == campaign_id:
                return c
        return None

    def search(self, query: str = "") -> list[Campaign]:
        if not query:
            return self.campaigns
        return search_campaigns(self.campaigns, query)

    def filter_by_status(self, status: str) -> list[Campaign]:
        return filter_by_status(self.campaigns, status)

    def filter_by_niche(self, niche: str) -> list[Campaign]:
        return [
            c
            for c in self.campaigns
            if niche.lower() in [n.lower() for n in c.target_niches]
        ]

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
