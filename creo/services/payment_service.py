import logging

from creo.storage.factories import get_payment_repo
from creo.models import Payment
from creo.services.base import CachedRepositoryService

logger = logging.getLogger(__name__)


class PaymentService(CachedRepositoryService[Payment]):
    def __init__(self):
        super().__init__()
        logger.debug("PaymentService initialized")

    def _make_repo(self):
        return get_payment_repo()

    @property
    def payments(self) -> list[Payment]:
        return self.items

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
