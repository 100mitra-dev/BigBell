from abc import ABC, abstractmethod
from typing import Optional

from creo.models import Creator, Campaign, Payment, FollowUpNote
from creo.runtime_config import get_data_source


class CreatorRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Creator]: ...

    @abstractmethod
    def get_by_id(self, creator_id: str) -> Optional[Creator]: ...

    @abstractmethod
    def add(self, creator: Creator): ...

    @abstractmethod
    def delete(self, creator_id: str): ...

    @abstractmethod
    def save_all(self, creators: list[Creator]): ...


class CampaignRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Campaign]: ...

    @abstractmethod
    def get_by_id(self, campaign_id: str) -> Optional[Campaign]: ...

    @abstractmethod
    def add(self, campaign: Campaign): ...

    @abstractmethod
    def delete(self, campaign_id: str): ...

    @abstractmethod
    def save_all(self, campaigns: list[Campaign]): ...


class PaymentRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Payment]: ...

    @abstractmethod
    def get_by_id(self, payment_id: str) -> Optional[Payment]: ...

    @abstractmethod
    def add(self, payment: Payment): ...

    @abstractmethod
    def delete(self, payment_id: str): ...

    @abstractmethod
    def save_all(self, payments: list[Payment]): ...


def get_creator_repo() -> CreatorRepository:
    source = get_data_source()
    if source == "api":
        from creo.storage.api.youtube import YouTubeCreatorRepository
        return YouTubeCreatorRepository()
    from creo.storage.json.creator_repo import JsonCreatorRepository
    return JsonCreatorRepository()


def get_campaign_repo() -> CampaignRepository:
    source = get_data_source()
    if source == "api":
        from creo.storage.api.instagram import InstagramCampaignRepository
        return InstagramCampaignRepository()
    from creo.storage.json.campaign_repo import JsonCampaignRepository
    return JsonCampaignRepository()


def get_payment_repo() -> PaymentRepository:
    source = get_data_source()
    if source == "api":
        from creo.storage.api.whatsapp import WhatsAppPaymentRepository
        return WhatsAppPaymentRepository()
    from creo.storage.json.payment_repo import JsonPaymentRepository
    return JsonPaymentRepository()


class FollowUpNoteRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[FollowUpNote]: ...

    @abstractmethod
    def get_by_id(self, note_id: str) -> Optional[FollowUpNote]: ...

    @abstractmethod
    def get_for_campaign(self, campaign_id: str) -> list[FollowUpNote]: ...

    @abstractmethod
    def add(self, note: FollowUpNote): ...

    @abstractmethod
    def delete(self, note_id: str): ...

    @abstractmethod
    def save_all(self, notes: list[FollowUpNote]): ...


def get_follow_up_note_repo() -> FollowUpNoteRepository:
    from creo.storage.json.note_repo import JsonFollowUpNoteRepository
    return JsonFollowUpNoteRepository()
