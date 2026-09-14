"""BigBell campaigns REST API — list, detail, creator matches."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from creo.services.campaign_service import CampaignService
from creo.services.creator_service import CreatorService, CreatorSearchQuery

logger = logging.getLogger(__name__)
router = APIRouter()


def _card(c) -> dict:
    try:
        return c.model_dump()
    except AttributeError:
        return dict(c)


@router.get("/")
def list_campaigns(status: Optional[str] = None, q: str = Query(default="")):
    cs = CampaignService()
    campaigns = cs.search(q) if q else cs.campaigns
    if status:
        campaigns = [c for c in campaigns if c.status == status.lower()]
    return [_card(c) for c in campaigns]


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str):
    campaign = CampaignService().get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _card(campaign)


@router.get("/{campaign_id}/matches")
def campaign_matches(campaign_id: str, limit: int = Query(default=10, ge=1, le=50)):
    cs = CampaignService()
    campaign = cs.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    svc = CreatorService()
    scored: list[tuple[float, object]] = []
    targets = {t.lower() for t in (campaign.target_niches or [])}
    langs = {lang.lower() for lang in (campaign.target_languages or [])}
    for creator in svc.creators:
        niche_hit = len(targets & {n.lower() for n in creator.niches})
        lang_hit = len(langs & {lang.lower() for lang in creator.languages}) if langs else 0
        score = niche_hit * 2.0 + lang_hit * 1.0 + min(creator.avg_engagement_rate / 5.0, 1.0)
        if niche_hit or lang_hit or not targets:
            try:
                card = creator.to_card_dict()
            except AttributeError:
                card = creator.model_dump()
            card["match_score"] = round(score, 2)
            scored.append((score, card))
    scored.sort(key=lambda t: (-t[0], -t[1].get("total_followers", 0)))
    return {
        "campaign": _card(campaign),
        "total": len(scored),
        "items": [card for _, card in scored[:limit]],
    }
