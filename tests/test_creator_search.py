"""BigBell creator-search tests — all mock data, no network, no real DB."""
import pytest

from creo.models import Creator, CreatorStatus, PlatformInfo
from creo.services.creator_service import CreatorSearchQuery, CreatorService


def _c(id, name, niche, lang, region, followers, eng, tier_plain=False, **kw):
    plats = kw.pop("platforms", {"instagram": PlatformInfo(handle="@" + id, followers=followers, verified=kw.pop("verified", False))})
    return Creator(
        id=id, name=name, email=f"{id}@test.com",
        primary_niche=niche, primary_language=lang,
        platforms=plats, avg_engagement_rate=eng,
        region=region, status=kw.pop("status", CreatorStatus.ACTIVE), **kw,
    )


@pytest.fixture
def mock_creators():
    return [
        _c("a1", "Ananya Roy", "Fashion", "English", "Delhi", 750_000, 5.5, verified=True),
        _c("a2", "Rahul Kitchen", "Food & Cooking", "Hindi", "Mumbai", 320_000, 3.0),
        _c("a3", "Gamer Zone", "Gaming", "English", "Bangalore", 180_000, 6.5,
            secondary_niches=["Technology"], secondary_languages=["Hindi"]),
        _c("a4", "Tiny Dancer", "Dance & Choreography", "Tamil", "Chennai", 5_000, 1.0,
            status=CreatorStatus.PENDING),
    ]


class _StubRepo:
    def __init__(self):
        self.saved = None

    def save_all(self, creators):
        self.saved = list(creators)


@pytest.fixture
def service(mock_creators):
    svc = CreatorService.__new__(CreatorService)
    from creo.services.base import CachedRepositoryService
    CachedRepositoryService.__init__(svc)
    svc._items = mock_creators
    svc.repo = _StubRepo()  # never touch the real DB from unit tests
    return svc


def test_text_search_matches_handle_and_region(service):
    assert [c.id for c in service.search("ananya")] == ["a1"]
    assert [c.id for c in service.search("@a3")] == ["a3"]
    assert [c.id for c in service.search("chennai")] == ["a4"]
    assert len(service.search("")) == 4


def test_advanced_niche_language_region(service):
    q = CreatorSearchQuery(niche="gaming")
    assert [c.id for c in service.advanced_search(q).items] == ["a3"]
    q = CreatorSearchQuery(niche="technology")  # secondary niche
    assert [c.id for c in service.advanced_search(q).items] == ["a3"]
    q = CreatorSearchQuery(language="hindi")  # primary + secondary
    assert {c.id for c in service.advanced_search(q).items} == {"a2", "a3"}
    q = CreatorSearchQuery(region="delhi")
    assert [c.id for c in service.advanced_search(q).items] == ["a1"]
    q = CreatorSearchQuery(region="mum")  # substring
    assert [c.id for c in service.advanced_search(q).items] == ["a2"]


def test_tier_and_threshold_filters(service):
    assert [c.id for c in service.advanced_search(CreatorSearchQuery(tier="elite")).items] == ["a1"]
    q = CreatorSearchQuery(min_followers=200_000)
    assert {c.id for c in service.advanced_search(q).items} == {"a1", "a2"}
    q = CreatorSearchQuery(min_engagement=5.0)
    assert {c.id for c in service.advanced_search(q).items} == {"a1", "a3"}
    q = CreatorSearchQuery(verified_only=True)
    assert [c.id for c in service.advanced_search(q).items] == ["a1"]


def test_sort_and_pagination(service):
    q = CreatorSearchQuery(sort_by="engagement", sort_desc=True, page_size=10)
    assert [c.id for c in service.advanced_search(q).items] == ["a3", "a1", "a2", "a4"]
    q = CreatorSearchQuery(sort_by="name", sort_desc=False, page_size=2, page=2)
    res = service.advanced_search(q)
    assert res.total == 4 and res.total_pages == 2 and len(res.items) == 2
    q = CreatorSearchQuery(sort_by="bogus")  # falls back to followers
    assert service.advanced_search(q).items[0].id == "a1"


def test_facets_and_card_payload(service):
    facets = service.facet_values()
    assert facets["niches"]["Fashion"] == 1
    assert facets["regions"]["Delhi"] == 1
    assert facets["tiers"]["Elite"] == 1
    card = service.get_by_id("a1").to_card_dict()
    for key in ("languages", "niches", "regions", "handles", "followers_by_platform",
                "total_followers", "total_subscribers", "engagement_rate", "display_region", "tier"):
        assert key in card
    assert card["languages"] == ["English"]
    assert card["handles"] == {"instagram": "@a1"}
    assert card["total_followers"] == 750_000


def test_update_status_missing_and_clamp(service):
    assert service.update_status("nope", CreatorStatus.ACTIVE) is False
    assert service.update_profile_completeness("nope", 50.0) is False
    assert service.update_status("a4", CreatorStatus.ACTIVE) is True
    assert service.get_by_id("a4").status == CreatorStatus.ACTIVE
    assert service.update_profile_completeness("a4", 150.0) is True
    assert service.get_by_id("a4").profile_completeness == 100.0


def test_random_pending_seeded(service):
    first = [c.id for c in service.get_random_pending(count=5, seed=42)]
    second = [c.id for c in service.get_random_pending(count=5, seed=42)]
    assert first == second
