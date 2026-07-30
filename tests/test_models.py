from creo.models import Creator, Campaign, PlatformInfo, CreatorStatus, AssignmentStatus, CampaignAssignment


class TestCreatorTier:
    def test_rising_tier(self):
        c = Creator(id="c1", name="Rising", email="r@x.com", primary_niche="Tech", primary_language="English",
                    platforms={"ig": PlatformInfo(handle="@r", followers=5000)})
        assert c.tier == "Rising"

    def test_growth_tier(self):
        c = Creator(id="c2", name="Growth", email="g@x.com", primary_niche="Tech", primary_language="English",
                    platforms={"ig": PlatformInfo(handle="@g", followers=50000)})
        assert c.tier == "Growth"

    def test_pro_tier(self):
        c = Creator(id="c3", name="Pro", email="p@x.com", primary_niche="Tech", primary_language="English",
                    platforms={"ig": PlatformInfo(handle="@p", followers=250000)})
        assert c.tier == "Pro"

    def test_elite_tier(self):
        c = Creator(id="c4", name="Elite", email="e@x.com", primary_niche="Tech", primary_language="English",
                    platforms={"ig": PlatformInfo(handle="@e", followers=1_000_000)})
        assert c.tier == "Elite"


class TestCreatorProperties:
    def test_total_followers(self, sample_creator):
        assert sample_creator.total_followers == 150000 + 80000

    def test_total_followers_empty(self, minimal_creator):
        assert minimal_creator.total_followers == 0

    def test_verified_count(self, sample_creator):
        assert sample_creator.verified_count == 2

    def test_verified_count_mixed(self):
        c = Creator(id="c5", name="Mixed", email="m@x.com", primary_niche="Art", primary_language="English",
                    platforms={
                        "ig": PlatformInfo(handle="@a", followers=100, verified=True),
                        "yt": PlatformInfo(handle="@b", followers=200, verified=False),
                    })
        assert c.verified_count == 1

    def test_platform_count(self, sample_creator):
        assert sample_creator.platform_count == 2


class TestCreatorStatus:
    def test_status_enum_values(self):
        assert CreatorStatus.PENDING.value == "pending"
        assert CreatorStatus.ACTIVE.value == "active"
        assert CreatorStatus.INACTIVE.value == "inactive"
        assert CreatorStatus.REJECTED.value == "rejected"
        assert CreatorStatus.ONBOARDING.value == "onboarding"


class TestAssignmentStatus:
    def test_status_enum_values(self):
        assert AssignmentStatus.MATCHED.value == "matched"
        assert AssignmentStatus.INVITED.value == "invited"
        assert AssignmentStatus.ACCEPTED.value == "accepted"
        assert AssignmentStatus.BRIEF_SENT.value == "brief_sent"
        assert AssignmentStatus.CONTENT_RECEIVED.value == "content_received"
        assert AssignmentStatus.APPROVED.value == "approved"
        assert AssignmentStatus.PAID.value == "paid"
        assert AssignmentStatus.REJECTED.value == "rejected"


class TestCampaign:
    def test_campaign_creation(self, sample_campaign):
        assert sample_campaign.title == "Summer Gaming Fest"
        assert sample_campaign.brand == "GameCo"
        assert sample_campaign.budget == 500000.0
        assert len(sample_campaign.target_niches) == 2

    def test_campaign_defaults(self):
        c = Campaign(id="c1", title="Test", brand="B", description="D", budget=100, deadline="2026-01-01")
        assert c.status == "active"
        assert c.requirements == []
        assert c.assigned_creators == []


class TestCampaignAssignment:
    def test_assignment_defaults(self):
        a = CampaignAssignment(id="a1", campaign_id="c1", creator_id="cr1")
        assert a.status == AssignmentStatus.MATCHED
        assert a.score == 0.0
        assert a.notes is None

    def test_assignment_with_values(self):
        a = CampaignAssignment(id="a2", campaign_id="c2", creator_id="cr2",
                               status=AssignmentStatus.APPROVED, score=8.5, notes="Great work")
        assert a.status == AssignmentStatus.APPROVED
        assert a.score == 8.5
        assert a.notes == "Great work"
