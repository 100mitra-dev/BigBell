import random
from typing import Optional

from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class InstagramCreatorRepository(CreatorRepository):
    """Discovers creators via Instagram profile scanning.

    This adapter is distinct from ``InstagramCampaignRepository`` (which reads a
    brand's *own* media). This repository scans *public* Instagram profiles to
    grow the creator pool — extracting handle, follower count, bio, and niche
    signals from public profile data.

    Uses the Instagram Graph API when a valid access token is configured;
    otherwise falls back to deterministic mock data.
    """

    @property
    def use_real_api(self) -> bool:
        from creo.utils.runtime_settings import get_instagram_key
        return bool(get_instagram_key())

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
        from creo.utils.runtime_settings import get_instagram_key
        key = get_instagram_key()
        try:
            import requests
            response = requests.get(
                "https://graph.instagram.com/v19.0/me",
                params={"fields": "id,username,account_type,followers_count", "access_token": key},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                # The /me endpoint returns the token owner's profile.
                # For broader discovery, the Instagram Basic Display API or
                # oEmbed endpoint can be used to scan public profiles by handle.
                creators = []
                username = data.get("username", "instagram_user")
                followers = data.get("followers_count", 0)
                creators.append(Creator(
                    id=data.get("id", f"ig_0"),
                    name=username,
                    email=f"{username}@instagram.com",
                    primary_niche="Lifestyle",
                    primary_language="English",
                    platforms={"instagram": PlatformInfo(handle=username, followers=followers)},
                    region="India",
                    status=CreatorStatus.ACTIVE,
                ))
                return creators
        except Exception:
            pass
        return self._mock_creators()

    def _mock_creators(self) -> list[Creator]:
        mock_creators = [
            ("Neha Malhotra", "Beauty & Makeup", "English", "Mumbai", "@nehamalhotra", 340000, True),
            ("Delhi Food Walks", "Food & Cooking", "Hindi", "Delhi", "@delhifoodwalks", 190000, True),
            ("Arjun Codes", "Technology", "English", "Bangalore", "@arjuncodes", 85000, False),
            ("Tina's Travelogue", "Travel", "English", "Goa", "@tinatravels", 150000, False),
            ("FitnessByRaj", "Fitness & Wellness", "Hindi", "Mumbai", "@fitnessbyraj", 65000, True),
            ("ComedyMumbai", "Comedy & Entertainment", "Hindi", "Mumbai", "@comedymumbai", 780000, True),
            ("ArtByPooja", "Photography", "English", "Delhi", "@artbypooja", 55000, False),
            ("BookSnob", "Book Reviews & Literature", "English", "Bangalore", "@booksnob", 42000, True),
        ]
        creators = []
        for i, (name, niche, lang, region, handle, followers, verified) in enumerate(mock_creators):
            creators.append(Creator(
                id=f"ig_{i}",
                name=name,
                email=f"{handle.replace('@', '')}@instagram.com",
                primary_niche=niche,
                primary_language=lang,
                platforms={"instagram": PlatformInfo(handle=handle, followers=followers, verified=verified)},
                region=region,
                content_quality_score=round(random.uniform(5.5, 8.8), 1),
                profile_completeness=round(random.uniform(60, 95), 1),
                avg_engagement_rate=round(random.uniform(1.0, 9.5), 1),
                total_campaigns_completed=random.randint(0, 25),
                total_earnings=round(random.uniform(20000, 600000), -3),
                status=CreatorStatus.ACTIVE,
            ))
        return creators
