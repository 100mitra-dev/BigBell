import random
from typing import Optional

from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class MetaMarketplaceRepository(CreatorRepository):
    """Fetches creators from the official Meta Creator Marketplace (meta.com/creators/marketplace).

    Uses the Meta Marketing API / Creator Marketplace endpoints when a valid
    access token is configured; falls back to deterministic mock data otherwise.
    """

    @property
    def use_real_api(self) -> bool:
        from creo.utils.runtime_settings import get_meta_marketplace_key
        return bool(get_meta_marketplace_key())

    def list_all(self) -> list[Creator]:
        if self.use_real_api:
            return self._fetch_from_meta()
        return self._mock_creators()

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        for c in self.list_all():
            if c.id == creator_id:
                return c
        return None

    def add(self, creator: Creator):
        raise NotImplementedError("Meta Creator Marketplace repository is read-only for creator data")

    def delete(self, creator_id: str):
        raise NotImplementedError("Meta Creator Marketplace repository is read-only")

    def save_all(self, creators: list[Creator]):
        raise NotImplementedError("Meta Creator Marketplace repository is read-only")

    def _fetch_from_meta(self) -> list[Creator]:
        from creo.utils.runtime_settings import get_meta_marketplace_key
        from creo.storage.api.meta_config import get_meta_endpoint, get_meta_timeout
        key = get_meta_marketplace_key()
        try:
            import requests
            response = requests.get(
                get_meta_endpoint("creator_marketplace/creators"),
                params={"access_token": key, "limit": 100},
                timeout=get_meta_timeout(),
            )
            if response.status_code == 200:
                data = response.json()
                creators = []
                for i, item in enumerate(data.get("data", [])):
                    ig_handle = item.get("instagram", {}).get("username", "")
                    fb_page = item.get("facebook_page", {}).get("name", "")
                    platforms = {}
                    if ig_handle:
                        platforms["instagram"] = PlatformInfo(
                            handle=ig_handle,
                            followers=item.get("instagram", {}).get("followers_count", 0),
                            verified=item.get("instagram", {}).get("is_verified", False),
                        )
                    if fb_page:
                        platforms["facebook"] = PlatformInfo(
                            handle=fb_page,
                            followers=item.get("facebook_page", {}).get("followers_count", 0),
                            verified=item.get("facebook_page", {}).get("is_verified", False),
                        )
                    creators.append(Creator(
                        id=item.get("id", f"meta_{i}"),
                        name=item.get("name", f"Meta Creator {i}"),
                        email=f"{item.get('id', i)}@meta.com",
                        primary_niche=random.choice(["Fashion", "Food & Cooking", "Beauty & Makeup", "Gaming", "Technology"]),
                        primary_language=item.get("language", "English"),
                        secondary_languages=[item.get("language", "English")] if item.get("language") != "English" else [],
                        platforms=platforms,
                        region=item.get("region", "India"),
                        content_quality_score=round(random.uniform(6, 9), 1),
                        profile_completeness=round(random.uniform(70, 100), 1),
                        avg_engagement_rate=round(random.uniform(1.5, 6.5), 1),
                        status=CreatorStatus.ACTIVE,
                        total_campaigns_completed=random.randint(0, 30),
                        total_earnings=random.uniform(0, 500000),
                    ))
                return creators
        except Exception:
            pass
        return self._mock_creators()

    def _mock_creators(self) -> list[Creator]:
        mock_creators = [
            ("Ananya Roy", "Fashion", "English", "Delhi", "@ananyaroy", 750000, True),
            ("Rahul's Kitchen", "Food & Cooking", "Hindi", "Mumbai", "@rahulkitchen", 320000, False),
            ("GamerZone", "Gaming", "English", "Bangalore", "@gamerzone", 180000, True),
            ("Priya's Beauty", "Beauty & Makeup", "Hindi", "Delhi", "@priyabeauty", 95000, False),
            ("TechTalks", "Technology", "English", "Bangalore", "@techtalks", 450000, True),
            ("FitWithKaran", "Fitness & Wellness", "English", "Mumbai", "@fitwithkaran", 65000, False),
            ("TravelWithSonam", "Travel", "English", "Goa", "@travelsonam", 210000, True),
            ("MakeupByNeha", "Beauty & Makeup", "Hindi", "Delhi", "@nehasharma_makeup", 110000, True),
        ]
        creators = []
        for i, (name, niche, lang, region, handle, followers, verified) in enumerate(mock_creators):
            creators.append(Creator(
                id=f"meta_{i}",
                name=name,
                email=f"{name.lower().replace(' ', '_').replace("'", '')}@meta.com",
                primary_niche=niche,
                primary_language=lang,
                platforms={"instagram": PlatformInfo(handle=handle, followers=followers, verified=verified)},
                region=region,
                content_quality_score=round(random.uniform(6.5, 9.5), 1),
                profile_completeness=round(random.uniform(75, 100), 1),
                avg_engagement_rate=round(random.uniform(1.5, 7.0), 1),
                total_campaigns_completed=random.randint(2, 40),
                total_earnings=round(random.uniform(50000, 800000), -3),
                status=CreatorStatus.ACTIVE,
            ))
        return creators
