from pydantic import BaseModel
from typing import Optional
from enum import Enum


class CreatorStatus(str, Enum):
    PENDING = "pending"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REJECTED = "rejected"


class PlatformInfo(BaseModel):
    handle: str
    followers: int
    verified: bool = False


class Creator(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    primary_niche: str
    secondary_niches: list[str] = []
    primary_language: str
    secondary_languages: list[str] = []
    platforms: dict[str, PlatformInfo] = {}
    content_quality_score: float = 0.0
    profile_completeness: float = 0.0
    avg_engagement_rate: float = 0.0
    status: CreatorStatus = CreatorStatus.PENDING
    onboarded_at: Optional[str] = None
    total_campaigns_completed: int = 0
    total_earnings: float = 0.0
    notes: Optional[str] = None
    verified: bool = False
    verification_score: float = 0.0
    verification_issues: list[str] = []
    verified_at: Optional[str] = None
    suggested_tags: list[str] = []
    classified_at: Optional[str] = None
    region: Optional[str] = None

    @property
    def total_followers(self) -> int:
        return sum(p.followers for p in self.platforms.values())

    @property
    def verified_count(self) -> int:
        return sum(1 for p in self.platforms.values() if p.verified)

    @property
    def platform_count(self) -> int:
        return len(self.platforms)

    @property
    def handles(self) -> dict[str, str]:
        """Platform -> handle mapping."""
        return {k: v.handle for k, v in self.platforms.items()}

    @property
    def tier(self) -> str:
        total = self.total_followers
        if total >= 500_000:
            return "Elite"
        elif total >= 100_000:
            return "Pro"
        elif total >= 10_000:
            return "Growth"
        return "Rising"
    @property
    def niches(self) -> list[str]:
        """All niches (primary + secondary) for matching."""
        return [self.primary_niche] + self.secondary_niches

    @property
    def languages(self) -> list[str]:
        """All languages (primary + secondary) for matching."""
        return [self.primary_language] + self.secondary_languages

    def to_card_dict(self) -> dict:
        """Compact card payload used by API + UI discovery."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "primary_niche": self.primary_niche,
            "secondary_niches": self.secondary_niches,
            "niches": self.niches,
            "primary_language": self.primary_language,
            "secondary_languages": self.secondary_languages,
            "languages": self.languages,
            "region": self.region,
            "regions": [self.region] if self.region else [],
            "display_region": self.region or "",
            "total_followers": self.total_followers,
            "total_subscribers": self.total_followers,  # alias for total_followers
            "avg_engagement_rate": self.avg_engagement_rate,
            "content_quality_score": self.content_quality_score,
            "profile_completeness": self.profile_completeness,
            "status": self.status.value if hasattr(self.status, "value") else self.status,
            "tier": self.tier,
            "verified": self.verified,
            "verification_score": self.verification_score,
            "engagement_rate": self.avg_engagement_rate,
            "platforms": {k: {"handle": v.handle, "followers": v.followers, "verified": v.verified} for k, v in self.platforms.items()},
            "handles": {k: v.handle for k, v in self.platforms.items()},
            "followers_by_platform": {k: v.followers for k, v in self.platforms.items()},
        }

class Campaign(BaseModel):
    id: str
    title: str
    brand: str
    description: str
    requirements: list[str] = []
    budget: float
    deadline: str
    target_niches: list[str] = []
    target_languages: list[str] = []
    status: str = "active"
    created_at: str = ""
    assigned_creators: list[str] = []


class Application(BaseModel):
    id: str
    creator_id: str
    campaign_id: str
    status: str = "pending"
    applied_at: str = ""
    reviewed_at: Optional[str] = None
    score: Optional[float] = None
    ai_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None
    source: str = "email"  # email | whatsapp
    letter: Optional[str] = None


class FAQ(BaseModel):
    id: str
    question: str
    answer: str
    category: str


class Payment(BaseModel):
    id: str
    creator_id: str
    campaign_id: str
    amount: float
    status: str = "pending"
    due_date: str = ""
    processed_at: Optional[str] = None
    notes: Optional[str] = None


class AssignmentStatus(str, Enum):
    MATCHED = "matched"
    INVITED = "invited"
    ACCEPTED = "accepted"
    BRIEF_SENT = "brief_sent"
    CONTENT_RECEIVED = "content_received"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"


class CampaignAssignment(BaseModel):
    id: str
    campaign_id: str
    creator_id: str
    status: AssignmentStatus = AssignmentStatus.MATCHED
    score: float = 0.0
    assigned_at: str = ""
    updated_at: str = ""
    notes: Optional[str] = None


class FollowUpNote(BaseModel):
    id: str
    campaign_id: str
    note: str
    created_at: str = ""


class ChatMessage(BaseModel):
    id: str
    creator_id: str
    role: str  # "creator" | "agent"
    content: str
    channel: str = "whatsapp"  # whatsapp | email | in_app
    kind: str = "manual"  # incoming | auto | manual
    faq_id: Optional[str] = None
    confidence: Optional[str] = None
    created_at: str = ""
