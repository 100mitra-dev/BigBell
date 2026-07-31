import logging
from typing import Optional
import uuid

from creo.storage.factories import get_assignment_repo
from creo.models import CampaignAssignment, AssignmentStatus
from creo.utils.dates import today_str
from creo.services.base import CachedRepositoryService

logger = logging.getLogger(__name__)


NEXT_STATUS: dict[AssignmentStatus, Optional[AssignmentStatus]] = {
    AssignmentStatus.MATCHED: AssignmentStatus.INVITED,
    AssignmentStatus.INVITED: AssignmentStatus.ACCEPTED,
    AssignmentStatus.ACCEPTED: AssignmentStatus.BRIEF_SENT,
    AssignmentStatus.BRIEF_SENT: AssignmentStatus.CONTENT_RECEIVED,
    AssignmentStatus.CONTENT_RECEIVED: AssignmentStatus.APPROVED,
    AssignmentStatus.APPROVED: AssignmentStatus.PAID,
    AssignmentStatus.PAID: None,
    AssignmentStatus.REJECTED: None,
}


STATUS_COLORS: dict[str, str] = {
    "matched": "#3498DB", "invited": "#9B59B6", "accepted": "#1ABC9C",
    "brief_sent": "#E67E22", "content_received": "#F1C40F",
    "approved": "#2ECC71", "paid": "#27AE60", "rejected": "#E74C3C",
}

STATUS_LABELS: dict[AssignmentStatus, str] = {
    AssignmentStatus.MATCHED: "Matched",
    AssignmentStatus.INVITED: "Invited",
    AssignmentStatus.ACCEPTED: "Accepted",
    AssignmentStatus.BRIEF_SENT: "Brief Sent",
    AssignmentStatus.CONTENT_RECEIVED: "Content Received",
    AssignmentStatus.APPROVED: "Approved",
    AssignmentStatus.PAID: "Paid",
    AssignmentStatus.REJECTED: "Rejected",
}


class AssignmentService(CachedRepositoryService[CampaignAssignment]):
    def __init__(self):
        super().__init__()
        logger.debug("AssignmentService initialized")

    def _make_repo(self):
        return get_assignment_repo()

    @property
    def assignments(self) -> list[CampaignAssignment]:
        return self.items

    def get_for_campaign(self, campaign_id: str) -> list[CampaignAssignment]:
        return [a for a in self.assignments if a.campaign_id == campaign_id]

    def get_for_creator(self, creator_id: str) -> list[CampaignAssignment]:
        return [a for a in self.assignments if a.creator_id == creator_id]

    def get_for_campaign_creator(self, campaign_id: str, creator_id: str) -> Optional[CampaignAssignment]:
        for a in self.assignments:
            if a.campaign_id == campaign_id and a.creator_id == creator_id:
                return a
        return None

    def is_assigned(self, campaign_id: str, creator_id: str) -> bool:
        return self.get_for_campaign_creator(campaign_id, creator_id) is not None

    def assign(self, campaign_id: str, creator_id: str, score: float = 0.0) -> CampaignAssignment:
        existing = self.get_for_campaign_creator(campaign_id, creator_id)
        if existing:
            return existing
        assignment = CampaignAssignment(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            creator_id=creator_id,
            score=score,
            assigned_at=today_str(),
            updated_at=today_str(),
        )
        self.repo.add(assignment)
        self.refresh()
        logger.info("Assigned creator %s to campaign %s (score=%.1f)", creator_id, campaign_id, score)
        return assignment

    def unassign(self, campaign_id: str, creator_id: str):
        existing = self.get_for_campaign_creator(campaign_id, creator_id)
        if existing:
            self.repo.delete(existing.id)
            self.refresh()
            logger.info("Unassigned creator %s from campaign %s", creator_id, campaign_id)

    def update_status(self, assignment_id: str, new_status: AssignmentStatus):
        all_a = self.repo.list_all()
        for a in all_a:
            if a.id == assignment_id:
                a.status = new_status
                a.updated_at = today_str()
                break
        self.repo.save_all(all_a)
        self.refresh()

    def advance_status(self, assignment_id: str) -> Optional[AssignmentStatus]:
        a = self.repo.get_by_id(assignment_id)
        if not a:
            logger.warning("advance_status: assignment %s not found", assignment_id)
            return None
        nxt = NEXT_STATUS.get(a.status)
        if nxt:
            self.update_status(assignment_id, nxt)
            logger.info("Advanced assignment %s from %s to %s", assignment_id, a.status.value, nxt.value)
        return nxt

    def get_campaign_summary(self, campaign_id: str) -> dict[str, int]:
        assignments = self.get_for_campaign(campaign_id)
        summary: dict[str, int] = {}
        for a in assignments:
            summary[a.status.value] = summary.get(a.status.value, 0) + 1
        return summary
