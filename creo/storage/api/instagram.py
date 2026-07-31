from typing import Optional
import random

from creo.storage.base import CampaignRepository
from creo.models import Campaign


class InstagramCampaignRepository(CampaignRepository):
    @property
    def use_real_api(self) -> bool:
        from creo.utils.runtime_settings import get_instagram_key
        return bool(get_instagram_key())

    def list_all(self) -> list[Campaign]:
        if self.use_real_api:
            return self._fetch_from_instagram()
        return self._mock_campaigns()

    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        for c in self.list_all():
            if c.id == campaign_id:
                return c
        return None

    def add(self, campaign: Campaign):
        raise NotImplementedError("Instagram API repository is read-only for campaign data")

    def delete(self, campaign_id: str):
        raise NotImplementedError("Instagram API repository is read-only")

    def save_all(self, campaigns: list[Campaign]):
        raise NotImplementedError("Instagram API repository is read-only")

    def _fetch_from_instagram(self) -> list[Campaign]:
        from creo.utils.runtime_settings import get_instagram_key
        key = get_instagram_key()
        try:
            import requests
            response = requests.get(
                f"https://graph.instagram.com/v12.0/me/media",
                params={"fields": "id,caption", "access_token": key},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                campaigns = []
                for i, item in enumerate(data.get("data", [])):
                    campaigns.append(Campaign(
                        id=f"ig_camp_{i}",
                        title=item.get("caption", f"Instagram Campaign {i}")[:50],
                        brand="Instagram Brand",
                        description=item.get("caption", ""),
                        budget=random.uniform(10000, 500000),
                        deadline="2026-12-31",
                        status="active",
                    ))
                return campaigns
        except Exception:
            pass
        return self._mock_campaigns()

    def _mock_campaigns(self) -> list[Campaign]:
        mock_campaigns = [
            ("Summer Collection Launch", "FashionBrand"),
            ("New Recipe Series", "FoodieCo"),
            ("Fitness Challenge", "FitLife"),
            ("Travel Vlog Contest", "Wanderlust"),
        ]
        campaigns = []
        for i, (title, brand) in enumerate(mock_campaigns):
            campaigns.append(Campaign(
                id=f"ig_camp_{i}",
                title=title,
                brand=brand,
                description=f"{title} - Instagram influencer campaign",
                budget=random.uniform(50000, 300000),
                deadline="2026-06-30",
                target_niches=[random.choice(["Fashion", "Food & Cooking", "Fitness & Wellness", "Travel"])],
                target_languages=["English"],
                status="active",
            ))
        return campaigns
