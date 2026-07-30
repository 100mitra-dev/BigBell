import json
from typing import Optional

from creo.storage.base import CreatorRepository
from creo.models import Creator, PlatformInfo
from creo.storage.db import get_session
from creo.storage.db.orm_models import DbCreator


class DbCreatorRepository(CreatorRepository):
    def list_all(self) -> list[Creator]:
        with get_session() as session:
            return [_db_to_model(db) for db in session.query(DbCreator).all()]

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        with get_session() as session:
            db = session.get(DbCreator, creator_id)
            return _db_to_model(db) if db else None

    def add(self, creator: Creator):
        with get_session() as session:
            session.add(_model_to_db(creator))
            session.commit()

    def delete(self, creator_id: str):
        with get_session() as session:
            db = session.get(DbCreator, creator_id)
            if db:
                session.delete(db)
                session.commit()

    def save_all(self, creators: list[Creator]):
        with get_session() as session:
            session.query(DbCreator).delete()
            session.add_all([_model_to_db(c) for c in creators])
            session.commit()


def _db_to_model(db: DbCreator) -> Creator:
    return Creator(
        id=db.id,
        name=db.name,
        email=db.email,
        phone=db.phone,
        primary_niche=db.primary_niche,
        secondary_niches=json.loads(db.secondary_niches),
        primary_language=db.primary_language,
        secondary_languages=json.loads(db.secondary_languages),
        platforms={k: PlatformInfo(**v) for k, v in json.loads(db.platforms).items()},
        content_quality_score=db.content_quality_score,
        profile_completeness=db.profile_completeness,
        avg_engagement_rate=db.avg_engagement_rate,
        status=db.status,
        onboarded_at=db.onboarded_at,
        total_campaigns_completed=db.total_campaigns_completed,
        total_earnings=db.total_earnings,
        notes=db.notes,
        verified=db.verified,
        verification_score=db.verification_score,
        verification_issues=json.loads(db.verification_issues),
        verified_at=db.verified_at,
        suggested_tags=json.loads(db.suggested_tags),
        classified_at=db.classified_at,
    )


def _model_to_db(creator: Creator) -> DbCreator:
    return DbCreator(
        id=creator.id,
        name=creator.name,
        email=creator.email,
        phone=creator.phone,
        primary_niche=creator.primary_niche,
        secondary_niches=json.dumps(creator.secondary_niches),
        primary_language=creator.primary_language,
        secondary_languages=json.dumps(creator.secondary_languages),
        platforms=json.dumps({k: v.model_dump() for k, v in creator.platforms.items()}),
        content_quality_score=creator.content_quality_score,
        profile_completeness=creator.profile_completeness,
        avg_engagement_rate=creator.avg_engagement_rate,
        status=creator.status.value if hasattr(creator.status, 'value') else creator.status,
        onboarded_at=creator.onboarded_at,
        total_campaigns_completed=creator.total_campaigns_completed,
        total_earnings=creator.total_earnings,
        notes=creator.notes,
        verified=creator.verified,
        verification_score=creator.verification_score,
        verification_issues=json.dumps(creator.verification_issues),
        verified_at=creator.verified_at,
        suggested_tags=json.dumps(creator.suggested_tags),
        classified_at=creator.classified_at,
    )
