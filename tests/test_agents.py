import pytest
from creo.agents.matching_agent import MatchingAgent
from creo.agents.categorization_agent import CategorizationAgent
from creo.agents.application_reviewer import ApplicationReviewerAgent
from creo.agents.verification_agent import VerificationAgent


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
