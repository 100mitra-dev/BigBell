"""BigBell discovery config API — add/rotate provider keys without editing files.

PUT /api/v1/discovery/config {"meta_marketplace_key": "...", "modash_key": "..."}
GET /api/v1/discovery/status  -> source availability (no secrets echoed)
POST /api/v1/discovery/sync   -> pull external discovery into the SQLite cache
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class DiscoveryConfigUpdate(BaseModel):
    meta_marketplace_key: str | None = None
    modash_key: str | None = None
    youtube_key: str | None = None
    instagram_key: str | None = None
    whatsapp_key: str | None = None
    meta_api_base_url: str | None = None
    meta_api_version: str | None = None
    data_source: str | None = None
    discovery_sources: list[str] | None = None


@router.get("/status")
def discovery_status():
    from creo.storage.factories import get_discovery_status
    return get_discovery_status()


@router.put("/config")
def update_discovery_config(update: DiscoveryConfigUpdate):
    from creo.utils import runtime_settings as rs

    applied: list[str] = []
    if update.meta_marketplace_key is not None:
        rs.set_meta_marketplace_key(update.meta_marketplace_key.strip())
        applied.append("meta_marketplace_key")
    if update.modash_key is not None:
        rs.set_modash_key(update.modash_key.strip())
        applied.append("modash_key")
    if update.youtube_key is not None:
        rs.set_youtube_key(update.youtube_key.strip())
        applied.append("youtube_key")
    if update.instagram_key is not None:
        rs.set_instagram_key(update.instagram_key.strip())
        applied.append("instagram_key")
    if update.whatsapp_key is not None:
        rs.set_whatsapp_key(update.whatsapp_key.strip())
        applied.append("whatsapp_key")
    if update.meta_api_base_url is not None:
        rs.set_meta_api_base_url(update.meta_api_base_url)
        applied.append("meta_api_base_url")
    if update.meta_api_version is not None:
        rs.set_meta_api_version(update.meta_api_version)
        applied.append("meta_api_version")
    if update.data_source is not None:
        rs.set_data_source(update.data_source.strip().lower())
        applied.append("data_source")
    if update.discovery_sources is not None:
        rs.set_discovery_sources(update.discovery_sources)
        applied.append("discovery_sources")
    try:
        rs.persist_config()
        persisted = True
    except Exception as exc:
        logger.warning("persist_config failed: %s", exc)
        persisted = False
    logger.info("Discovery config updated: %s", ",".join(applied))
    return {"applied": applied, "persisted": persisted}


@router.post("/sync")
def sync_discovery():
    from creo.storage.factories import get_creator_repo
    repo = get_creator_repo()
    sync = getattr(repo, "sync_external_to_db", None)
    if sync is None:
        return {"synced": 0, "status": "repo does not support sync"}
    return sync()
