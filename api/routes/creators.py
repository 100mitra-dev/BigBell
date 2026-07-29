from fastapi import APIRouter, HTTPException

from creo.services.creator_service import CreatorService

router = APIRouter()
cs = CreatorService()


@router.get("/")
def list_creators(status: str = None, niche: str = None):
    creators = cs.creators
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


@router.get("/{creator_id}")
def get_creator(creator_id: str):
    creator = cs.get_by_id(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    return creator.model_dump()
