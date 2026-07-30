from typing import Optional

from creo.storage.base import AssignmentRepository
from creo.models import CampaignAssignment
from creo.storage.db import get_session
from creo.storage.db.orm_models import DbAssignment


class DbAssignmentRepository(AssignmentRepository):
    def list_all(self) -> list[CampaignAssignment]:
        with get_session() as session:
            return [_db_to_model(db) for db in session.query(DbAssignment).all()]

    def get_by_id(self, assignment_id: str) -> Optional[CampaignAssignment]:
        with get_session() as session:
            db = session.get(DbAssignment, assignment_id)
            return _db_to_model(db) if db else None

    def get_for_campaign(self, campaign_id: str) -> list[CampaignAssignment]:
        with get_session() as session:
            return [
                _db_to_model(db)
                for db in session.query(DbAssignment).filter_by(campaign_id=campaign_id).all()
            ]

    def get_for_creator(self, creator_id: str) -> list[CampaignAssignment]:
        with get_session() as session:
            return [
                _db_to_model(db)
                for db in session.query(DbAssignment).filter_by(creator_id=creator_id).all()
            ]

    def add(self, assignment: CampaignAssignment):
        with get_session() as session:
            session.add(_model_to_db(assignment))
            session.commit()

    def delete(self, assignment_id: str):
        with get_session() as session:
            db = session.get(DbAssignment, assignment_id)
            if db:
                session.delete(db)
                session.commit()

    def save_all(self, assignments: list[CampaignAssignment]):
        with get_session() as session:
            session.query(DbAssignment).delete()
            session.add_all([_model_to_db(a) for a in assignments])
            session.commit()


def _db_to_model(db: DbAssignment) -> CampaignAssignment:
    return CampaignAssignment(
        id=db.id,
        campaign_id=db.campaign_id,
        creator_id=db.creator_id,
        status=db.status,
        score=db.score,
        assigned_at=db.assigned_at,
        updated_at=db.updated_at,
        notes=db.notes,
    )


def _model_to_db(assignment: CampaignAssignment) -> DbAssignment:
    return DbAssignment(
        id=assignment.id,
        campaign_id=assignment.campaign_id,
        creator_id=assignment.creator_id,
        status=assignment.status.value if hasattr(assignment.status, 'value') else assignment.status,
        score=assignment.score,
        assigned_at=assignment.assigned_at,
        updated_at=assignment.updated_at,
        notes=assignment.notes,
    )
