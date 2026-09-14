from __future__ import annotations
from creo.utils.runtime_settings import get_data_source
from creo.storage.base import (
    AssignmentRepository,
    CampaignRepository,
    CreatorRepository,
    FollowUpNoteRepository,
    PaymentRepository,
)


def _repo_for(kind: str):
    source = get_data_source()
    if kind == "creator":
        if source == "hybrid":
            from creo.storage.api.hybrid_creators import HybridCreatorRepository
            return HybridCreatorRepository()
        if source == "api":
            from creo.storage.api.youtube import YouTubeCreatorRepository
            return YouTubeCreatorRepository()
        if source == "db":
            from creo.storage.db.creator_repo import DbCreatorRepository
            return DbCreatorRepository()
        from creo.storage.json.creator_repo import JsonCreatorRepository
        return JsonCreatorRepository()
    if kind == "campaign":
        if source == "api":
            from creo.storage.api.instagram import InstagramCampaignRepository
            return InstagramCampaignRepository()
        if source == "db":
            from creo.storage.db.campaign_repo import DbCampaignRepository
            return DbCampaignRepository()
        from creo.storage.json.campaign_repo import JsonCampaignRepository
        return JsonCampaignRepository()
    if kind == "payment":
        if source == "api":
            from creo.storage.api.whatsapp import WhatsAppPaymentRepository
            return WhatsAppPaymentRepository()
        if source == "db":
            from creo.storage.db.payment_repo import DbPaymentRepository
            return DbPaymentRepository()
        from creo.storage.json.payment_repo import JsonPaymentRepository
        return JsonPaymentRepository()
    if kind == "note":
        if source == "db":
            from creo.storage.db.note_repo import DbFollowUpNoteRepository
            return DbFollowUpNoteRepository()
        from creo.storage.json.note_repo import JsonFollowUpNoteRepository
        return JsonFollowUpNoteRepository()
    if kind == "assignment":
        if source == "db":
            from creo.storage.db.assignment_repo import DbAssignmentRepository
            return DbAssignmentRepository()
        from creo.storage.json.assignment_repo import JsonAssignmentRepository
        return JsonAssignmentRepository()
    raise ValueError(f"Unknown repository kind: {kind}")


def get_creator_repo() -> CreatorRepository:
    return _repo_for("creator")

def get_campaign_repo() -> CampaignRepository:
    return _repo_for("campaign")


def get_payment_repo() -> PaymentRepository:
    return _repo_for("payment")


def get_follow_up_note_repo() -> FollowUpNoteRepository:
    return _repo_for("note")


def get_assignment_repo() -> AssignmentRepository:
    return _repo_for("assignment")


def get_discovery_status() -> dict:
    """Non-secret status of all discovery data sources (never returns keys)."""
    from creo.utils.runtime_settings import get_data_source, get_discovery_sources
    status = {
        "data_source": get_data_source(),
        "discovery_sources": get_discovery_sources(),
    }
    for name, mod_name in [
        ("meta", "creo.storage.api.meta_config"),
        ("modash", "creo.storage.api.modash"),
        ("youtube", "creo.storage.api.youtube"),
        ("instagram", "creo.storage.api.instagram_creators"),
    ]:
        try:
            mod = __import__(mod_name, fromlist=["meta_status", "ModashCreatorRepository", "YouTubeCreatorRepository", "InstagramCreatorRepository"])
            status_fn = getattr(mod, "meta_status", None) or getattr(mod, "status", None)
            if status_fn:
                status[name] = status_fn()
            else:
                cls = getattr(mod, "ModashCreatorRepository") if name == "modash" else getattr(mod, "YouTubeCreatorRepository") if name == "youtube" else getattr(mod, "InstagramCreatorRepository")
                status[name] = {"configured": bool(getattr(cls(), "use_real_api", False))}
        except Exception as exc:
            status[name] = {"error": str(exc)}
    return status
