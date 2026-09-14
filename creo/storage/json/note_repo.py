from pathlib import Path
from typing import Optional

from creo.config import SAMPLE_DATA_DIR
from creo.models import FollowUpNote
from creo.utils.json_io import save_json


class JsonFollowUpNoteRepository:
    def __init__(self):
        self.path: Path = SAMPLE_DATA_DIR / "follow_up_notes.json"

    def list_all(self) -> list[FollowUpNote]:
        return [FollowUpNote(**d) for d in load_json("follow_up_notes.json")]

    def get_by_id(self, note_id: str) -> Optional[FollowUpNote]:
        for n in self.list_all():
            if n.id == note_id:
                return n
        return None

    def get_for_campaign(self, campaign_id: str) -> list[FollowUpNote]:
        return [n for n in self.list_all() if n.campaign_id == campaign_id]

    def add(self, note: FollowUpNote):
        notes = self.list_all()
        notes.append(note)
        self.save_all(notes)

    def delete(self, note_id: str):
        notes = self.list_all()
        notes = [n for n in notes if n.id != note_id]
        self.save_all(notes)

    def save_all(self, notes: list[FollowUpNote]):
        save_json("follow_up_notes.json", [n.model_dump() for n in notes])
