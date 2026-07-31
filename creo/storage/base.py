from abc import ABC, abstractmethod
from typing import Optional

from creo.models import Creator, Campaign, Payment, CampaignAssignment, FollowUpNote


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
