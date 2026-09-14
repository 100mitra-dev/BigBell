import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from creo.storage.db import Base


class DbCreator(Base):
    __tablename__ = "creators"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String)
    email: Mapped[str] = mapped_column(sa.String)
    phone: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    primary_niche: Mapped[str] = mapped_column(sa.String)
    secondary_niches: Mapped[str] = mapped_column(sa.Text, default="[]")
    primary_language: Mapped[str] = mapped_column(sa.String)
    secondary_languages: Mapped[str] = mapped_column(sa.Text, default="[]")
    platforms: Mapped[str] = mapped_column(sa.Text, default="{}")
    content_quality_score: Mapped[float] = mapped_column(sa.Float, default=0.0)
    profile_completeness: Mapped[float] = mapped_column(sa.Float, default=0.0)
    avg_engagement_rate: Mapped[float] = mapped_column(sa.Float, default=0.0)
    status: Mapped[str] = mapped_column(sa.String, default="pending")
    onboarded_at: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    total_campaigns_completed: Mapped[int] = mapped_column(sa.Integer, default=0)
    total_earnings: Mapped[float] = mapped_column(sa.Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    verified: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    verification_score: Mapped[float] = mapped_column(sa.Float, default=0.0)
    verification_issues: Mapped[str] = mapped_column(sa.Text, default="[]")
    verified_at: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    suggested_tags: Mapped[str] = mapped_column(sa.Text, default="[]")
    classified_at: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class DbCampaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    title: Mapped[str] = mapped_column(sa.String)
    brand: Mapped[str] = mapped_column(sa.String)
    description: Mapped[str] = mapped_column(sa.Text)
    requirements: Mapped[str] = mapped_column(sa.Text, default="[]")
    budget: Mapped[float] = mapped_column(sa.Float)
    deadline: Mapped[str] = mapped_column(sa.String)
    target_niches: Mapped[str] = mapped_column(sa.Text, default="[]")
    target_languages: Mapped[str] = mapped_column(sa.Text, default="[]")
    status: Mapped[str] = mapped_column(sa.String, default="active")
    created_at: Mapped[str] = mapped_column(sa.String, default="")
    assigned_creators: Mapped[str] = mapped_column(sa.Text, default="[]")


class DbPayment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    creator_id: Mapped[str] = mapped_column(sa.String)
    campaign_id: Mapped[str] = mapped_column(sa.String)
    amount: Mapped[float] = mapped_column(sa.Float)
    status: Mapped[str] = mapped_column(sa.String, default="pending")
    due_date: Mapped[str] = mapped_column(sa.String, default="")
    processed_at: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class DbAssignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(sa.String)
    creator_id: Mapped[str] = mapped_column(sa.String)
    status: Mapped[str] = mapped_column(sa.String, default="matched")
    score: Mapped[float] = mapped_column(sa.Float, default=0.0)
    assigned_at: Mapped[str] = mapped_column(sa.String, default="")
    updated_at: Mapped[str] = mapped_column(sa.String, default="")
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class DbFollowUpNote(Base):
    __tablename__ = "follow_up_notes"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(sa.String)
    note: Mapped[str] = mapped_column(sa.Text)
    created_at: Mapped[str] = mapped_column(sa.String, default="")

class DbSchemaRevision(Base):
    __tablename__ = "schema_revisions"

    revision: Mapped[str] = mapped_column(sa.String, primary_key=True)
    applied_at: Mapped[str] = mapped_column(sa.String, default="")
