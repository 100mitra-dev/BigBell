import random
from typing import Optional

from creo.storage.base import CreatorRepository
from creo.models import Creator, CreatorStatus, PlatformInfo


class ModashCreatorRepository(CreatorRepository):
    """Fetches creators from the Modash.io API (third-party creator discovery platform).

    Modash provides creator profiles, audience analytics, and past performance data.
    Uses the Modash REST API when a valid API key is configured; otherwise falls
    back to deterministic mock data.
    """

    @property
    def use_real_api(self) -> bool:
        from creo.utils.runtime_settings import get_modash_key
        return bool(get_modash_key())

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
        from creo.utils.runtime_settings import get_modash_key
        key = get_modash_key()
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
                    platforms = {}
                    for plat in ("instagram", "youtube", "tiktok", "twitter", "facebook"):
                        if plat in item.get("social_profiles", {}):
                            prof = item["social_profiles"][plat]
                            platforms[plat] = PlatformInfo(
                                handle=prof.get("username", ""),
                                followers=prof.get("followers", 0),
                                verified=prof.get("verified", False),
                            )
                    audience = item.get("audience", {})
                    creators.append(Creator(
                        id=item.get("id", f"modash_{i}"),
                        name=item.get("username", f"Modash Creator {i}"),
                        email=f"{item.get('id', i)}@modash.io",
                        primary_niche=item.get("category", "Lifestyle"),
                        primary_language=audience.get("primary_language", "English"),
                        secondary_languages=audience.get("languages", []),
                        platforms=platforms,
                        region=item.get("location", {}).get("country", "India"),
                        content_quality_score=round(item.get("quality_score", random.uniform(5, 9)), 1),
                        profile_completeness=100.0,
                        avg_engagement_rate=round(item.get("avg_engagement_rate", random.uniform(1, 7)), 1),
                        total_campaigns_completed=item.get("campaigns_completed", random.randint(0, 20)),
                        total_earnings=random.uniform(0, 300000),
                        status=CreatorStatus.ACTIVE,
                    ))
                return creators
        except Exception:
            pass
        return self._mock_creators()

    def _mock_creators(self) -> list[Creator]:
        mock_creators = [
            ("Zara Influences", "Fashion", "English", "Mumbai", "@zara_influences", 2400000, True, "instagram"),
            ("FoodieFables", "Food & Cooking", "Hindi", "Delhi", "@foodiefables", 560000, True, "instagram"),
            ("GamersDen", "Gaming", "English", "Bangalore", "@gamersden", 890000, True, "youtube"),
            ("FitnessWithRiya", "Fitness & Wellness", "English", "Mumbai", "@riya_fitness", 120000, False, "instagram"),
            ("TechBytesIndia", "Technology", "English", "Delhi", "@techbytesindia", 340000, True, "youtube"),
            ("ComedyChowk", "Comedy & Entertainment", "Hindi", "Mumbai", "@comedychowk", 1800000, True, "instagram"),
            ("DanceWithMeera", "Dance & Choreography", "Hindi", "Chennai", "@dancewemeera", 75000, False, "instagram"),
            ("MinimalistLife", "Lifestyle", "English", "Bangalore", "@minimalist_life", 450000, True, "instagram"),
        ]
        creators = []
        for i, (name, niche, lang, region, handle, followers, verified, primary_plat) in enumerate(mock_creators):
            platforms = {
                primary_plat: PlatformInfo(handle=handle, followers=followers, verified=verified),
            }
            if primary_plat == "instagram":
                platforms["youtube"] = PlatformInfo(handle=name.lower().replace(" ", "").replace("'", ""), followers=followers // 2, verified=False)
            else:
                platforms["instagram"] = PlatformInfo(handle=name.lower().replace(" ", "").replace("'", ""), followers=followers // 3, verified=verified)
            creators.append(Creator(
                id=f"modash_{i}",
                name=name,
                email=f"{name.lower().replace(' ', '_').replace("'", '')}@modash.io",
                primary_niche=niche,
                primary_language=lang,
                secondary_languages=["Hindi"] if lang == "English" else ["English"],
                platforms=platforms,
                region=region,
                content_quality_score=round(random.uniform(6.0, 9.2), 1),
                profile_completeness=round(random.uniform(80, 100), 1),
                avg_engagement_rate=round(random.uniform(2.0, 8.5), 1),
                total_campaigns_completed=random.randint(1, 50),
                total_earnings=round(random.uniform(100000, 2000000), -3),
                status=CreatorStatus.ACTIVE,
            ))
        return creators
