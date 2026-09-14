"""Idempotent migration: reads JSON files and upserts into SQLite (safe to re-run)."""

import json
from datetime import datetime, timezone
from pathlib import Path

from creo.config import SAMPLE_DATA_DIR
from creo.storage.db import init_db, get_session
from creo.storage.db.orm_models import (
    DbCreator, DbCampaign, DbPayment, DbAssignment, DbFollowUpNote, DbSchemaRevision,
)
from creo.models import Creator, Campaign, Payment, CampaignAssignment, FollowUpNote

MIGRATION_REVISION = "json-baseline-v1"


def _load_json(filename: str) -> list[dict]:
    path: Path = SAMPLE_DATA_DIR / filename
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def _already_applied(session, revision: str) -> bool:
    return session.get(DbSchemaRevision, revision) is not None


def migrate():
    init_db()
    session = get_session()
    try:
        if _already_applied(session, MIGRATION_REVISION):
            print(f"Migration {MIGRATION_REVISION} already applied; skipping")
            return {"skipped": True, "revision": MIGRATION_REVISION}

        creators_data = _load_json("creators.json")
        for d in creators_data:
            c = Creator(**d)
            session.merge(DbCreator(
                id=c.id, name=c.name, email=c.email, phone=c.phone,
                primary_niche=c.primary_niche,
                secondary_niches=json.dumps(c.secondary_niches),
                primary_language=c.primary_language,
                secondary_languages=json.dumps(c.secondary_languages),
                platforms=json.dumps({k: v.model_dump() for k, v in c.platforms.items()}),
                content_quality_score=c.content_quality_score,
                profile_completeness=c.profile_completeness,
                avg_engagement_rate=c.avg_engagement_rate,
                status=c.status.value if hasattr(c.status, "value") else c.status,
                onboarded_at=c.onboarded_at,
                total_campaigns_completed=c.total_campaigns_completed,
                total_earnings=c.total_earnings,
                notes=c.notes, verified=c.verified,
                verification_score=c.verification_score,
                verification_issues=json.dumps(c.verification_issues),
                verified_at=c.verified_at,
                suggested_tags=json.dumps(c.suggested_tags),
                classified_at=c.classified_at,
            ))

        campaigns_data = _load_json("campaigns.json")
        for d in campaigns_data:
            c = Campaign(**d)
            session.merge(DbCampaign(
                id=c.id, title=c.title, brand=c.brand, description=c.description,
                requirements=json.dumps(c.requirements),
                budget=c.budget, deadline=c.deadline,
                target_niches=json.dumps(c.target_niches),
                target_languages=json.dumps(c.target_languages),
                status=c.status, created_at=c.created_at,
                assigned_creators=json.dumps(c.assigned_creators),
            ))

        payments_data = _load_json("payments.json")
        for d in payments_data:
            p = Payment(**d)
            session.merge(DbPayment(
                id=p.id, creator_id=p.creator_id, campaign_id=p.campaign_id,
                amount=p.amount, status=p.status, due_date=p.due_date,
                processed_at=p.processed_at, notes=p.notes,
            ))

        assignments_data = _load_json("assignments.json")
        for d in assignments_data:
            a = CampaignAssignment(**d)
            session.merge(DbAssignment(
                id=a.id, campaign_id=a.campaign_id, creator_id=a.creator_id,
                status=a.status.value if hasattr(a.status, "value") else a.status,
                score=a.score, assigned_at=a.assigned_at, updated_at=a.updated_at,
                notes=a.notes,
            ))

        notes_data = _load_json("follow_up_notes.json")
        for d in notes_data:
            n = FollowUpNote(**d)
            session.merge(DbFollowUpNote(id=n.id, campaign_id=n.campaign_id, note=n.note, created_at=n.created_at))

        session.merge(DbSchemaRevision(
            revision=MIGRATION_REVISION,
            applied_at=datetime.now(timezone.utc).isoformat(),
        ))
        session.commit()
        print(f"Migration complete: {len(creators_data)} creators, {len(campaigns_data)} campaigns, "
              f"{len(payments_data)} payments, {len(assignments_data)} assignments, {len(notes_data)} notes")
        return {"skipped": False, "revision": MIGRATION_REVISION}
    finally:
        session.close()


if __name__ == "__main__":
    migrate()
