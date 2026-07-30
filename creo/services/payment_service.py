import logging
from typing import Optional

from creo.storage.base import get_payment_repo
from creo.models import Payment

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        self._payments: list[Payment] = []
        self.repo = get_payment_repo()
        logger.debug("PaymentService initialized")

    @property
    def payments(self) -> list[Payment]:
        if not self._payments:
            self._payments = self.repo.list_all()
        return self._payments

    def refresh(self):
        self._payments = self.repo.list_all()

    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        for p in self.payments:
            if p.id == payment_id:
                return p
        return None

    def add(self, payment: Payment):
        self.repo.add(payment)
        self.refresh()
        logger.info("Added payment %s (creator=%s, amount=%.2f)", payment.id, payment.creator_id, payment.amount)

    def delete(self, payment_id: str):
        self.repo.delete(payment_id)
        self.refresh()
        logger.info("Deleted payment %s", payment_id)

    def filter_by_status(self, status: str) -> list[Payment]:
        return [p for p in self.payments if p.status == status]

    def get_for_creator(self, creator_id: str) -> list[Payment]:
        return [p for p in self.payments if p.creator_id == creator_id]

    def get_for_campaign(self, campaign_id: str) -> list[Payment]:
        return [p for p in self.payments if p.campaign_id == campaign_id]

    def get_pending_count(self) -> int:
        return len(self.filter_by_status("pending"))

    def get_processed_count(self) -> int:
        return len(self.filter_by_status("processed"))

    def get_paid_count(self) -> int:
        return len(self.filter_by_status("paid"))

    def get_disputed_count(self) -> int:
        return len(self.filter_by_status("disputed"))

    def get_total_pending_amount(self) -> float:
        return sum(p.amount for p in self.filter_by_status("pending"))

    def get_total_paid_amount(self) -> float:
        return sum(p.amount for p in self.filter_by_status("paid"))

    def update_status(self, payment_id: str, status: str):
        payment = self.get_by_id(payment_id)
        if payment:
            payment.status = status
            self.repo.save_all(self.payments)
            logger.info("Updated payment %s status to %s", payment_id, status)
