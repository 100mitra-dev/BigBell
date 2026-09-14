from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from creo.services.creator_service import CreatorService, CreatorSearchQuery

router = APIRouter()


@lru_cache(maxsize=1)
def get_cs() -> CreatorService:
    return CreatorService()


@router.get("/")
def list_creators(status: Optional[str] = None, niche: Optional[str] = None):
    creators = get_cs().creators
    if status:
        creators = [c for c in creators if c.status.value == status]
    if niche:
        creators = [c for c in creators if c.primary_niche == niche or niche in c.secondary_niches]
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "primary_niche": c.primary_niche,
            "primary_language": c.primary_language,
            "status": c.status.value,
            "tier": c.tier,
            "total_followers": c.total_followers,
            "engagement_rate": c.avg_engagement_rate,
        }
        for c in creators
    ]


@router.get("/search")
def search_creators(
    q: str = "",
    niche: Optional[str] = None,
    language: Optional[str] = None,
    region: Optional[str] = None,
    min_followers: Optional[int] = None,
    min_engagement: Optional[float] = None,
    verified_only: bool = False,
    tier: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: str = "followers",
    sort_desc: bool = True,
    page: int = 1,
    page_size: int = 50,
):
    query = CreatorSearchQuery(
        niche=niche,
        language=language,
        region=region,
        min_followers=min_followers,
        min_engagement=min_engagement,
        verified_only=verified_only,
        tier=tier,
        sort_by=sort_by,
        sort_desc=sort_desc,
        page=page,
        page_size=page_size,
    )
    result = get_cs().advanced_search(query)
    if q:
        result.items = [
            c for c in result.items
            if q.lower() in c.name.lower()
            or q.lower() in c.email.lower()
            or (q.lower().startswith("@") and q.lower() in [h.lower() for h in c.handles.values()])
        ]
        result.total = len(result.items)
        result.total_pages = 1
    if source:
        # Filter by source based on ID prefix
        if source == "meta":
            result.items = [c for c in result.items if c.id.startswith("meta_")]
        elif source == "modash":
            result.items = [c for c in result.items if c.id.startswith("modash_")]
        elif source == "youtube":
            result.items = [c for c in result.items if c.id.startswith("yt_") or c.id.startswith("youtube_")]
        elif source == "instagram":
            result.items = [c for c in result.items if c.id.startswith("ig_") or c.id.startswith("instagram_")]
        elif source == "db":
            result.items = [c for c in result.items if not any(c.id.startswith(p) for p in ["meta_", "modash_", "yt_", "youtube_", "ig_", "instagram_"])]
        result.total = len(result.items)
        result.total_pages = 1
    return {
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "total_pages": result.total_pages,
        "items": [{**c.to_card_dict(), "source": _infer_source(c.id)} for c in result.items],
    }


def _infer_source(creator_id: str) -> str:
    if creator_id.startswith("meta_"):
        return "meta"
    if creator_id.startswith("modash_"):
        return "modash"
    if creator_id.startswith("yt_") or creator_id.startswith("youtube_"):
        return "youtube"
    if creator_id.startswith("ig_") or creator_id.startswith("instagram_"):
        return "instagram"
    return "db"


@router.get("/facets")
def get_facets():
    return get_cs().facet_values()


@router.get("/{creator_id}")
def get_creator(creator_id: str):
    creator = get_cs().get_by_id(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    return creator.model_dump()
