from typing import Optional

from creo.storage.base import CampaignRepository
from creo.models import Campaign
from creo.utils.helpers import load_campaigns


class JsonCampaignRepository(CampaignRepository):
    _campaigns: list[Campaign] = []

    def list_all(self) -> list[Campaign]:
        if not self._campaigns:
            self._campaigns = load_campaigns()
        return self._campaigns

    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        for c in self.list_all():
            if c.id == campaign_id:
                return c
        return None

    def add(self, campaign: Campaign):
        self._campaigns.append(campaign)
        self._persist()

    def delete(self, campaign_id: str):
        self._campaigns = [c for c in self._campaigns if c.id != campaign_id]
        self._persist()

    def save_all(self, campaigns: list[Campaign]):
        self._campaigns = campaigns
        self._persist()

    def _persist(self):
        from creo.utils.helpers import save_json
        save_json("campaigns.json", [c.model_dump() for c in self._campaigns])
