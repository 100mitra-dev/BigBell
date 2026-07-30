import json
from typing import Optional

from creo.storage.base import CampaignRepository
from creo.models import Campaign
from creo.storage.db import get_session
from creo.storage.db.orm_models import DbCampaign


class DbCampaignRepository(CampaignRepository):
    def list_all(self) -> list[Campaign]:
        with get_session() as session:
            return [_db_to_model(db) for db in session.query(DbCampaign).all()]

    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        with get_session() as session:
            db = session.get(DbCampaign, campaign_id)
            return _db_to_model(db) if db else None

    def add(self, campaign: Campaign):
        with get_session() as session:
            session.add(_model_to_db(campaign))
            session.commit()

    def delete(self, campaign_id: str):
        with get_session() as session:
            db = session.get(DbCampaign, campaign_id)
            if db:
                session.delete(db)
                session.commit()

    def save_all(self, campaigns: list[Campaign]):
        with get_session() as session:
            session.query(DbCampaign).delete()
            session.add_all([_model_to_db(c) for c in campaigns])
            session.commit()


def _db_to_model(db: DbCampaign) -> Campaign:
    return Campaign(
        id=db.id,
        title=db.title,
        brand=db.brand,
        description=db.description,
        requirements=json.loads(db.requirements),
        budget=db.budget,
        deadline=db.deadline,
        target_niches=json.loads(db.target_niches),
        target_languages=json.loads(db.target_languages),
        status=db.status,
        created_at=db.created_at,
        assigned_creators=json.loads(db.assigned_creators),
    )


def _model_to_db(campaign: Campaign) -> DbCampaign:
    return DbCampaign(
        id=campaign.id,
        title=campaign.title,
        brand=campaign.brand,
        description=campaign.description,
        requirements=json.dumps(campaign.requirements),
        budget=campaign.budget,
        deadline=campaign.deadline,
        target_niches=json.dumps(campaign.target_niches),
        target_languages=json.dumps(campaign.target_languages),
        status=campaign.status,
        created_at=campaign.created_at,
        assigned_creators=json.dumps(campaign.assigned_creators),
    )
