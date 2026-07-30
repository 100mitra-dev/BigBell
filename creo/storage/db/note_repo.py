from typing import Optional

from creo.storage.base import FollowUpNoteRepository
from creo.models import FollowUpNote
from creo.storage.db import get_session
from creo.storage.db.orm_models import DbFollowUpNote


class DbFollowUpNoteRepository(FollowUpNoteRepository):
    def list_all(self) -> list[FollowUpNote]:
        with get_session() as session:
            return [_db_to_model(db) for db in session.query(DbFollowUpNote).all()]

    def get_by_id(self, note_id: str) -> Optional[FollowUpNote]:
        with get_session() as session:
            db = session.get(DbFollowUpNote, note_id)
            return _db_to_model(db) if db else None

    def get_for_campaign(self, campaign_id: str) -> list[FollowUpNote]:
        with get_session() as session:
            return [
                _db_to_model(db)
                for db in session.query(DbFollowUpNote).filter_by(campaign_id=campaign_id).all()
            ]

    def add(self, note: FollowUpNote):
        with get_session() as session:
            session.add(_model_to_db(note))
            session.commit()

    def delete(self, note_id: str):
        with get_session() as session:
            db = session.get(DbFollowUpNote, note_id)
            if db:
                session.delete(db)
                session.commit()

    def save_all(self, notes: list[FollowUpNote]):
        with get_session() as session:
            session.query(DbFollowUpNote).delete()
            session.add_all([_model_to_db(n) for n in notes])
            session.commit()


def _db_to_model(db: DbFollowUpNote) -> FollowUpNote:
    return FollowUpNote(
        id=db.id,
        campaign_id=db.campaign_id,
        note=db.note,
        created_at=db.created_at,
    )


def _model_to_db(note: FollowUpNote) -> DbFollowUpNote:
    return DbFollowUpNote(
        id=note.id,
        campaign_id=note.campaign_id,
        note=note.note,
        created_at=note.created_at,
    )
