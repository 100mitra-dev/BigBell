"""Meta creator discovery: filter normalization, live Meta Creator Marketplace API call, deterministic mock fallback."""
import logging
import random
from dataclasses import dataclass, field

from creo.config import (
    CONTENT_TYPES,
    AUDIENCE_TYPES,
    SORT_OPTIONS,
    PLATFORM_OPTIONS,
    LANGUAGE_CODES,
    lang_to_code,
)

logger = logging.getLogger(__name__)

DEFAULT_PLATFORM = "instagram"
DEFAULT_CONTENT_TYPE = "ALL"
DEFAULT_AUDIENCE_TYPE = "ALL"
DEFAULT_SORT = "relevance"


@dataclass
class DiscoveryFilters:
    niche: str = ""
    language: str = ""
    region: str = ""
    min_followers: int = 0
    max_followers: int = 0
    platform: str = DEFAULT_PLATFORM
    limit: int = 20
    search_query: str = ""
    content_type: str = DEFAULT_CONTENT_TYPE
    audience_type: str = DEFAULT_AUDIENCE_TYPE
    sort_by: str = DEFAULT_SORT


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
    ("Sofia Rossi", "sofia.rossi", "Beauty & Makeup", "Italian", "IT", 240000, 4.1),
    ("Liam Carter", "liamcarterfit", "Fitness & Wellness", "English", "US", 120000, 2.8),
    ("Priya Nair", "priya.cooks", "Food & Cooking", "Malayalam", "IN-KL", 45000, 5.4),
    ("Diego Santos", "diego.tech", "Technology", "Spanish", "BR", 310000, 2.1),
    ("Amara Okafor", "amara.travels", "Travel", "English", "NG", 67000, 3.9),
    ("Yuki Tanaka", "yuki.gaming", "Gaming", "Japanese", "JP", 520000, 3.5),
    ("Emma Wilson", "emma.lifestyle", "Lifestyle", "English", "UK", 15000, 6.2),
    ("Raj Patel", "raj.edits", "Technology", "Hindi", "IN-GJ", 220000, 4.8),
    ("Maria Silva", "maria.beauty", "Beauty & Makeup", "Portuguese", "BR", 98000, 5.1),
    ("Chen Wei", "chen.travel", "Travel", "Mandarin", "CN", 180000, 3.0),
    ("Omar Khalid", "omar.comedy", "Comedy & Entertainment", "Arabic", "EG", 55000, 7.1),
    ("Zoe Kim", "zoe.fitness", "Fitness & Wellness", "Korean", "KR", 110000, 4.3),
    ("Noah Brown", "noah.music", "Music & Entertainment", "English", "US", 420000, 2.6),
    ("Isla Martinez", "isla.parenting", "Parenting", "Spanish", "ES", 78000, 5.7),
    ("Fatima Ali", "fatima.food", "Food & Cooking", "Urdu", "PK", 35000, 4.9),
]


def apply_filters(pool: list[DiscoveredCreator], f: DiscoveryFilters) -> list[DiscoveredCreator]:
    out = pool
    if f.search_query:
        sq = f.search_query.lower()
        out = [c for c in out if sq in c.name.lower() or sq in c.handle.lower() or sq in c.niche.lower()]
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
    if f.platform and f.platform != "all":
        out = [c for c in out if c.platform.lower() == f.platform.lower()]
    if f.content_type and f.content_type != "ALL":
        ct = f.content_type.lower()
        out = [c for c in out if c.extra.get("content_type", "").lower() == ct]
    if f.audience_type and f.audience_type != "ALL":
        at = f.audience_type.lower()
        out = [c for c in out if c.extra.get("audience_type", "").lower() == at]
    if f.sort_by == "followers":
        out.sort(key=lambda c: c.followers, reverse=True)
    elif f.sort_by == "engagement_rate":
        out.sort(key=lambda c: c.engagement_rate, reverse=True)
    elif f.sort_by == "relevance":
        out.sort(key=lambda c: (c.followers * c.engagement_rate), reverse=True)
    return out[: f.limit]


def mock_discover(f: DiscoveryFilters) -> list[DiscoveredCreator]:
    rng = random.Random(hash((f.niche, f.language, f.region, f.platform, f.search_query)) & 0xFFFFFFFF)
    pool = []
    for name, handle, ni, la, re, fo, en in _MOCK_NAMES:
        followers = fo + rng.randint(-5000, 5000)
        pool.append(DiscoveredCreator(
            name=name, handle=f"@{handle}", niche=ni, language=la, region=re,
            followers=max(0, followers), engagement_rate=en,
            platform=f.platform,
            profile_url=f"https://instagram.com/{handle}",
            extra={"content_type": rng.choice(CONTENT_TYPES), "audience_type": rng.choice(AUDIENCE_TYPES)},
        ))
    if not (f.niche and f.niche != "All") and not (f.language and f.language != "All") and not f.region and not f.min_followers and not f.max_followers and not f.search_query and (not f.content_type or f.content_type == "ALL") and (not f.audience_type or f.audience_type == "ALL"):
        return pool[: f.limit]
    result = apply_filters(pool, f)
    return result if result else pool[: min(3, f.limit)]


def live_discover(f: DiscoveryFilters, api_key: str = "", api_token: str = "") -> list[DiscoveredCreator]:
    """Call Meta Creator Marketplace API. Raises on failure so caller falls back to mock."""
    token = api_token or api_key
    if not token:
        raise ValueError("Missing Meta API credentials")

    from creo.storage.api.meta_config import get_meta_endpoint, get_meta_timeout

    params = {
        "access_token": token,
        "limit": min(f.limit, 100),
        "platform": f.platform.upper() if f.platform else "INSTAGRAM",
    }

    if f.search_query:
        params["q"] = f.search_query
    if f.niche and f.niche != "All":
        params["category"] = f.niche
    if f.min_followers:
        params["followers_min"] = f.min_followers
    if f.max_followers:
        params["followers_max"] = f.max_followers
    if f.content_type and f.content_type != "ALL":
        params["content_type"] = f.content_type
    if f.audience_type and f.audience_type != "ALL":
        params["audience_type"] = f.audience_type
    if f.sort_by:
        params["sort_by"] = f.sort_by
    if f.region:
        params["region"] = f.region
    if f.language and f.language != "All":
        code = lang_to_code(f.language)
        if code:
            params["language"] = code

    import requests

    endpoint = get_meta_endpoint("creator_marketplace/creators")
    resp = requests.get(endpoint, params=params, timeout=get_meta_timeout())
    resp.raise_for_status()
    data = resp.json().get("data", [])
    results = []
    for i, item in enumerate(data):
        ig = item.get("instagram", {}) or {}
        handle = ig.get("username", item.get("username", f"creator_{i}"))
        results.append(DiscoveredCreator(
            name=item.get("name", handle or f"Creator {i}"),
            handle="@" + handle,
            niche=item.get("category", f.niche or "General"),
            language=f.language or item.get("language", "English"),
            region=f.region or item.get("location", item.get("region", "")),
            followers=int(item.get("followers_count", item.get("followers", 0))),
            engagement_rate=float(item.get("engagement_rate", 0.0)),
            platform=f.platform,
            profile_url=item.get("profile_url", ig.get("profile_url", "")),
            verified=bool(item.get("is_verified", item.get("verified", False))),
            extra=item,
        ))
    return apply_filters(results, f)
