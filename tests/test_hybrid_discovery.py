"""BigBell hybrid discovery + REST API tests — mocked, no network."""
from fastapi.testclient import TestClient

from creo.models import Creator, CreatorStatus, PlatformInfo
from creo.storage.api.hybrid_creators import HybridCreatorRepository
from creo.storage.api.meta_config import (
    get_meta_endpoint,
    get_meta_timeout,
    meta_status,
)


def _c(id, name, followers, niche="Gaming"):
    return Creator(
        id=id, name=name, email=f"{id}@t.com", primary_niche=niche,
        primary_language="English",
        platforms={"instagram": PlatformInfo(handle="@" + id, followers=followers)},
        region="Delhi", status=CreatorStatus.ACTIVE,
    )


class FakeRepo:
    def __init__(self, items, writable=True):
        self._items = list(items)
        self.writable = writable

    def list_all(self):
        return list(self._items)

    def get_by_id(self, cid):
        for c in self._items:
            if c.id == cid:
                return c
        return None

    def add(self, c):
        if not self.writable:
            raise NotImplementedError("read-only")
        self._items.append(c)

    def delete(self, cid):
        if not self.writable:
            raise NotImplementedError("read-only")
        self._items = [c for c in self._items if c.id != cid]

    def save_all(self, creators):
        if not self.writable:
            raise NotImplementedError("read-only")
        self._items = list(creators)


class FailingRepo:
    def list_all(self):
        raise RuntimeError("provider down")

    def get_by_id(self, cid):
        raise RuntimeError("provider down")

    def add(self, c):
        raise NotImplementedError("read-only")

    def delete(self, cid):
        raise NotImplementedError("read-only")

    def save_all(self, creators):
        raise NotImplementedError("read-only")


def test_hybrid_dedups_and_prefers_richer_record():
    from creo.models import PlatformInfo as _PI
    db = FakeRepo([Creator(id="CRE-1", name="Ananya Roy", email="a@t.com", primary_niche="Fashion",
                           primary_language="English", region="Delhi", status=CreatorStatus.ACTIVE,
                           platforms={"instagram": _PI(handle="@ananya", followers=100)})])
    meta = FakeRepo([Creator(id="meta_9", name="Ananya Roy", email="a@meta.com", primary_niche="Fashion",
                             primary_language="English", region="Delhi", status=CreatorStatus.ACTIVE,
                             platforms={"instagram": _PI(handle="@ananya", followers=750_000)})],
                    writable=False)  # same name+handle fingerprint
    hybrid = HybridCreatorRepository(sources=[db, meta])
    merged = hybrid.list_all()
    assert len(merged) == 1
    assert merged[0].total_followers == 750_000


def test_hybrid_survives_failing_source():
    hybrid = HybridCreatorRepository(sources=[FailingRepo(), FakeRepo([_c("CRE-2", "Solo", 10)])])
    assert [c.id for c in hybrid.list_all()] == ["CRE-2"]
    assert hybrid.get_by_id("CRE-2").name == "Solo"
    assert hybrid.get_by_id("missing") is None


def test_sync_external_to_db():
    db = FakeRepo([])
    hybrid = HybridCreatorRepository(sources=[db, FakeRepo([_c("meta_1", "Ext One", 50)], writable=False)])
    out = hybrid.sync_external_to_db()
    assert out["status"] == "ok" and out["synced"] == 1
    assert {c.id for c in db.list_all()} == {"meta_1"}


def test_sync_without_db():
    hybrid = HybridCreatorRepository(sources=[FakeRepo([_c("x", "X", 1)], writable=False)])
    hybrid._db = None
    assert hybrid.sync_external_to_db()["status"] == "no-db-source"


def test_meta_config_helpers(monkeypatch):
    monkeypatch.setenv("META_API_BASE_URL", "https://graph.facebook.com")
    monkeypatch.setenv("META_API_VERSION", "v19.0")
    assert get_meta_endpoint("creator_marketplace/creators").endswith("v19.0/creator_marketplace/creators")
    assert get_meta_timeout() >= 1
    status = meta_status()
    assert status["provider"] == "meta_creator_marketplace"
    assert "endpoint" in status and "configured" in status


def _client(monkeypatch):
    from creo.services.creator_service import CreatorService
    items = [
        _c("CRE-1", "Ananya Roy", 750_000, niche="Fashion"),
        _c("meta_1", "Meta Star", 320_000, niche="Gaming"),
    ]
    monkeypatch.setattr(CreatorService, "_make_repo", lambda self: FakeRepo(items))
    monkeypatch.setattr(CreatorService, "refresh", lambda self: setattr(self, "_items", list(items)))
    from api.main import app
    return TestClient(app)


def test_search_api_filters_and_source(monkeypatch):
    client = _client(monkeypatch)
    r = client.get("/api/v1/creators/search", params={"q": "ananya"})
    assert r.status_code == 200 and r.json()["total"] == 1
    r = client.get("/api/v1/creators/search", params={"niche": "Gaming", "source": "meta"})
    body = r.json()
    assert body["total"] >= 1 and all(i["source"] == "meta" for i in body["items"])
    assert "handles" in body["items"][0] and "languages" in body["items"][0]


def test_facets_detail_and_404(monkeypatch):
    client = _client(monkeypatch)
    assert "niches" in client.get("/api/v1/creators/facets").json()
    assert client.get("/api/v1/creators/CRE-1").json()["id"] == "CRE-1"
    assert client.get("/api/v1/creators/nope").status_code == 404


def test_discovery_status_sync_and_config(monkeypatch):
    from creo.utils import runtime_settings as rs
    monkeypatch.setattr(rs, "persist_config", lambda: True)  # no disk writes in tests
    monkeypatch.setenv("ADMIN_KEY", "test-admin-key-123")
    rs.update_from_env()
    client = _client(monkeypatch)
    assert "meta" in client.get("/api/v1/discovery/status").json()
    r = client.put("/api/v1/discovery/config", json={"meta_marketplace_key": "tok123", "meta_api_version": "v19.0"}, headers={"X-Admin-Key": "test-admin-key-123"})
    assert r.status_code == 200 and "meta_marketplace_key" in r.json()["applied"]
    assert r.json()["persisted"] is True
    rs._RUNTIME_CONFIG.pop("meta_marketplace_key", None)
    rs._RUNTIME_CONFIG["meta_api_version"] = "v19.0"
