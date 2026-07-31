import logging

from creo.agents.base import BaseAgent
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


class MatchingAgent(BaseAgent):
    def match(self, creator: Creator, campaign: Campaign) -> dict:
        return self._score_match(creator, campaign)

    def _score_match(self, creator: Creator, campaign: Campaign) -> dict:
        niche_overlap = self._score_niche(creator, campaign)
        language_overlap = self._score_language(creator, campaign)

        reach_score = min(10, (creator.total_followers / 100000) * 0.5)
        engagement_score = min(10, creator.avg_engagement_rate * 1.5)
        quality_score = min(10, creator.content_quality_score)
        completeness_score = min(10, creator.profile_completeness / 10)

        avg_earning_per_campaign = max(creator.total_earnings / max(creator.total_campaigns_completed, 1), 1)
        budget_fit = min(10, (campaign.budget / avg_earning_per_campaign) * 2) if creator.total_campaigns_completed > 0 else 5.0

        overall = (
            niche_overlap * 0.30
            + language_overlap * 0.15
            + reach_score * 0.10
            + engagement_score * 0.15
            + quality_score * 0.15
            + completeness_score * 0.05
            + budget_fit * 0.10
        )

        alignment_points = []
        if niche_overlap >= 7:
            alignment_points.append(f"Niche alignment: {creator.primary_niche} matches campaign target")
        elif niche_overlap >= 5:
            alignment_points.append(f"Niche alignment: {creator.primary_niche} is semantically close to campaign targets")
        if language_overlap >= 7:
            alignment_points.append(f"Language match: {creator.primary_language} is targeted")
        if engagement_score >= 7:
            alignment_points.append(f"Strong engagement rate: {creator.avg_engagement_rate}%")
        if quality_score >= 7:
            alignment_points.append(f"High content quality score: {creator.content_quality_score}/10")

        return {
            "overall_score": round(min(10, overall), 1),
            "niche_overlap": round(niche_overlap, 1),
            "language_overlap": round(language_overlap, 1),
            "reach_score": round(reach_score, 1),
            "engagement_score": round(engagement_score, 1),
            "quality_score": round(quality_score, 1),
            "completeness_score": round(completeness_score, 1),
            "budget_fit": round(budget_fit, 1),
            "alignment_points": alignment_points,
            "match_quality": "excellent" if overall >= 8 else "good" if overall >= 6 else "fair" if overall >= 4 else "poor",
        }

    def _score_niche(self, creator: Creator, campaign: Campaign) -> float:
        targets = [t.lower() for t in campaign.target_niches]
        if creator.primary_niche.lower() in targets:
            return 9.5
        if any(n.lower() in targets for n in creator.secondary_niches):
            return 7.0
        best = 0.0
        creator_niches = [creator.primary_niche] + list(creator.secondary_niches)
        for cn in creator_niches:
            cv = _niche_embedding(cn)
            for target in campaign.target_niches:
                sim = cosine_similarity(cv, _niche_embedding(target))
                if sim > best:
                    best = sim
        if best >= 0.60:
            return 6.0
        if best >= 0.50:
            return 5.0
        return 2.0

    def _score_language(self, creator: Creator, campaign: Campaign) -> float:
        if creator.primary_language in campaign.target_languages:
            return 9.5
        if any(l in campaign.target_languages for l in creator.secondary_languages):
            return 7.0
        return 2.0

    def _mock_match(self, creator: Creator, campaign: Campaign) -> dict:
        niche_overlap = 0
        if creator.primary_niche.lower() in [n.lower() for n in campaign.target_niches]:
            niche_overlap = 9.5
        elif any(n.lower() in [t.lower() for t in campaign.target_niches] for n in creator.secondary_niches):
            niche_overlap = 7.0
        else:
            for target_niche in campaign.target_niches:
                if any(charmap.lower() in target_niche.lower() for charmap in [creator.primary_niche] + creator.secondary_niches):
                    niche_overlap = 5.0
                    break
            else:
                niche_overlap = 2.0

        language_overlap = 0
        if creator.primary_language in campaign.target_languages:
            language_overlap = 9.5
        elif any(l in campaign.target_languages for l in creator.secondary_languages):
            language_overlap = 7.0
        else:
            language_overlap = 2.0

        reach_score = min(10, (creator.total_followers / 100000) * 0.5)
        engagement_score = min(10, creator.avg_engagement_rate * 1.5)
        quality_score = min(10, creator.content_quality_score)
        completeness_score = min(10, creator.profile_completeness / 10)

        avg_earning_per_campaign = max(creator.total_earnings / max(creator.total_campaigns_completed, 1), 1)
        budget_fit = min(10, (campaign.budget / avg_earning_per_campaign) * 2) if creator.total_campaigns_completed > 0 else 5.0

        overall = (
            niche_overlap * 0.30
            + language_overlap * 0.15
            + reach_score * 0.10
            + engagement_score * 0.15
            + quality_score * 0.15
            + completeness_score * 0.05
            + budget_fit * 0.10
        )

        alignment_points = []
        if niche_overlap >= 7:
            alignment_points.append(f"Niche alignment: {creator.primary_niche} matches campaign target")
        if language_overlap >= 7:
            alignment_points.append(f"Language match: {creator.primary_language} is targeted")
        if engagement_score >= 7:
            alignment_points.append(f"Strong engagement rate: {creator.avg_engagement_rate}%")
        if quality_score >= 7:
            alignment_points.append(f"High content quality score: {creator.content_quality_score}/10")

        return {
            "overall_score": round(min(10, overall), 1),
            "niche_overlap": round(niche_overlap, 1),
            "language_overlap": round(language_overlap, 1),
            "reach_score": round(reach_score, 1),
            "engagement_score": round(engagement_score, 1),
            "quality_score": round(quality_score, 1),
            "completeness_score": round(completeness_score, 1),
            "budget_fit": round(budget_fit, 1),
            "alignment_points": alignment_points,
            "match_quality": "excellent" if overall >= 8 else "good" if overall >= 6 else "fair" if overall >= 4 else "poor",
        }

    def _ai_match(self, creator: Creator, campaign: Campaign) -> dict:
        platforms_str = ", ".join(f"{p}({info.followers:,})" for p, info in creator.platforms.items())
        prompt = f"""You are an AI matching agent for creator-campaign alignment.

Creator:
- Name: {creator.name}
- Niche: {creator.primary_niche} (Secondary: {', '.join(creator.secondary_niches)})
- Languages: {creator.primary_language} (+ {', '.join(creator.secondary_languages)})
- Followers: {creator.total_followers:,} on {platforms_str}
- Content Quality: {creator.content_quality_score}/10
- Engagement Rate: {creator.avg_engagement_rate}%
- Profile Completeness: {creator.profile_completeness}%
- Past Campaigns: {creator.total_campaigns_completed}
- Total Earnings: ₹{creator.total_earnings:,.0f}

Campaign:
- Title: {campaign.title}
- Brand: {campaign.brand}
- Budget: ₹{campaign.budget:,.0f}
- Target Niches: {', '.join(campaign.target_niches)}
- Target Languages: {', '.join(campaign.target_languages)}
- Requirements: {'; '.join(campaign.requirements)}

Return a JSON with:
1. overall_score (0-10)
2. niche_overlap (0-10)
3. language_overlap (0-10)
4. reach_score (0-10)
5. engagement_score (0-10)
6. quality_score (0-10)
7. completeness_score (0-10)
8. budget_fit (0-10)
9. alignment_points (list of 2-4 strings explaining why)
10. match_quality ("excellent"/"good"/"fair"/"poor")

Return ONLY valid JSON, no markdown formatting."""
        result = self._run_llm_chain(prompt)
        if result is None:
            return self._mock_match(creator, campaign)
        try:
            import json
            return json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception as e:
            logger.error("AI matching failed, falling back to mock: %s", e)
            return self._mock_match(creator, campaign)
