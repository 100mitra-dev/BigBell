from typing import Optional

from creo.storage.base import PaymentRepository
from creo.models import Payment
from creo.storage.db import get_session
from creo.storage.db.orm_models import DbPayment


class DbPaymentRepository(PaymentRepository):
    def list_all(self) -> list[Payment]:
        with get_session() as session:
            return [_db_to_model(db) for db in session.query(DbPayment).all()]

    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        with get_session() as session:
            db = session.get(DbPayment, payment_id)
            return _db_to_model(db) if db else None

    def add(self, payment: Payment):
        with get_session() as session:
            session.add(_model_to_db(payment))
            session.commit()

    def delete(self, payment_id: str):
        with get_session() as session:
            db = session.get(DbPayment, payment_id)
            if db:
                session.delete(db)
                session.commit()

    def save_all(self, payments: list[Payment]):
        with get_session() as session:
            session.query(DbPayment).delete()
            session.add_all([_model_to_db(p) for p in payments])
            session.commit()


def _db_to_model(db: DbPayment) -> Payment:
    return Payment(
        id=db.id,
        creator_id=db.creator_id,
        campaign_id=db.campaign_id,
        amount=db.amount,
        status=db.status,
        due_date=db.due_date,
        processed_at=db.processed_at,
        notes=db.notes,
    )


def _model_to_db(payment: Payment) -> DbPayment:
    return DbPayment(
        id=payment.id,
        creator_id=payment.creator_id,
        campaign_id=payment.campaign_id,
        amount=payment.amount,
        status=payment.status,
        due_date=payment.due_date,
        processed_at=payment.processed_at,
        notes=payment.notes,
    )
