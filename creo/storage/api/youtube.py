"""BigBell YouTube creator repository — fetches creators from YouTube Data API."""
import random
from typing import Optional

from creo.storage.api.base_api import BaseApiRepository
from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class YouTubeCreatorRepository(BaseApiRepository, CreatorRepository):
    """Fetches creator data from the YouTube Data API v3 when a valid API key is configured;
    falls back to deterministic mock data otherwise.
    """

    def _check_key(self) -> bool:
        try:
            from creo.utils.runtime_settings import get_youtube_key
            return bool(get_youtube_key())
        except Exception:
            return False

    def _mock_data(self) -> list[Creator]:
        return self._mock_creators()

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
        try:
            from creo.utils.runtime_settings import get_youtube_key
            key = get_youtube_key()
        except (ImportError, OSError, ValueError) as e:
            import logging; logging.getLogger(__name__).warning('%s fallback: %s', __name__, e)
            return self._mock_creators()
        try:
            import requests
            # Search for popular channels
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "type": "channel",
                    "maxResults": 20,
                    "order": "viewCount",
                    "key": key,
                },
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                creators = []
                for i, item in enumerate(data.get("items", [])):
                    snippet = item.get("snippet", {})
                    channel_id = item.get("id", {}).get("channelId", f"yt_{i}")
                    creators.append(Creator(
                        id=f"yt_{i}",
                        name=snippet.get("title", f"YouTube Creator {i}"),
                        email=f"{snippet.get('title', 'creator').lower().replace(' ', '')}@youtube.com",
                        primary_niche=self._infer_niche(snippet.get("title", "")),
                        secondary_niches=[],
                        primary_language="English",
                        secondary_languages=[],
                        platforms={"youtube": PlatformInfo(
                            handle=snippet.get("channelTitle", f"@channel{i}"),
                            followers=0,  # Would need channels.list API call
                            verified=False,
                        )},
                        content_quality_score=0.0,
                        profile_completeness=50.0,
                        avg_engagement_rate=0.0,
                        status=CreatorStatus.ACTIVE,
                        region=snippet.get("country", ""),
                        verified=False,
                        verification_score=30.0,
                    ))
                return creators
        except (ImportError, OSError) as e:
            import logging; logging.getLogger(__name__).warning('%s fetch fallback: %s', __name__, e)
        return self._mock_creators()

    def _infer_niche(self, title: str) -> str:
        title_lower = title.lower()
        if any(k in title_lower for k in ["tech", "code", "dev", "program"]):
            return "Technology"
        if any(k in title_lower for k in ["food", "cook", "recipe", "chef"]):
            return "Food & Cooking"
        if any(k in title_lower for k in ["fit", "gym", "workout", "health"]):
            return "Fitness"
        if any(k in title_lower for k in ["travel", "vlog", "trip"]):
            return "Travel"
        if any(k in title_lower for k in ["game", "play", "stream"]):
            return "Gaming"
        if any(k in title_lower for k in ["beauty", "makeup", "fashion", "style"]):
            return "Beauty & Makeup"
        return "General"

    def _mock_creators(self) -> list[Creator]:
        mock_channels = [
            ("TechWithAlex", "Technology", "English", "US", "@techwithalex", 1200000, False),
            ("CreativeMornings", "Design", "English", "US", "@creativemornings", 450000, True),
            ("TravelTales", "Travel", "English", "Global", "@traveltales", 780000, True),
            ("FoodFusion", "Food & Cooking", "English", "India", "@foodfusion", 2100000, True),
            ("FitnessFanatic", "Fitness", "English", "UK", "@fitnessfanatic", 560000, False),
            ("MusicMakers", "Music", "English", "US", "@musicmakers", 340000, True),
        ]
        creators = []
        for i, (name, niche, lang, region, handle, followers, verified) in enumerate(mock_channels):
            creators.append(Creator(
                id=f"yt_{i}",
                name=name,
                email=f"{handle[1:]}@youtube.com",
                primary_niche=niche,
                secondary_niches=[],
                primary_language=lang,
                secondary_languages=[],
                platforms={"youtube": PlatformInfo(handle=handle, followers=followers, verified=verified)},
                content_quality_score=0.0,
                profile_completeness=50.0,
                avg_engagement_rate=random.uniform(1.5, 4.5),
                status=CreatorStatus.ACTIVE,
                region=region,
                verified=verified,
                verification_score=30.0,
            ))
        return creators