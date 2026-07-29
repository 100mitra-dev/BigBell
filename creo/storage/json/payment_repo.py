from typing import Optional

from creo.storage.base import PaymentRepository
from creo.models import Payment
from creo.utils.helpers import load_payments


class JsonPaymentRepository(PaymentRepository):
    _payments: list[Payment] = []

    def list_all(self) -> list[Payment]:
        if not self._payments:
            self._payments = load_payments()
        return self._payments

    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        for p in self.list_all():
            if p.id == payment_id:
                return p
        return None

    def add(self, payment: Payment):
        self._payments.append(payment)
        self._persist()

    def delete(self, payment_id: str):
        self._payments = [p for p in self._payments if p.id != payment_id]
        self._persist()

    def save_all(self, payments: list[Payment]):
        self._payments = payments
        self._persist()

    def _persist(self):
        from creo.utils.helpers import save_json
        save_json("payments.json", [p.model_dump() for p in self._payments])
