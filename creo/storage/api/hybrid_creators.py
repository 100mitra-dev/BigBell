"""BigBell hybrid creator repository — DB cache + JSON seed + external APIs.

Default search path:
  1. SQLite (`DbCreatorRepository`) — primary, always read.
  2. JSON seed (`JsonCreatorRepository`) — fills the DB on first run.
  3. External discovery (Meta Marketplace, Modash, Instagram, YouTube) —
     merged in, deduplicated, optionally synced into the DB.

Set DISCOVERY_SOURCES in `.env` to toggle, e.g.:
  DISCOVERY_SOURCES=db,json,meta,modash
"""
import hashlib
import logging

from creo.models import Creator
from creo.storage.base import CreatorRepository

logger = logging.getLogger(__name__)

_READ_ONLY_TYPES = frozenset({
    "MetaMarketplaceRepository",
    "ModashCreatorRepository",
    "InstagramCreatorRepository",
    "YouTubeCreatorRepository",
    "InstagramCampaignRepository",
    "WhatsAppPaymentRepository",
})


def _fingerprint(c: Creator) -> str:
    handle = ""
    if c.platforms:
        first = sorted(c.platforms.items())[0]
        handle = first[1].handle if first[1].handle else ""
    raw = f"{c.name.strip().lower()}|{handle.strip().lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


class HybridCreatorRepository(CreatorRepository):
    def __init__(self, sources: list[CreatorRepository] | None = None):
        self._sources: list[CreatorRepository] = sources or self._default_sources()
        self._db = self._find_db_source()

    def _default_sources(self) -> list[CreatorRepository]:
        try:
            from creo.utils.runtime_settings import get_discovery_sources
            wanted = get_discovery_sources()
        except Exception:
            wanted = ["db", "json", "meta", "modash"]
        sources: list[CreatorRepository] = []
        if "db" in wanted:
            try:
                from creo.storage.db import init_db
                from creo.storage.db.creator_repo import DbCreatorRepository
                init_db()
                sources.append(DbCreatorRepository())
            except Exception as exc:
                logger.warning("DB source unavailable: %s", exc)
        if "json" in wanted:
            try:
                from creo.storage.json.creator_repo import JsonCreatorRepository
                sources.append(JsonCreatorRepository())
            except Exception as exc:
                logger.warning("JSON source unavailable: %s", exc)
        if "meta" in wanted:
            try:
                from creo.storage.api.meta_marketplace import MetaMarketplaceRepository
                sources.append(MetaMarketplaceRepository())
            except Exception as exc:
                logger.warning("Meta source unavailable: %s", exc)
        if "modash" in wanted:
            try:
                from creo.storage.api.modash import ModashCreatorRepository
                sources.append(ModashCreatorRepository())
            except Exception as exc:
                logger.warning("Modash source unavailable: %s", exc)
        if "instagram" in wanted:
            try:
                from creo.storage.api.instagram_creators import (
                    InstagramCreatorRepository,
                )
                sources.append(InstagramCreatorRepository())
            except Exception as exc:
                logger.warning("Instagram source unavailable: %s", exc)
        if "youtube" in wanted:
            try:
                from creo.storage.api.youtube import YouTubeCreatorRepository
                sources.append(YouTubeCreatorRepository())
            except Exception as exc:
                logger.warning("YouTube source unavailable: %s", exc)
        if not sources:
            from creo.storage.json.creator_repo import JsonCreatorRepository
            sources = [JsonCreatorRepository()]
        return sources

    def _find_db_source(self) -> CreatorRepository | None:
        for s in self._sources:
            if getattr(s, "_is_writable", None) is True:
                return s
            if getattr(s, "_is_writable", None) is False:
                continue
            if type(s).__name__ in _READ_ONLY_TYPES:
                continue
            return s
        return None

    @property
    def sources(self) -> list[CreatorRepository]:
        return self._sources

    @property
    def source_names(self) -> list[str]:
        return [type(s).__name__ for s in self._sources]

    def list_all(self) -> list[Creator]:
        merged: dict[str, Creator] = {}
        for source in self._sources:
            try:
                creators = source.list_all() or []
            except Exception as exc:
                logger.warning("%s failed: %s", type(source).__name__, exc)
                continue
            for c in creators:
                key = _fingerprint(c)
                if key not in merged:
                    merged[key] = c
                else:
                    # Prefer the record with the richer audience signal.
                    if c.total_followers > merged[key].total_followers:
                        merged[key] = c
        result = sorted(merged.values(), key=lambda c: c.total_followers, reverse=True)
        # Opportunistically seed an empty DB so later searches hit SQLite.
        if self._db is not None and result:
            try:
                if not self._db.list_all():
                    self._db.save_all(result)
                    logger.info("Seeded creator DB with %d records", len(result))
            except Exception as exc:
                logger.debug("DB seed skipped: %s", exc)
        return result

    def get_by_id(self, creator_id: str) -> Creator | None:
        for source in self._sources:
            try:
                found = source.get_by_id(creator_id)
            except Exception:
                continue
            if found:
                return found
        return None

    def _writable(self) -> CreatorRepository:
        if self._db is not None:
            return self._db
        for s in self._sources:
            # Skip read-only API sources; only True for JSON/DB-backed repos.
            write_marker = getattr(s, "_is_writable", None)
            if write_marker is True:
                return s
            if write_marker is False:
                continue
            # Fallback for legacy sources without the marker: skip known read-only
            # API repo classes by declaring them in _READ_ONLY_TYPES.
            if type(s).__name__ in _READ_ONLY_TYPES:
                continue
            return s
        raise NotImplementedError("No writable creator source available")

    def add(self, creator: Creator):
        self._writable().add(creator)

    def delete(self, creator_id: str):
        self._writable().delete(creator_id)

    def save_all(self, creators: list[Creator]):
        self._writable().save_all(creators)

    def sync_external_to_db(self) -> dict:
        """Pull every non-DB source and upsert the merged pool into SQLite."""
        if self._db is None:
            return {"synced": 0, "status": "no-db-source"}
        # Capture existing IDs BEFORE list_all() triggers auto-seeding
        existing = {c.id for c in self._db.list_all()}
        merged = self.list_all()
        try:
            fresh = [c for c in merged if c.id not in existing]
            combined = self._db.list_all() + fresh
            # Re-merge by fingerprint to avoid duplicates on repeat syncs.
            dedup: dict[str, Creator] = {}
            for c in combined:
                dedup[_fingerprint(c)] = c
            self._db.save_all(list(dedup.values()))
            return {"synced": len(fresh), "total": len(dedup), "status": "ok"}
        except Exception as exc:
            logger.exception("sync_external_to_db failed")
            return {"synced": 0, "status": f"error: {exc}"}
