from typing import Optional

from creo.storage.base import get_follow_up_note_repo
from creo.models import FollowUpNote


class FollowUpNoteService:
    def __init__(self):
        self._notes: list[FollowUpNote] = []
        self.repo = get_follow_up_note_repo()

    @property
    def notes(self) -> list[FollowUpNote]:
        if not self._notes:
            self._notes = self.repo.list_all()
        return self._notes

    def refresh(self):
        self._notes = self.repo.list_all()

    def get_for_campaign(self, campaign_id: str) -> list[FollowUpNote]:
        return self.repo.get_for_campaign(campaign_id)

    def add(self, note: FollowUpNote):
        self.repo.add(note)
        self.refresh()

    def delete(self, note_id: str):
        self.repo.delete(note_id)
        self.refresh()
