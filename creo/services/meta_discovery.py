"""Meta creator discovery: filter normalization, live API call, deterministic mock fallback."""
import logging
import random
from dataclasses import dataclass, field

import requests

from creo.config import META_API_BASE_URL

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryFilters:
    niche: str = ""
    language: str = ""
    region: str = ""
    min_followers: int = 0
    max_followers: int = 0  # 0 = no upper bound
    platform: str = "instagram"
    limit: int = 20


@dataclass
class DiscoveredCreator:
    name: str
    handle: str
    niche: str
    language: str
    region: str
    followers: int
    engagement_rate: float
    platform: str
    profile_url: str = ""
    verified: bool = False
    extra: dict = field(default_factory=dict)


_MOCK_NAMES = [
    ("Aarav Mehta", "aarav.creates", "Fashion", "Hindi", "IN-MH", 85000, 3.2),
    ("Sofia Rossi", "sofia.rossi", "Beauty", "Italian", "IT", 240000, 4.1),
    ("Liam Carter", "liamcarterfit", "Fitness", "English", "US", 120000, 2.8),
    ("Priya Nair", "priya.cooks", "Food", "Malayalam", "IN-KL", 45000, 5.4),
    ("Diego Santos", "diego.tech", "Tech", "Spanish", "BR", 310000, 2.1),
    ("Amara Okafor", "amara.travels", "Travel", "English", "NG", 67000, 3.9),
    ("Yuki Tanaka", "yuki.gaming", "Gaming", "Japanese", "JP", 520000, 3.5),
    ("Emma Wilson", "emma.lifestyle", "Lifestyle", "English", "UK", 15000, 6.2),
]


def apply_filters(pool: list[DiscoveredCreator], f: DiscoveryFilters) -> list[DiscoveredCreator]:
    out = pool
    if f.niche and f.niche != "All":
        out = [c for c in out if c.niche.lower() == f.niche.lower()]
    if f.language and f.language != "All":
        out = [c for c in out if c.language.lower() == f.language.lower()]
    if f.region:
        out = [c for c in out if f.region.lower() in c.region.lower()]
    if f.min_followers:
        out = [c for c in out if c.followers >= f.min_followers]
    if f.max_followers:
        out = [c for c in out if c.followers <= f.max_followers]
    return out[: f.limit]


def mock_discover(f: DiscoveryFilters) -> list[DiscoveredCreator]:
    rng = random.Random(hash((f.niche, f.language, f.region, f.platform)) & 0xFFFFFFFF)
    pool = [
        DiscoveredCreator(
            name=n, handle=f"@{h}", niche=ni, language=la, region=re,
            followers=fo + rng.randint(-5000, 5000), engagement_rate=en,
            platform=f.platform, profile_url=f"https://instagram.com/{h}",
        )
        for n, h, ni, la, re, fo, en in _MOCK_NAMES
    ]
    # If no attribute filters, return a slice so the tab is never empty.
    if not f.niche and not f.language and not f.region and not f.min_followers and not f.max_followers:
        return pool[: f.limit]
    result = apply_filters(pool, f)
    return result if result else pool[: min(3, f.limit)]


def live_discover(f: DiscoveryFilters, api_key: str = "", api_token: str = "") -> list[DiscoveredCreator]:
    """Call Meta Graph API creator search. Raises on failure so caller falls back to mock."""
    token = api_token or api_key
    if not token:
        raise ValueError("Missing Meta API credentials")
    params = {
        "access_token": token,
        "q": f.niche or "creator",
        "limit": min(f.limit, 50),
    }
    if f.region:
        params["region"] = f.region
    resp = requests.get(f"{META_API_BASE_URL}/creator_discovery", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    results = []
    for item in data:
        results.append(DiscoveredCreator(
            name=item.get("name", item.get("username", "Unknown")),
            handle="@ spont" + item.get("username", ""),
            niche=f.niche or item.get("category", "General"),
            language=f.language or "English",
            region=f.region or "",
            followers=int(item.get("followers_count", 0)),
            engagement_rate=float(item.get("engagement_rate", 0.0)),
            platform=f.platform,
            profile_url=item.get("profile_url", ""),
            verified=bool(item.get("is_verified", False)),
            extra=item,
        ))
    return apply_filters(results, f)
