"""BigBell Meta API configuration — single place to add/rotate the Meta key.

Add your key in any of these ways (first non-empty wins):
  1. `.env`: META_MARKETPLACE_API_KEY='<token>'
  2. Settings UI / PUT /api/v1/discovery/config {"meta_marketplace_key": "<token>"}
  3. Env var META_MARKETPLACE_API_KEY

Optional overrides in `.env`:
  META_API_BASE_URL=https://graph.facebook.com
  META_API_VERSION=v19.0
  META_API_TIMEOUT_S=10
  META_API_PAGE_LIMIT=100
"""
import os


def get_meta_endpoint(path: str) -> str:
    try:
        from creo.utils.runtime_settings import (
            get_meta_api_base_url,
            get_meta_api_version,
        )
        base = (get_meta_api_base_url() or "https://graph.facebook.com").rstrip("/")
        version = (get_meta_api_version() or "v19.0").strip().strip("/")
    except Exception:
        base = os.getenv("META_API_BASE_URL", "https://graph.facebook.com").rstrip("/")
        version = os.getenv("META_API_VERSION", "v19.0").strip().strip("/")
    path = path.strip().lstrip("/")
    return f"{base}/{version}/{path}"


def get_meta_timeout() -> int:
    try:
        from creo import config as cfg
        return int(getattr(cfg, "META_API_TIMEOUT_S", 10))
    except Exception:
        return int(os.getenv("META_API_TIMEOUT_S", "10"))


def get_meta_page_limit() -> int:
    try:
        from creo import config as cfg
        return int(getattr(cfg, "META_API_PAGE_LIMIT", 100))
    except Exception:
        return int(os.getenv("META_API_PAGE_LIMIT", "100"))


def meta_status() -> dict:
    """Non-secret status for the discovery UI (never returns the key)."""
    try:
        from creo.utils.runtime_settings import get_meta_marketplace_key
        configured = bool(get_meta_marketplace_key())
    except Exception:
        configured = bool(os.getenv("META_MARKETPLACE_API_KEY", ""))
    return {
        "provider": "meta_creator_marketplace",
        "configured": configured,
        "endpoint": get_meta_endpoint("creator_marketplace/creators"),
        "timeout_s": get_meta_timeout(),
        "page_limit": get_meta_page_limit(),
    }
