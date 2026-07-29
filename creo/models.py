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
    def tier(self) -> str:
        total = self.total_followers
        if total >= 500_000:
            return "Elite"
        elif total >= 100_000:
            return "Pro"
        elif total >= 10_000:
            return "Growth"
        return "Rising"


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


class FollowUpNote(BaseModel):
    id: str
    campaign_id: str
    note: str
    created_at: str = ""
