import random
import statistics

from src.core.agents.base import BaseAgent
from src.core.models import Creator, Campaign


class MatchingAgent(BaseAgent):
    def match(self, creator: Creator, campaign: Campaign) -> dict:
        if self.use_mock:
            return self._mock_match(creator, campaign)
        return self._ai_match(creator, campaign)

    def _mock_match(self, creator: Creator, campaign: Campaign) -> dict:
        niche_overlap = 0
        if creator.primary_niche.lower() in [n.lower() for n in campaign.target_niches]:
            niche_overlap = 9 + random.uniform(0, 1)
        elif any(n.lower() in [t.lower() for t in campaign.target_niches] for n in creator.secondary_niches):
            niche_overlap = 6 + random.uniform(0, 2)
        else:
            for target_niche in campaign.target_niches:
                if any(charmap.lower() in target_niche.lower() for charmap in [creator.primary_niche] + creator.secondary_niches):
                    niche_overlap = 4 + random.uniform(0, 2)
                    break
            else:
                niche_overlap = random.uniform(1, 3)

        language_overlap = 0
        if creator.primary_language in campaign.target_languages:
            language_overlap = 9 + random.uniform(0, 1)
        elif any(l in campaign.target_languages for l in creator.secondary_languages):
            language_overlap = 6 + random.uniform(0, 2)
        else:
            language_overlap = random.uniform(1, 3)

        reach_score = min(10, (creator.total_followers / 100000) * 0.5 + random.uniform(0, 2))
        engagement_score = min(10, creator.avg_engagement_rate * 1.5 + random.uniform(-0.5, 0.5))
        quality_score = min(10, creator.content_quality_score + random.uniform(-0.5, 0.5))
        completeness_score = min(10, creator.profile_completeness / 10 + random.uniform(-0.5, 0.5))

        budget_fit = min(10, (campaign.budget / max(creator.total_earnings / max(creator.total_campaigns_completed, 1), 1)) * 2 + random.uniform(0, 2)) if creator.total_campaigns_completed > 0 else 5

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
        try:
            import json
            return json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception:
            return self._mock_match(creator, campaign)
