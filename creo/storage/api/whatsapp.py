from typing import Optional
import random

from creo.storage.base import PaymentRepository
from creo.models import Payment


class WhatsAppPaymentRepository(PaymentRepository):
    @property
    def use_real_api(self) -> bool:
        from creo.utils.runtime_settings import get_whatsapp_key
        return bool(get_whatsapp_key())

    def list_all(self) -> list[Payment]:
        return self._mock_payments()

    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        for p in self.list_all():
            if p.id == payment_id:
                return p
        return None

    def add(self, payment: Payment):
        raise NotImplementedError("WhatsApp API repository is read-only")

    def delete(self, payment_id: str):
        raise NotImplementedError("WhatsApp API repository is read-only")

    def save_all(self, payments: list[Payment]):
        raise NotImplementedError("WhatsApp API repository is read-only")

    def _mock_payments(self) -> list[Payment]:
        return [
            Payment(id=f"wa_pay_{i}", creator_id=f"c_{i}", campaign_id=f"camp_{i % 5}", amount=random.uniform(5000, 50000), status=random.choice(["pending", "paid"]), due_date="2026-06-15")
            for i in range(5)
        ]
