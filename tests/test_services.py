from creo.models import AssignmentStatus, CreatorStatus
from creo.services.assignment_service import NEXT_STATUS, STATUS_LABELS


class TestAssignmentStatusTransitions:
    def test_next_status_from_matched(self):
        assert NEXT_STATUS[AssignmentStatus.MATCHED] == AssignmentStatus.INVITED

    def test_next_status_from_invited(self):
        assert NEXT_STATUS[AssignmentStatus.INVITED] == AssignmentStatus.ACCEPTED

    def test_next_status_from_accepted(self):
        assert NEXT_STATUS[AssignmentStatus.ACCEPTED] == AssignmentStatus.BRIEF_SENT

    def test_next_status_from_brief_sent(self):
        assert NEXT_STATUS[AssignmentStatus.BRIEF_SENT] == AssignmentStatus.CONTENT_RECEIVED

    def test_next_status_from_content_received(self):
        assert NEXT_STATUS[AssignmentStatus.CONTENT_RECEIVED] == AssignmentStatus.APPROVED

    def test_next_status_from_approved(self):
        assert NEXT_STATUS[AssignmentStatus.APPROVED] == AssignmentStatus.PAID

    def test_next_status_from_paid_is_none(self):
        assert NEXT_STATUS[AssignmentStatus.PAID] is None

    def test_next_status_from_rejected_is_none(self):
        assert NEXT_STATUS[AssignmentStatus.REJECTED] is None

    def test_all_statuses_have_labels(self):
        for status in AssignmentStatus:
            assert status in STATUS_LABELS
            assert isinstance(STATUS_LABELS[status], str)
            assert len(STATUS_LABELS[status]) > 0

    def test_all_statuses_covered_in_next(self):
        for status in AssignmentStatus:
            assert status in NEXT_STATUS


class TestCreatorService:
    def test_search_by_name(self, creator_service):
        results = creator_service.search("Priya")
        assert len(results) >= 1
        assert any("Priya" in c.name for c in results)

    def test_search_by_niche(self, creator_service):
        results = creator_service.search("Gaming")
        assert len(results) >= 1

    def test_search_by_email(self, creator_service):
        results = creator_service.search("priya.sharma@email.com")
        assert len(results) >= 1

    def test_filter_by_status(self, creator_service):
        active = creator_service.filter_by_status("active")
        assert len(active) >= 1
        assert all(c.status.value == "active" for c in active)

    def test_filter_by_niche(self, creator_service):
        gaming = creator_service.filter_by_niche("Gaming")
        assert len(gaming) >= 1

    def test_get_count_methods(self, creator_service):
        assert creator_service.get_active_count() >= 1
        assert creator_service.get_pending_count() >= 0
        assert creator_service.get_inactive_count() >= 1

    def test_refresh(self, creator_service):
        before = len(creator_service.creators)
        creator_service.refresh()
        after = len(creator_service.creators)
        assert before == after
