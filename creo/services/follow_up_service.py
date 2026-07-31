import logging

from creo.storage.factories import get_follow_up_note_repo
from creo.models import FollowUpNote
from creo.services.base import CachedRepositoryService

logger = logging.getLogger(__name__)


class FollowUpNoteService(CachedRepositoryService[FollowUpNote]):
    def __init__(self):
        super().__init__()
        logger.debug("FollowUpNoteService initialized")

    def _make_repo(self):
        return get_follow_up_note_repo()

    @property
    def notes(self) -> list[FollowUpNote]:
        return self.items

    def get_for_campaign(self, campaign_id: str) -> list[FollowUpNote]:
        return self.repo.get_for_campaign(campaign_id)
