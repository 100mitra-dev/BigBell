"""BigBell Meta Creator Marketplace repository — fetches creators from Meta Graph API."""
import random
from typing import Optional

from creo.storage.api.base_api import BaseApiRepository
from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class MetaMarketplaceRepository(BaseApiRepository, CreatorRepository):
    """Fetches creators from the official Meta Creator Marketplace.

    Uses the Meta Marketing API / Creator Marketplace endpoints when a valid
    access token is configured; falls back to deterministic mock data otherwise.
    """

    def _check_key(self) -> bool:
        try:
            from creo.utils.runtime_settings import get_meta_marketplace_key
            return bool(get_meta_marketplace_key())
        except Exception:
            return False

    def _mock_data(self) -> list[Creator]:
        return self._mock_creators()

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
        try:
            from creo.utils.runtime_settings import get_meta_marketplace_key
            from creo.storage.api.meta_config import get_meta_endpoint, get_meta_timeout
            key = get_meta_marketplace_key()
        except (ImportError, OSError, ValueError) as e:
            import logging; logging.getLogger(__name__).warning('%s fallback: %s', __name__, e)
            return self._mock_creators()
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
                    creators.append(Creator(
                        id=f"meta_{i}",
                        name=item.get("name", ig_handle or f"Creator {i}"),
                        email=item.get("email", f"meta_{i}@marketplace.com"),
                        primary_niche=item.get("category", "General"),
                        secondary_niches=[],
                        primary_language="English",
                        secondary_languages=[],
                        platforms={"instagram": PlatformInfo(
                            handle=f"@{ig_handle}" if ig_handle else f"@meta_{i}",
                            followers=int(item.get("followers_count", 0)),
                            verified=bool(item.get("is_verified", False)),
                        )},
                        content_quality_score=0.0,
                        profile_completeness=80.0,
                        avg_engagement_rate=float(item.get("engagement_rate", 0.0)),
                        status=CreatorStatus.ACTIVE,
                        region=item.get("location", ""),
                        verified=bool(item.get("is_verified", False)),
                        verification_score=70.0,
                    ))
                return creators
        except (ImportError, OSError) as e:
            import logging; logging.getLogger(__name__).warning('%s fetch fallback: %s', __name__, e)
        return self._mock_creators()

    def _mock_creators(self) -> list[Creator]:
        mock_creators = [
            ("Ananya Roy", "Fashion", "English", "Delhi", "@ananyaroy", 750000, True),
            ("Rahul's Kitchen", "Food & Cooking", "Hindi", "Mumbai", "@rahulkitchen", 320000, False),
            ("Gamer Zone", "Gaming", "English", "Bangalore", "@gamerzone", 180000, True),
            ("Tech with Priya", "Technology", "English", "Hyderabad", "@priyatech", 95000, True),
            ("Dance with Maya", "Dance & Choreography", "Tamil", "Chennai", "@mayadance", 42000, False),
        ]
        creators = []
        for i, (name, niche, lang, region, handle, followers, verified) in enumerate(mock_creators):
            creators.append(Creator(
                id=f"meta_{i}",
                name=name,
                email=f"{handle[1:]}@marketplace.com",
                primary_niche=niche,
                secondary_niches=[],
                primary_language=lang,
                secondary_languages=[],
                platforms={"instagram": PlatformInfo(handle=handle, followers=followers, verified=verified)},
                content_quality_score=0.0,
                profile_completeness=80.0,
                avg_engagement_rate=random.uniform(2.0, 6.0),
                status=CreatorStatus.ACTIVE,
                region=region,
                verified=verified,
                verification_score=70.0,
            ))
        return creators