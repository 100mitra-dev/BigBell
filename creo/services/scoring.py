"""BigBell shared scoring logic for creator-campaign matching and application review."""
import logging
from dataclasses import dataclass

from creo.models import Creator, Campaign
from creo.rag.embeddings import get_local_embeddings, cosine_similarity

logger = logging.getLogger(__name__)

_NICHE_EMBEDDING_CACHE: dict[str, list[float]] = {}


def _niche_embedding(text: str) -> list[float]:
    vector = _NICHE_EMBEDDING_CACHE.get(text)
    if vector is None:
        vector = get_local_embeddings().embed_query(text)
        _NICHE_EMBEDDING_CACHE[text] = vector
    return vector


# Weights from config
MATCH_NICHE_WEIGHT = 0.30
MATCH_LANGUAGE_WEIGHT = 0.15
MATCH_REACH_WEIGHT = 0.10
MATCH_ENGAGEMENT_WEIGHT = 0.15
MATCH_QUALITY_WEIGHT = 0.15
MATCH_COMPLETENESS_WEIGHT = 0.05
MATCH_BUDGET_WEIGHT = 0.10


@dataclass
class ScoreComponents:
    niche_overlap: float
    language_overlap: float
    reach_score: float
    engagement_score: float
    quality_score: float
    completeness_score: float
    budget_fit: float
    alignment_points: list[str]


def score_niche(creator: Creator, campaign: Campaign) -> float:
    """Score niche overlap between creator and campaign targets."""
    creator_niches = [n.lower() for n in creator.niches]
    target_niches = [n.lower() for n in campaign.target_niches]

    if creator.primary_niche.lower() in target_niches:
        return 9.5
    if any(n in target_niches for n in creator.secondary_niches):
        return 7.0
    # Substring fallback
    for target in target_niches:
        if any(c in target for c in creator_niches):
            return 5.0
    return 2.0


def score_language(creator: Creator, campaign: Campaign) -> float:
    """Score language overlap between creator and campaign targets."""
    if not campaign.target_languages:
        return 5.0  # neutral if no language requirement
    creator_langs = [l.lower() for l in creator.languages]
    target_langs = [l.lower() for l in campaign.target_languages]
    if creator.primary_language.lower() in target_langs:
        return 9.5
    if any(l.lower() in target_langs for l in creator.secondary_languages):
        return 7.0
    return 2.0


def score_reach(creator: Creator) -> float:
    """Score based on total followers (reach)."""
    return min(10.0, (creator.total_followers / 100000) * 0.5)


def score_engagement(creator: Creator) -> float:
    """Score based on engagement rate."""
    return min(10.0, creator.avg_engagement_rate * 1.5)


def score_quality(creator: Creator) -> float:
    """Score based on content quality."""
    return min(10.0, creator.content_quality_score)


def score_completeness(creator: Creator) -> float:
    """Score based on profile completeness."""
    return min(10.0, creator.profile_completeness / 10)


def score_budget_fit(creator: Creator, campaign: Campaign) -> float:
    """Score based on budget fit."""
    avg_earning = max(creator.total_earnings / max(creator.total_campaigns_completed, 1), 1)
    if creator.total_campaigns_completed > 0:
        return min(10.0, (campaign.budget / avg_earning) * 2)
    return 5.0



def calculate_overall_score(components: ScoreComponents) -> float:
    """Calculate weighted overall score from components."""
    overall = (
        components.niche_overlap * MATCH_NICHE_WEIGHT
        + components.language_overlap * MATCH_LANGUAGE_WEIGHT
        + components.reach_score * MATCH_REACH_WEIGHT
        + components.engagement_score * MATCH_ENGAGEMENT_WEIGHT
        + components.quality_score * MATCH_QUALITY_WEIGHT
        + components.completeness_score * MATCH_COMPLETENESS_WEIGHT
        + components.budget_fit * MATCH_BUDGET_WEIGHT
    )
    return round(min(10.0, overall), 1)


def build_alignment_points(components: ScoreComponents, creator: Creator) -> list[str]:
    """Build human-readable alignment points."""
    points = []
    if components.niche_overlap >= 7:
        points.append(f"Niche alignment: {creator.primary_niche} matches campaign target")
    if components.language_overlap >= 7:
        points.append(f"Language match: {creator.primary_language} is targeted")
    if components.engagement_score >= 7:
        points.append(f"Strong engagement rate: {creator.avg_engagement_rate}%")
    if components.quality_score >= 7:
        points.append(f"High content quality score: {creator.content_quality_score}/10")
    return points



def compute_match_components(creator: Creator, campaign: Campaign) -> ScoreComponents:
    """Compute all score components for a creator-campaign pair."""
    niche = score_niche(creator, campaign)
    language = score_language(creator, campaign)
    reach = float(getattr(creator, "total_followers", 0) or 0) / 200000.0
    engagement = float(getattr(creator, "avg_engagement_rate", 0) or 0) * 1.5
    quality = float(getattr(creator, "content_quality_score", 0) or 0)
    completeness = float(getattr(creator, "profile_completeness", 0) or 0) / 10.0
    budget = score_budget_fit(creator, campaign)


    alignment = []
    if niche >= 7:
        alignment.append(f"Niche alignment: {creator.primary_niche} matches campaign target")
    if language >= 7:
        alignment.append(f"Language match: {creator.primary_language} is targeted")
    if engagement >= 7:
        alignment.append(f"Strong engagement rate: {creator.avg_engagement_rate}%")
    if quality >= 7:
        alignment.append(f"High content quality score: {creator.content_quality_score}/10")

    return ScoreComponents(
        niche_overlap=niche,
        language_overlap=language,
        reach_score=reach,
        engagement_score=engagement,
        quality_score=quality,
        completeness_score=completeness,
        budget_fit=budget,
        alignment_points=alignment,
    )


def match_score(creator: Creator, campaign: Campaign) -> dict:
    """Full match scoring - returns structured dict."""
    components = compute_match_components(creator, campaign)
    overall = calculate_overall_score(components)

    match_quality = "Excellent" if overall >= 8.5 else "Good" if overall >= 7.0 else "Fair" if overall >= 5.5 else "Poor"

    return {
        "overall_score": overall,
        "niche_overlap": round(components.niche_overlap, 1),
        "language_overlap": round(components.language_overlap, 1),
        "reach_score": round(components.reach_score, 1),
        "engagement_score": round(components.engagement_score, 1),
        "quality_score": round(components.quality_score, 1),
        "completeness_score": round(components.completeness_score, 1),
        "budget_fit": round(components.budget_fit, 1),
        "alignment_points": components.alignment_points,
        "match_quality": match_quality,
    }