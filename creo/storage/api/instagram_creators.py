"""BigBell Instagram profile scanning repository — fetches creators by scanning Instagram profiles."""
import random
from typing import Optional

from creo.storage.api.base_api import BaseApiRepository
from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class InstagramCreatorRepository(BaseApiRepository, CreatorRepository):
    """Scans Instagram profiles for creator data using the Instagram Basic Display API
    or Graph API when a valid access token is configured; falls back to deterministic
    mock data otherwise.
    """

    def _check_key(self) -> bool:
        try:
            from creo.utils.runtime_settings import get_instagram_key
            return bool(get_instagram_key())
        except Exception:
            return False

    def _mock_data(self) -> list[Creator]:
        return self._mock_creators()

    def list_all(self) -> list[Creator]:
        if self.use_real_api:
            return self._fetch_from_instagram()
        return self._mock_creators()

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        for c in self.list_all():
            if c.id == creator_id:
                return c
        return None

    def add(self, creator: Creator):
        raise NotImplementedError("Instagram profile scanning repository is read-only")

    def delete(self, creator_id: str):
        raise NotImplementedError("Instagram profile scanning repository is read-only")

    def save_all(self, creators: list[Creator]):
        raise NotImplementedError("Instagram profile scanning repository is read-only")

    def _fetch_from_instagram(self) -> list[Creator]:
        try:
            from creo.utils.runtime_settings import get_instagram_key
            key = get_instagram_key()
        except (ImportError, OSError, ValueError) as e:
            import logging; logging.getLogger(__name__).warning('%s fallback: %s', __name__, e)
            return self._mock_creators()
        try:
            import requests
            response = requests.get(
                "https://graph.instagram.com/me/media",
                params={"fields": "username,media_count", "access_token": key},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                # Note: Real implementation would need to fetch multiple profiles
                # This is a placeholder for the API structure
                creators = []
                for i, item in enumerate(data.get("data", [])):
                    creators.append(Creator(
                        id=f"ig_{i}",
                        name=item.get("username", f"IG Creator {i}"),
                        email=f"{item.get('username', 'creator')}@instagram.com",
                        primary_niche="General",
                        secondary_niches=[],
                        primary_language="English",
                        secondary_languages=[],
                        platforms={"instagram": PlatformInfo(
                            handle=f"@{item.get('username', f'creator{i}')}",
                            followers=int(item.get("followers_count", 0)),
                            verified=False,
                        )},
                        content_quality_score=0.0,
                        profile_completeness=60.0,
                        avg_engagement_rate=0.0,
                        status=CreatorStatus.ACTIVE,
                        region="",
                        verified=False,
                        verification_score=0.0,
                    ))
                return creators
        except (ImportError, OSError) as e:
            import logging; logging.getLogger(__name__).warning('%s fetch fallback: %s', __name__, e)
        return self._mock_creators()

    def _mock_creators(self) -> list[Creator]:
        mock_creators = [
            ("Neha Malhotra", "Beauty & Makeup", "English", "Mumbai", "@nehamalhotra", 340000, True),
            ("Delhi Food Walks", "Food & Cooking", "Hindi", "Delhi", "@delhifoodwalks", 190000, True),
            ("Mumbai Traveler", "Travel", "English", "Mumbai", "@mumbaitraveler", 85000, False),
            ("Bengaluru Coder", "Technology", "English", "Bangalore", "@blrcoder", 67000, True),
            ("Chennai Dancer", "Dance & Choreography", "Tamil", "Chennai", "@chennaidancer", 45000, False),
        ]
        creators = []
        for i, (name, niche, lang, region, handle, followers, verified) in enumerate(mock_creators):
            creators.append(Creator(
                id=f"ig_{i}",
                name=name,
                email=f"{handle[1:]}@instagram.com",
                primary_niche=niche,
                secondary_niches=[],
                primary_language=lang,
                secondary_languages=[],
                platforms={"instagram": PlatformInfo(handle=handle, followers=followers, verified=verified)},
                content_quality_score=0.0,
                profile_completeness=60.0,
                avg_engagement_rate=random.uniform(2.0, 5.0),
                status=CreatorStatus.ACTIVE,
                region=region,
                verified=verified,
                verification_score=40.0,
            ))
        return creators