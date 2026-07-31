import pytest
from unittest import mock

from creo.agents.base import BaseAgent
from creo.agents.matching import MatchingAgent
from creo.models import Application
from creo.utils.mock_content import mock_recent_posts
from creo.agents.categorization import CategorizationAgent
from creo.agents.application_reviewer import ApplicationReviewerAgent
from creo.agents.verification import VerificationAgent
from creo.agents.extraction import CreatorExtractionAgent, extract_pdf_text, missing_required_fields
from creo.models import Creator, CreatorStatus


class TestMatchingAgent:
    def test_mock_match_exact_niche(self, sample_creator, sample_campaign):
        agent = MatchingAgent()
        result = agent._mock_match(sample_creator, sample_campaign)
        assert result["niche_overlap"] == 9.5
        assert result["language_overlap"] == 9.5
        assert result["overall_score"] > 0
        assert "match_quality" in result
        assert len(result["alignment_points"]) >= 2

    def test_mock_match_no_overlap(self, minimal_creator, sample_campaign):
        agent = MatchingAgent()
        result = agent._mock_match(minimal_creator, sample_campaign)
        assert result["niche_overlap"] == 2.0
        assert result["language_overlap"] == 9.5

    def test_mock_match_secondary_niche(self, inactive_creator, sample_campaign):
        agent = MatchingAgent()
        result = agent._mock_match(inactive_creator, sample_campaign)
        assert result["niche_overlap"] == 2.0
        assert result["language_overlap"] == 7.0

    def test_mock_match_deterministic(self, sample_creator, sample_campaign):
        agent = MatchingAgent()
        r1 = agent._mock_match(sample_creator, sample_campaign)
        r2 = agent._mock_match(sample_creator, sample_campaign)
        assert r1 == r2

    def test_score_match_deterministic(self, sample_creator, sample_campaign):
        agent = MatchingAgent()
        r1 = agent.match(sample_creator, sample_campaign)
        r2 = agent.match(sample_creator, sample_campaign)
        assert r1 == r2

    def test_score_match_exact_niche(self, sample_creator, sample_campaign):
        result = MatchingAgent().match(sample_creator, sample_campaign)
        assert result["niche_overlap"] == 9.5
        assert result["language_overlap"] == 9.5
        assert result["overall_score"] > 0

    def test_score_match_no_overlap(self, minimal_creator, sample_campaign):
        result = MatchingAgent().match(minimal_creator, sample_campaign)
        assert result["niche_overlap"] == 2.0

    def test_score_match_semantic_niche_boost(self, sample_campaign):
        creator = Creator(
            id="creator-sem",
            name="Semantic Creator",
            email="sem@example.com",
            primary_niche="Fitness & Wellness",
            secondary_niches=[],
            primary_language="English",
            platforms={},
            content_quality_score=7.0,
            profile_completeness=80.0,
            avg_engagement_rate=3.0,
            status=CreatorStatus.ACTIVE,
        )
        campaign = sample_campaign.model_copy(deep=True)
        campaign.target_niches = ["Lifestyle & Health"]
        result = MatchingAgent().match(creator, campaign)
        assert result["niche_overlap"] >= 5.0


class TestCategorizationAgent:
    def test_mock_categorize(self, sample_creator):
        agent = CategorizationAgent()
        result = agent._mock_categorize(sample_creator)
        assert result["primary_niche"] == "Gaming"
        assert result["primary_language"] == "English"
        assert result["tier"] == "Pro"
        assert len(result["niche_scores"]) == 5
        assert len(result["suggested_tags"]) >= 3

    def test_mock_categorize_deterministic(self, sample_creator):
        agent = CategorizationAgent()
        r1 = agent._mock_categorize(sample_creator)
        r2 = agent._mock_categorize(sample_creator)
        assert r1 == r2


class TestApplicationReviewerAgent:
    def test_mock_review_accept(self, sample_creator, sample_campaign):
        agent = ApplicationReviewerAgent()
        result = agent._mock_review(sample_creator, sample_campaign)
        assert result["recommendation"] == "accept"
        assert result["score"] >= 7
        assert result["niche_alignment"] == 9.0
        assert result["language_match"] == 9.0

    def test_mock_review_risks(self, minimal_creator, sample_campaign):
        agent = ApplicationReviewerAgent()
        result = agent._mock_review(minimal_creator, sample_campaign)
        assert len(result["risks"]) > 0
        assert result["recommendation"] == "reject"

    def test_mock_review_deterministic(self, sample_creator, sample_campaign):
        agent = ApplicationReviewerAgent()
        r1 = agent._mock_review(sample_creator, sample_campaign)
        r2 = agent._mock_review(sample_creator, sample_campaign)
        assert r1 == r2


