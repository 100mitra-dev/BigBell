from creo.utils.runtime_settings import get_data_source
from creo.storage.base import (
    AssignmentRepository,
    CampaignRepository,
    CreatorRepository,
    FollowUpNoteRepository,
    PaymentRepository,
)


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


def get_follow_up_note_repo() -> FollowUpNoteRepository:
    source = get_data_source()
    if source == "db":
        from creo.storage.db.note_repo import DbFollowUpNoteRepository
        return DbFollowUpNoteRepository()
    from creo.storage.json.note_repo import JsonFollowUpNoteRepository
    return JsonFollowUpNoteRepository()


def get_assignment_repo() -> AssignmentRepository:
    source = get_data_source()
    if source == "db":
        from creo.storage.db.assignment_repo import DbAssignmentRepository
        return DbAssignmentRepository()
    from creo.storage.json.assignment_repo import JsonAssignmentRepository
    return JsonAssignmentRepository()
