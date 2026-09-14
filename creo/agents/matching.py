"""BigBell matching agent — AI-powered creator-campaign match scoring."""
import logging

from creo.agents.base import BaseAgent
from creo.models import Creator, Campaign
from creo.rag.embeddings import get_local_embeddings, cosine_similarity
from creo.services.scoring import (
    match_score,
    score_niche,
    score_language,
    score_reach,
    score_engagement,
    score_quality,
    score_completeness,
    score_budget_fit,
    calculate_overall_score,
    build_alignment_points,
    ScoreComponents,
    ScoreComponents as SC,
    _niche_embedding,
)

logger = logging.getLogger(__name__)


class MatchingAgent(BaseAgent):
    def match(self, creator, campaign):
        return self._score_base(creator, campaign, self._score_niche)

    def _score_base(self, creator, campaign, niche_fn):
        n = niche_fn(creator, campaign)
        l = self._score_language(creator, campaign)
        r = score_reach(creator)
        e = score_engagement(creator)
        q = score_quality(creator)
        c = score_completeness(creator)
        b = score_budget_fit(creator, campaign)
        s = ScoreComponents(n, l, r, e, q, c, b, [])
        o = calculate_overall_score(s)
        return {
            "overall_score": o,
            "niche_overlap": round(n, 1),
            "language_overlap": round(l, 1),
            "reach_score": round(r, 1),
            "engagement_score": round(e, 1),
            "quality_score": round(q, 1),
            "completeness_score": round(c, 1),
            "budget_fit": round(b, 1),
            "alignment_points": build_alignment_points(s, creator),
            "match_quality": "Excellent" if o >= 8.5 else "Good" if o >= 7 else "Fair" if o >= 5.5 else "Poor",
        }

    def _score_niche(self, creator, campaign):
        keyword = self._keyword_niche(creator, campaign)
        try:
            creator_niche_text = " ".join(creator.niches)
            campaign_niche_text = " ".join(campaign.target_niches)
            if creator_niche_text and campaign_niche_text:
                creator_vec = _niche_embedding(creator_niche_text)
                campaign_vec = _niche_embedding(campaign_niche_text)
                if creator_vec and campaign_vec:
                    sim = cosine_similarity(creator_vec, campaign_vec)
                    if sim is not None:
                        score = 2.0 + sim * 8.0
                        return round(max(score, keyword), 1)
        except Exception:
            pass
        return keyword

    def _keyword_niche(self, creator, campaign):
        creator_niches = [str(n).lower() for n in (creator.niches or []) if n]
        target_niches = [str(n).lower() for n in (campaign.target_niches or []) if n]
        primary = str(getattr(creator, "primary_niche", "") or "").lower()
        if primary and primary in target_niches:
            return 9.5
        if any(str(n).lower() in target_niches for n in (creator.secondary_niches or [])):
            return 7.0
        health_cluster = {"fitness", "wellness", "health", "lifestyle", "gym", "yoga"}
        creator_tokens = {t for n in creator_niches for t in n.replace("&", " ").split()}
        target_tokens = {t for n in target_niches for t in n.replace("&", " ").split()}
        if creator_tokens & health_cluster and target_tokens & health_cluster:
            return 6.0
        for target in target_niches:
            if any(c in target for c in creator_niches):
                return 5.0
        return 2.0

    def _score_language(self, creator, campaign):
        return score_language(creator, campaign)

    def _mock_match(self, creator, campaign):
        return self._score_base(creator, campaign, self._keyword_niche)

    def _ai_match(self, creator, campaign):
        return self._score_base(creator, campaign, self._score_niche)
