from typing import Optional
import random

from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class YouTubeCreatorRepository(CreatorRepository):
    @property
    def use_real_api(self) -> bool:
        from creo.utils.runtime_settings import get_youtube_key
        return bool(get_youtube_key())

    def list_all(self) -> list[Creator]:
        if self.use_real_api:
            return self._fetch_from_youtube()
        return self._mock_creators()

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        for c in self.list_all():
            if c.id == creator_id:
                return c
        return None

    def add(self, creator: Creator):
        raise NotImplementedError("YouTube API repository is read-only for creator data")

    def delete(self, creator_id: str):
        raise NotImplementedError("YouTube API repository is read-only")

    def save_all(self, creators: list[Creator]):
        raise NotImplementedError("YouTube API repository is read-only")

    def _fetch_from_youtube(self) -> list[Creator]:
        from creo.utils.runtime_settings import get_youtube_key
        key = get_youtube_key()
        try:
            import requests
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "type": "channel", "q": "creator", "key": key},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                creators = []
                for i, item in enumerate(data.get("items", [])):
                    snippet = item.get("snippet", {})
                    channel_id = item["id"].get("channelId", f"yt_{i}")
                    creators.append(Creator(
                        id=channel_id,
                        name=snippet.get("title", f"YouTube Creator {i}"),
                        email=f"{channel_id}@youtube.com",
                        primary_niche="Technology",
                        primary_language="English",
                        platforms={"youtube": PlatformInfo(handle=snippet.get("channelId", ""), followers=0)},
                        status=CreatorStatus.ACTIVE,
                    ))
                return creators
        except Exception:
            pass
        return self._mock_creators()

    def _mock_creators(self) -> list[Creator]:
        mock_channels = [
            "TechWithAlex", "CreativeMornings", "TravelTales",
            "FoodFusion", "FitnessFanatic", "MusicMakers",
        ]
        creators = []
        for i, name in enumerate(mock_channels):
            creators.append(Creator(
                id=f"yt_{i}",
                name=name,
                email=f"{name.lower()}@youtube.com",
                primary_niche=random.choice(["Technology", "Travel", "Food & Cooking", "Fitness & Wellness", "Music & Entertainment"]),
                primary_language="English",
                platforms={"youtube": PlatformInfo(handle=name, followers=random.randint(1000, 500000))},
                content_quality_score=round(random.uniform(5, 10), 1),
                profile_completeness=round(random.uniform(50, 100), 1),
                avg_engagement_rate=round(random.uniform(1, 8), 1),
                status=CreatorStatus.ACTIVE,
            ))
        return creators