class TestVerificationAgent:
    def test_mock_verify_high_score(self, sample_creator):
        agent = VerificationAgent()
        result = agent._mock_verify(sample_creator)
        assert result["verified"] is True
        assert result["overall_score"] >= 60
        assert len(result["issues"]) == 0
        assert result["profile_fields"]["name"] is True
        assert result["profile_fields"]["email"] is True

    def test_mock_verify_low_score(self, minimal_creator):
        agent = VerificationAgent()
        result = agent._mock_verify(minimal_creator)
        assert result["profile_completeness"] < 80
        assert len(result["issues"]) > 0

    def test_mock_verify_platforms(self, sample_creator):
        agent = VerificationAgent()
        result = agent._mock_verify(sample_creator)
        for platform, info in result["platforms"].items():
            assert info["exists"] is True
            assert info["active_recently"] is True
            assert info["suspicious_activity"] is False

    def test_mock_verify_deterministic(self, sample_creator):
        agent = VerificationAgent()
        r1 = agent._mock_verify(sample_creator)
        r2 = agent._mock_verify(sample_creator)
        assert r1 == r2


class TestCreatorExtractionAgent:
    def test_mock_parse_whatsapp_style_text(self):
        agent = CreatorExtractionAgent()
        text = (
            "Hi team, this is Arjun Mehta. I run a gaming channel on YouTube — "
            "youtube.com/@arjunplays, 250k subscribers. I make gaming and tech content "
            "in English. My email is arjun.mehta@email.com and phone is +91 98765 43211."
        )
        result = agent._mock_parse_text(text)
        assert result["name"] == "Arjun Mehta"
        assert result["email"] == "arjun.mehta@email.com"
        assert result["phone"] == "+919876543211"
        assert result["primary_niche"] == "Gaming"
        assert result["primary_language"] == "English"
        assert result["platforms"]["youtube"]["handle"] == "@arjunplays"
        assert result["platforms"]["youtube"]["followers"] == 250000
        assert result["notes"] == text

    def test_mock_parse_beauty_intro(self):
        agent = CreatorExtractionAgent()
        result = agent._mock_parse_text(
            "Hi, I'm Priya Sharma. I'm a beauty content creator from Mumbai. "
            "My Instagram @priyabeauty has 125k followers. I make makeup tutorials "
            "in Hindi and English. Reach me at priya.sharma@email.com or +91 98765 43210."
        )
        assert result["name"] == "Priya Sharma"
        assert result["email"] == "priya.sharma@email.com"
        assert result["phone"] == "+919876543210"
        assert result["primary_niche"] == "Beauty & Makeup"
        assert result["primary_language"] == "Hindi"
        assert result["platforms"]["instagram"]["handle"] == "@priyabeauty"
        assert result["platforms"]["instagram"]["followers"] == 125000

    def test_mock_parse_email_fallback_name(self):
        agent = CreatorExtractionAgent()
        result = agent._mock_parse_text(
            "Makeup collab — priya.sharma@email.com, based in Mumbai. "
            "90k followers on Instagram @priyabeauty."
        )
        assert result["name"] == "Priya Sharma"
        assert result["primary_niche"] == "Beauty & Makeup"
        assert result["platforms"]["instagram"]["followers"] == 90000

    def test_mock_parse_skips_email_handle(self):
        agent = CreatorExtractionAgent()
        result = agent._mock_parse_text(
            "Contact rohit.kumar@email.com. 50k followers on YouTube @rohitkumar."
        )
        assert result["email"] == "rohit.kumar@email.com"
        assert "youtube" in result["platforms"]
        assert result["platforms"]["youtube"]["handle"] == "@rohitkumar"
        assert all("email.com" not in info["handle"] for info in result["platforms"].values())

    def test_mock_parse_missing_fields(self):
        agent = CreatorExtractionAgent()
        result = agent._mock_parse_text("Just a random note with no profile details.")
        missing = missing_required_fields(result)
        assert missing == ["name", "email", "primary_niche", "primary_language"]

    def test_parse_pdf_and_extract(self):
        from io import BytesIO

        from reportlab.pdfgen import canvas

        buf = BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(72, 720, "Name: Kavya Nair")
        c.drawString(72, 700, "Email: kavya.nair@email.com")
        c.drawString(72, 680, "Phone: +91 98765 43212")
        c.save()
        text = extract_pdf_text(buf.getvalue())
        assert "Kavya Nair" in text
        result = CreatorExtractionAgent()._mock_parse_text(text)
        assert result["name"] == "Kavya Nair"
        assert result["email"] == "kavya.nair@email.com"
        assert result["phone"] == "+919876543212"

    def test_mock_parse_deterministic(self):
        agent = CreatorExtractionAgent()
        text = "Hi, I'm Ravi Kumar. Gaming creator on YouTube @ravikumar, 1.2M subscribers."
        assert agent._mock_parse_text(text) == agent._mock_parse_text(text)


