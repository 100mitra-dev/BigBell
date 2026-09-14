import pytest
from creo.models import Creator, Campaign, PlatformInfo, CreatorStatus
from creo.services.creator_service import CreatorService


@pytest.fixture
def creator_service():
    return CreatorService()


@pytest.fixture
def sample_creator():
    return Creator(
        id="creator-1",
        name="Test Creator",
        email="test@example.com",
        phone="+919876543210",
        primary_niche="Gaming",
        secondary_niches=["Technology", "Comedy & Entertainment"],
        primary_language="English",
        secondary_languages=["Hindi"],
        platforms={
            "youtube": PlatformInfo(handle="@testcreator", followers=150000, verified=True),
            "instagram": PlatformInfo(handle="@testcreator", followers=80000, verified=True),
        },
        content_quality_score=8.5,
        profile_completeness=95.0,
        avg_engagement_rate=4.2,
        status=CreatorStatus.ACTIVE,
        total_campaigns_completed=12,
        total_earnings=2500000.0,
    )


@pytest.fixture
def sample_campaign():
    return Campaign(
        id="campaign-1",
        title="Summer Gaming Fest",
        brand="GameCo",
        description="A summer gaming festival campaign",
        requirements=["Post 3 videos", "Use hashtag #SummerGaming"],
        budget=500000.0,
        deadline="2026-08-31",
        target_niches=["Gaming", "Technology"],
        target_languages=["English", "Hindi"],
        status="active",
        created_at="2026-06-01",
    )


@pytest.fixture
def minimal_creator():
    return Creator(
        id="creator-2",
        name="Minimal Creator",
        email="minimal@example.com",
        primary_niche="Fashion",
        primary_language="English",
        secondary_languages=["Hindi"],
        platforms={},
        avg_engagement_rate=1.2,
        status=CreatorStatus.PENDING,
    )


@pytest.fixture
def inactive_creator():
    return Creator(
        id="creator-3",
        name="Inactive Creator",
        email="inactive@example.com",
        primary_niche="Fitness & Wellness",
        secondary_niches=["Health & Wellness"],
        primary_language="Tamil",
        secondary_languages=["English"],
        platforms={
            "youtube": PlatformInfo(handle="@inactive", followers=5000, verified=False),
        },
        content_quality_score=6.0,
        profile_completeness=60.0,
        avg_engagement_rate=0.8,
        status=CreatorStatus.INACTIVE,
        total_campaigns_completed=2,
        total_earnings=50000.0,
    )
