from pathlib import Path
from typing import Optional

from creo.config import SAMPLE_DATA_DIR
from creo.models import CampaignAssignment
from creo.utils.json_io import load_json, save_json

class JsonAssignmentRepository:
    def __init__(self):
        self.path: Path = SAMPLE_DATA_DIR / "assignments.json"

    def list_all(self) -> list[CampaignAssignment]:
        return [CampaignAssignment(**d) for d in load_json("assignments.json")]

    def get_by_id(self, assignment_id: str) -> Optional[CampaignAssignment]:
        for a in self.list_all():
            if a.id == assignment_id:
                return a
        return None

    def get_for_campaign(self, campaign_id: str) -> list[CampaignAssignment]:
        return [a for a in self.list_all() if a.campaign_id == campaign_id]

    def get_for_creator(self, creator_id: str) -> list[CampaignAssignment]:
        return [a for a in self.list_all() if a.creator_id == creator_id]

    def add(self, assignment: CampaignAssignment):
        items = self.list_all()
        items.append(assignment)
        self.save_all(items)

    def delete(self, assignment_id: str):
        items = self.list_all()
        items = [a for a in items if a.id != assignment_id]
        self.save_all(items)

    def save_all(self, assignments: list[CampaignAssignment]):
        save_json("assignments.json", [a.model_dump(mode="json") for a in assignments])
