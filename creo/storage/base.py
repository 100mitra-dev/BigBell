from abc import ABC, abstractmethod
from typing import Optional

from creo.models import Creator, Campaign, Payment, CampaignAssignment, FollowUpNote
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
    if source == "db":
        from creo.storage.db.creator_repo import DbCreatorRepository
        return DbCreatorRepository()
    from creo.storage.json.creator_repo import JsonCreatorRepository
    return JsonCreatorRepository()


def get_campaign_repo() -> CampaignRepository:
    source = get_data_source()
    if source == "api":
        from creo.storage.api.instagram import InstagramCampaignRepository
        return InstagramCampaignRepository()
    if source == "db":
        from creo.storage.db.campaign_repo import DbCampaignRepository
        return DbCampaignRepository()
    from creo.storage.json.campaign_repo import JsonCampaignRepository
    return JsonCampaignRepository()


def get_payment_repo() -> PaymentRepository:
    source = get_data_source()
    if source == "api":
        from creo.storage.api.whatsapp import WhatsAppPaymentRepository
        return WhatsAppPaymentRepository()
    if source == "db":
        from creo.storage.db.payment_repo import DbPaymentRepository
        return DbPaymentRepository()
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
    source = get_data_source()
    if source == "db":
        from creo.storage.db.note_repo import DbFollowUpNoteRepository
        return DbFollowUpNoteRepository()
    from creo.storage.json.note_repo import JsonFollowUpNoteRepository
    return JsonFollowUpNoteRepository()


class AssignmentRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[CampaignAssignment]: ...

    @abstractmethod
    def get_by_id(self, assignment_id: str) -> Optional[CampaignAssignment]: ...

    @abstractmethod
    def get_for_campaign(self, campaign_id: str) -> list[CampaignAssignment]: ...

    @abstractmethod
    def get_for_creator(self, creator_id: str) -> list[CampaignAssignment]: ...

    @abstractmethod
    def add(self, assignment: CampaignAssignment): ...

    @abstractmethod
    def delete(self, assignment_id: str): ...

    @abstractmethod
    def save_all(self, assignments: list[CampaignAssignment]): ...


def get_assignment_repo() -> AssignmentRepository:
    source = get_data_source()
    if source == "db":
        from creo.storage.db.assignment_repo import DbAssignmentRepository
        return DbAssignmentRepository()
    from creo.storage.json.assignment_repo import JsonAssignmentRepository
    return JsonAssignmentRepository()
