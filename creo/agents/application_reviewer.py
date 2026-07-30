import logging

from creo.agents.base import BaseAgent
from creo.models import Creator, Campaign

logger = logging.getLogger(__name__)


class ApplicationReviewerAgent(BaseAgent):
    def review(self, creator: Creator, campaign: Campaign) -> dict:
        if self.use_mock:
            return self._mock_review(creator, campaign)
        logger.debug("AI reviewing creator %s for campaign %s", creator.id, campaign.id)
        return self._ai_review(creator, campaign)

    def _mock_review(self, creator: Creator, campaign: Campaign) -> dict:
        niche_score = 0
        if creator.primary_niche.lower() in [n.lower() for n in campaign.target_niches]:
            niche_score = 9.0
        elif any(n.lower() in [t.lower() for t in campaign.target_niches] for n in creator.secondary_niches):
            niche_score = 6.0
        else:
            niche_score = 2.5

        quality_score = min(10, creator.content_quality_score)
        engagement_score = min(10, creator.avg_engagement_rate * 2)
        completeness_score = creator.profile_completeness / 10

        language_match = 0
        if creator.primary_language in campaign.target_languages:
            language_match = 9.0
        elif any(l in campaign.target_languages for l in creator.secondary_languages):
            language_match = 6.0
        else:
            language_match = 2.0

        overall = (niche_score * 0.35 + quality_score * 0.25 + engagement_score * 0.2 + completeness_score * 0.1 + language_match * 0.1)

        risks = []
        if creator.profile_completeness < 70:
            risks.append("Profile is less than 70% complete")
        if creator.avg_engagement_rate < 2.0:
            risks.append("Low engagement rate")
        if creator.status.value == "inactive":
            risks.append("Creator account is inactive")
        if not creator.platforms:
            risks.append("No social media platforms linked")
        verified = sum(1 for p in creator.platforms.values() if p.verified)
        if verified == 0 and len(creator.platforms) > 0:
            risks.append("No verified social media accounts")

        feedback_parts = []
        if niche_score >= 7:
            feedback_parts.append(f"Strong niche alignment with {campaign.title}")
        else:
            feedback_parts.append(f"Niche ({creator.primary_niche}) may not be ideal for this campaign")

        if quality_score >= 7:
            feedback_parts.append("Good content quality")
        else:
            feedback_parts.append("Content quality needs improvement")

        if language_match >= 7:
            feedback_parts.append(f"Language ({creator.primary_language}) matches campaign requirements")
        else:
            feedback_parts.append(f"Language mismatch - creator primarily uses {creator.primary_language}")

        return {
            "score": round(min(10, overall), 1),
            "niche_alignment": round(niche_score, 1),
            "quality_score": round(quality_score, 1),
            "engagement_score": round(engagement_score, 1),
            "completeness_score": round(completeness_score, 1),
            "language_match": round(language_match, 1),
            "risks": risks,
            "feedback": " | ".join(feedback_parts),
            "recommendation": "accept" if overall >= 7 else "shortlist" if overall >= 5 else "reject",
        }

    def _ai_review(self, creator: Creator, campaign: Campaign) -> dict:
        prompt = f"""You are an AI application reviewer for a creator management platform.

Creator Profile:
- Name: {creator.name}
- Niche: {creator.primary_niche} (Secondary: {', '.join(creator.secondary_niches)})
- Languages: {creator.primary_language} (Secondary: {', '.join(creator.secondary_languages)})
- Total Followers: {creator.total_followers:,}
- Content Quality Score: {creator.content_quality_score}/10
- Profile Completeness: {creator.profile_completeness}%
- Engagement Rate: {creator.avg_engagement_rate}%
- Platforms: {', '.join(creator.platforms.keys())}
- Status: {creator.status.value}

Campaign: {campaign.title} by {campaign.brand}
- Target Niches: {', '.join(campaign.target_niches)}
- Target Languages: {', '.join(campaign.target_languages)}
- Budget: ₹{campaign.budget:,.0f}

Review this application and return a JSON with:
1. score (0-10)
2. niche_alignment (0-10)
3. quality_score (0-10)
4. engagement_score (0-10)
5. completeness_score (0-10)
6. language_match (0-10)
7. risks (list of strings)
8. feedback (string)
9. recommendation: "accept", "shortlist", or "reject"

Return ONLY valid JSON, no markdown formatting."""
        result = self._run_llm_chain(prompt)
        try:
            import json
            parsed = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
            return {
                "score": float(parsed.get("score", 5)),
                "niche_alignment": float(parsed.get("niche_alignment", 5)),
                "quality_score": float(parsed.get("quality_score", 5)),
                "engagement_score": float(parsed.get("engagement_score", 5)),
                "completeness_score": float(parsed.get("completeness_score", 5)),
                "language_match": float(parsed.get("language_match", 5)),
                "risks": parsed.get("risks", []),
                "feedback": parsed.get("feedback", ""),
                "recommendation": parsed.get("recommendation", "shortlist"),
            }
        except Exception as e:
            logger.error("AI review failed, falling back to mock: %s", e)
            return self._mock_review(creator, campaign)