class TestApplicationModelFields:
    def test_application_defaults(self):
        app = Application(id="APP-1", creator_id="CRE-1", campaign_id="CAM-1")
        assert app.source == "email"
        assert app.letter is None

    def test_application_custom_source_and_letter(self):
        app = Application(
            id="APP-1",
            creator_id="CRE-1",
            campaign_id="CAM-1",
            source="whatsapp",
            letter="Hi team, would love to collaborate!",
        )
        assert app.source == "whatsapp"
        assert "collaborate" in app.letter


class TestMockRecentPosts:
    def test_returns_five_deterministic_posts(self, sample_creator):
        posts = mock_recent_posts(sample_creator)
        assert len(posts) == 5
        assert all("caption" in p and "likes" in p and "platform" in p for p in posts)
        assert mock_recent_posts(sample_creator) == posts

    def test_posts_use_creator_platforms(self, sample_creator):
        platforms = {p["platform"] for p in mock_recent_posts(sample_creator)}
        assert platforms.issubset(set(sample_creator.platforms.keys()))

    def test_posts_scale_with_followers(self, sample_creator, minimal_creator):
        big = mock_recent_posts(sample_creator)
        small = mock_recent_posts(minimal_creator)
        assert sum(p["likes"] for p in big) > sum(p["likes"] for p in small)

    def test_falls_back_to_instagram_without_platforms(self, minimal_creator):
        posts = mock_recent_posts(minimal_creator)
        assert all(p["platform"] == "instagram" for p in posts)


class TestBaseAgentTimeout:
    def test_llm_timeout_constant_is_10_seconds(self):
        assert BaseAgent.LLM_TIMEOUT_SECONDS == 10

    def test_failure_still_logs_api_entry(self):
        agent = BaseAgent()
        captured = {}

        def fake_add_log(entry):
            captured.update(entry.__dict__)

        def fake_get_llm():
            llm = mock.MagicMock()
            llm.invoke.side_effect = RuntimeError("server exploded")
            return llm

        with mock.patch.object(agent, "_get_llm", fake_get_llm), mock.patch(
            "creo.agents.base.add_log", fake_add_log
        ):
            result = agent._run_llm_chain("test prompt")

        assert result is None
        assert captured["success"] is False
        assert captured["error"] == "server exploded"
        assert captured["duration_ms"] >= 0
        assert captured["request_preview"] == "test prompt"

    def test_timeout_error_is_labeled(self):
        agent = BaseAgent()
        captured = {}

        def fake_add_log(entry):
            captured.update(entry.__dict__)

        def fake_get_llm():
            llm = mock.MagicMock()
            llm.invoke.side_effect = TimeoutError("Request timed out after 20 seconds")
            return llm

        with mock.patch.object(agent, "_get_llm", fake_get_llm), mock.patch(
            "creo.agents.base.add_log", fake_add_log
        ):
            result = agent._run_llm_chain("test prompt")

        assert result is None
        assert captured["success"] is False
        assert captured["error"].startswith("TIMEOUT (>10s)")

    def test_stream_failure_logs_entry(self):
        agent = BaseAgent()

        def fake_get_llm():
            llm = mock.MagicMock()
            llm.stream.side_effect = RuntimeError("stream failed")
            return llm

        with mock.patch.object(agent, "_get_llm", fake_get_llm), mock.patch(
            "creo.agents.base.add_log"
        ) as fake_add_log:
            chunks = list(agent._stream_llm("test prompt"))

        assert any("stream failed" in c for c in chunks)
        entry = fake_add_log.call_args[0][0]
        assert entry.success is False
        assert entry.error == "stream failed"

    def test_get_llm_forwards_timeout(self):
        with mock.patch("creo.agents.base.get_provider", return_value="openai"), mock.patch(
            "creo.agents.base.get_openai_key", return_value="sk-test"
        ), mock.patch("creo.agents.base.get_openai_model", return_value="gpt-4o-mini"):
            llm = BaseAgent()._get_llm()
        assert llm.request_timeout == 10
        assert llm.max_retries == 1

        with mock.patch("creo.agents.base.get_provider", return_value="gemini"), mock.patch(
            "creo.agents.base.get_gemini_key", return_value="AIza-test"
        ), mock.patch("creo.agents.base.get_gemini_model", return_value="gemini-2.0-flash"):
            llm = BaseAgent()._get_llm()
        assert llm.timeout == 10
