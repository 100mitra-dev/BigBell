import logging

from creo.agents.base import BaseAgent
from creo.models import Creator

logger = logging.getLogger(__name__)


class VerificationAgent(BaseAgent):
    def verify(self, creator: Creator) -> dict:
        if self.use_mock:
            return self._mock_verify(creator)
        logger.debug("AI verifying creator %s", creator.id)
        return self._ai_verify(creator)

    def _mock_verify(self, creator: Creator) -> dict:
        checks = {}

        profile_check = {
            "name": bool(creator.name),
            "email": bool(creator.email and "@" in creator.email),
            "phone": bool(creator.phone and len(creator.phone) >= 10),
            "primary_niche": bool(creator.primary_niche),
            "primary_language": bool(creator.primary_language),
        }
        checks["profile_fields"] = profile_check
        checks["profile_completeness"] = creator.profile_completeness

        platform_results = {}
        for platform, info in creator.platforms.items():
            platform_results[platform] = {
                "handle": info.handle,
                "followers": info.followers,
                "verified": info.verified,
                "exists": True,
                "active_recently": True,
                "suspicious_activity": False,
            }
        checks["platforms"] = platform_results

        follower_growth = [3.5, 2.1, 4.8]
        checks["follower_growth_rate"] = follower_growth

        content_quality = {
            "score": creator.content_quality_score,
            "consistency": round(creator.content_quality_score * 0.9, 1),
            "originality": round(creator.content_quality_score * 0.85, 1),
            "audience_match": round(creator.content_quality_score * 0.8, 1),
        }
        checks["content_quality"] = content_quality

        issues = []
        if creator.profile_completeness < 80:
            issues.append("Profile incomplete - missing key fields")
        if not creator.phone:
            issues.append("Phone number not provided")
        verified_count = sum(1 for p in creator.platforms.values() if p.verified)
        if verified_count == 0 and creator.platforms:
            issues.append("No verified social media accounts")

        overall = min(100, (creator.profile_completeness * 0.4 + creator.content_quality_score * 10 * 0.3 + verified_count * 10 * 0.3))
        checks["overall_score"] = round(overall, 1)
        checks["issues"] = issues
        checks["verified"] = overall >= 60

        return checks

    def _ai_verify(self, creator: Creator) -> dict:
        platforms_str = "\n".join(
            f"- {p}: @{info.handle}, {info.followers:,} followers, {'verified' if info.verified else 'unverified'}"
            for p, info in creator.platforms.items()
        )
        prompt = f"""You are an AI verification agent for creator accounts.

Verify the following creator profile:

Name: {creator.name}
Email: {creator.email}
Phone: {creator.phone or 'Not provided'}
Niche: {creator.primary_niche}
Language: {creator.primary_language}
Content Quality Score: {creator.content_quality_score}/10
Profile Completeness: {creator.profile_completeness}%

Platforms:
{platforms_str}

Return a JSON with:
1. overall_score (0-100)
2. profile_completeness (0-100)
3. issues (list of strings found)
4. verified (boolean - true if score >= 60)
5. content_quality (object with score, consistency, originality)
6. platform_status (object with each platform and its status)

Return ONLY valid JSON, no markdown formatting."""
        result = self._run_llm_chain(prompt)
        if result is None:
            return self._mock_verify(creator)
        try:
            import json
            return json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception as e:
            logger.error("AI verification failed, falling back to mock: %s", e)
            return self._mock_verify(creator)
