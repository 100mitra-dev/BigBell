import logging

from creo.agents.base import BaseAgent
from creo.models import Creator
from creo.config import get_all_niches, LANGUAGES

logger = logging.getLogger(__name__)


class CategorizationAgent(BaseAgent):
    def categorize(self, creator: Creator) -> dict:
        if self.use_mock:
            return self._mock_categorize(creator)
        logger.debug("AI categorizing creator %s", creator.id)
        return self._ai_categorize(creator)

    def _mock_categorize(self, creator: Creator) -> dict:
        primary_niche = creator.primary_niche
        niche_scores = {niche: 2.5 for niche in get_all_niches()}
        niche_scores[primary_niche] = 9.0

        for secondary in creator.secondary_niches:
            if secondary in niche_scores:
                niche_scores[secondary] = 7.5

        niche_scores = dict(sorted(niche_scores.items(), key=lambda x: -x[1])[:5])

        primary_lang = creator.primary_language
        lang_scores = {lang: 1.5 for lang in LANGUAGES}
        lang_scores[primary_lang] = 10.0
        for sec_lang in creator.secondary_languages:
            if sec_lang in lang_scores:
                lang_scores[sec_lang] = 7.5
        lang_scores = dict(sorted(lang_scores.items(), key=lambda x: -x[1])[:5])

        tier = creator.tier
        suggested_tags = [primary_niche.lower().replace(" & ", "-").replace(" ", "-")]
        for s in creator.secondary_niches[:2]:
            suggested_tags.append(s.lower().replace(" & ", "-").replace(" ", "-"))
        suggested_tags.append(primary_lang.lower())
        for sl in creator.secondary_languages[:1]:
            suggested_tags.append(sl.lower())

        return {
            "primary_niche": primary_niche,
            "niche_scores": {k: round(v, 1) for k, v in niche_scores.items()},
            "primary_language": primary_lang,
            "language_scores": {k: round(v, 1) for k, v in lang_scores.items()},
            "tier": tier,
            "suggested_tags": suggested_tags,
        }

    def _ai_categorize(self, creator: Creator) -> dict:
        prompt = f"""You are an AI categorization agent for creators.

Categorize this creator profile:

Name: {creator.name}
Current Niche: {creator.primary_niche}
Secondary Niches: {', '.join(creator.secondary_niches)}
Languages: {creator.primary_language} + {', '.join(creator.secondary_languages)}
Followers: {creator.total_followers:,}
Content Quality: {creator.content_quality_score}/10
Engagement Rate: {creator.avg_engagement_rate}%

Available niches: {', '.join(get_all_niches())}
Available languages: {', '.join(LANGUAGES)}

Return a JSON with:
1. primary_niche (string - the best matching niche)
2. secondary_niches (list of 2-3 recommended niches)
3. niche_scores (dict of top 5 niches with scores 0-10)
4. primary_language (string)
5. language_scores (dict of top 3 languages with scores 0-10)
6. tier (string: Rising/Growth/Pro/Elite)
7. suggested_tags (list of 3-5 string tags)

Return ONLY valid JSON, no markdown formatting."""
        result = self._run_llm_chain(prompt)
        try:
            import json
            return json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception as e:
            logger.error("AI categorization failed, falling back to mock: %s", e)
            return self._mock_categorize(creator)
