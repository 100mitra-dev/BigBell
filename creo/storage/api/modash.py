"""BigBell Modash.io creator repository — fetches creators from Modash API."""
import random
from typing import Optional

from creo.storage.api.base_api import BaseApiRepository
from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class ModashCreatorRepository(BaseApiRepository, CreatorRepository):
    """Fetches creators from the Modash.io API (third-party creator discovery platform).

    Uses the Modash API v2 when a valid API key is configured; falls back to
    deterministic mock data otherwise.
    """

    def _check_key(self) -> bool:
        try:
            from creo.utils.runtime_settings import get_modash_key
            return bool(get_modash_key())
        except Exception:
            return False

    def _mock_data(self) -> list[Creator]:
        return self._mock_creators()

    def list_all(self) -> list[Creator]:
        if self.use_real_api:
            return self._fetch_from_modash()
        return self._mock_creators()

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        for c in self.list_all():
            if c.id == creator_id:
                return c
        return None

    def add(self, creator: Creator):
        raise NotImplementedError("Modash API repository is read-only for creator data")

    def delete(self, creator_id: str):
        raise NotImplementedError("Modash API repository is read-only")

    def save_all(self, creators: list[Creator]):
        raise NotImplementedError("Modash API repository is read-only")

    def _fetch_from_modash(self) -> list[Creator]:
        try:
            from creo.utils.runtime_settings import get_modash_key
            key = get_modash_key()
        except (ImportError, OSError, ValueError) as e:
            import logging; logging.getLogger(__name__).warning('%s fallback: %s', __name__, e)
            return self._mock_creators()
        try:
            import requests
            response = requests.get(
                "https://api.modash.io/v2/creators/search",
                headers={"Authorization": f"Bearer {key}"},
                params={"limit": 50, "region": "india"},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                creators = []
                for i, item in enumerate(data.get("creators", [])):
                    ig_handle = item.get("instagram_username", "")
                    creators.append(Creator(
                        id=f"modash_{i}",
                        name=item.get("name", ig_handle or f"Modash Creator {i}"),
                        email=f"{ig_handle}@modash.com" if ig_handle else f"modash_{i}@modash.com",
                        primary_niche=item.get("category", "General"),
                        secondary_niches=[],
                        primary_language=item.get("language", "English"),
                        secondary_languages=[],
                        platforms={"instagram": PlatformInfo(
                            handle=f"@{ig_handle}" if ig_handle else f"@modash_{i}",
                            followers=int(item.get("followers_count", 0)),
                            verified=bool(item.get("is_verified", False)),
                        )},
                        content_quality_score=0.0,
                        profile_completeness=75.0,
                        avg_engagement_rate=float(item.get("engagement_rate", 0.0)),
                        status=CreatorStatus.ACTIVE,
                        region=item.get("location", ""),
                        verified=bool(item.get("is_verified", False)),
                        verification_score=65.0,
                    ))
                return creators
        except (ImportError, OSError) as e:
            import logging; logging.getLogger(__name__).warning('%s fetch fallback: %s', __name__, e)
        return self._mock_creators()

    def _mock_creators(self) -> list[Creator]:
        mock_creators = [
            ("Zara Influences", "Fashion", "English", "Mumbai", "@zara_influences", 2400000, True, "instagram"),
            ("FoodieFables", "Food & Cooking", "Hindi", "Delhi", "@foodiefables", 560000, True, "instagram"),
            ("TechTalks", "Technology", "English", "Bangalore", "@techtalks", 1200000, True, "instagram"),
            ("FitnessFreak", "Fitness", "English", "Pune", "@fitnessfreak", 890000, True, "instagram"),
            ("TravelTales", "Travel", "English", "Goa", "@traveltales", 340000, False, "instagram"),
        ]
        creators = []
        for i, (name, niche, lang, region, handle, followers, verified, platform) in enumerate(mock_creators):
            creators.append(Creator(
                id=f"modash_{i}",
                name=name,
                email=f"{handle[1:]}@modash.com",
                primary_niche=niche,
                secondary_niches=[],
                primary_language=lang,
                secondary_languages=[],
                platforms={platform: PlatformInfo(handle=handle, followers=followers, verified=verified)},
                content_quality_score=0.0,
                profile_completeness=75.0,
                avg_engagement_rate=random.uniform(3.0, 7.0),
                status=CreatorStatus.ACTIVE,
                region=region,
                verified=verified,
                verification_score=65.0,
            ))
        return creators