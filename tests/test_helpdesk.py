import pytest

from creo.rag.faq_kb import (
    FAQKnowledgeBase,
    _parse_faq_text,
    confidence_for_distance,
    generate_faq_pdf_bytes,
    parse_faq_pdf,
)
from creo.services.helpdesk_service import HelpdeskService
from creo.utils.json_io import load_faqs


class TestFAQTextParsing:
    def test_parse_basic_q_a(self):
        faqs = _parse_faq_text(
            "Q1: How do I apply for campaigns?\n"
            "A1: You can apply from your dashboard.\n"
            "Q2: When will I get paid?\n"
            "A: Payments take 15-30 days."
        )
        assert len(faqs) == 2
        assert faqs[0].question == "How do I apply for campaigns?"
        assert faqs[1].question == "When will I get paid?"

    def test_parse_numbered_variants(self):
        faqs = _parse_faq_text(
            "Question 1: What is onboarding?\n"
            "Answer: Document verification.\n"
            "Question 2: Payment methods?\n"
            "Answer: NEFT and IMPS."
        )
        assert len(faqs) == 2

    def test_parse_empty_returns_none(self):
        assert _parse_faq_text("Just some prose without any structure.") == []


class TestFAQPDF:
    def test_pdf_round_trip(self):
        pdf = generate_faq_pdf_bytes(load_faqs()[:5])
        assert pdf.startswith(b"%PDF")
        faqs = parse_faq_pdf(pdf)
        assert len(faqs) == 5
        assert faqs[0].question == load_faqs()[0].question

    def test_invalid_pdf_raises(self):
        with pytest.raises(Exception):
            parse_faq_pdf(b"this is not a pdf at all")


class TestConfidence:
    def test_high_medium_low(self):
        assert confidence_for_distance(0.5) == "high"
        assert confidence_for_distance(1.2) == "medium"
        assert confidence_for_distance(1.9) == "low"


class TestHelpdeskService:
    def _make_service(self, tmp_path):
        kb = FAQKnowledgeBase(persist_dir=tmp_path / "vector_store")
        return HelpdeskService(
            history_file=str(tmp_path / "chat_history.json"),
            kb=kb,
        )

    def test_receive_question_auto_answers_faq_match(self, tmp_path):
        svc = self._make_service(tmp_path)
        result = svc.receive_question("creator-1", "How do I apply for a campaign?", "whatsapp")
        assert result["auto_answered"] is True
        assert result["message"].kind == "auto"
        assert result["message"].confidence in ("high", "medium")
        assert result["message"].faq_id
        assert result["message"].role == "agent"

    def test_receive_question_no_auto_for_unrelated(self, tmp_path):
        svc = self._make_service(tmp_path)
        result = svc.receive_question("creator-1", "What is the meaning of life?", "email")
        assert result["auto_answered"] is False

    def test_history_persisted(self, tmp_path):
        svc = self._make_service(tmp_path)
        svc.receive_question("creator-1", "How do I apply for a campaign?", "whatsapp")
        svc2 = HelpdeskService(
            history_file=str(tmp_path / "chat_history.json"),
            kb=FAQKnowledgeBase(persist_dir=tmp_path / "vector_store"),
        )
        assert len(svc2.thread("creator-1")) == 2
        assert svc2.pending_count("creator-1") == 0

    def test_suggest_replies_fallback_to_kb(self, tmp_path):
        svc = self._make_service(tmp_path)
        svc._suggester._run_llm_chain = lambda prompt: None
        suggestions = svc.suggest_replies("How do I apply?", count=3)
        assert 0 < len(suggestions) <= 3
        assert all(isinstance(s, str) and s.strip() for s in suggestions)

    def test_create_mock_creator_dedupe(self, tmp_path, monkeypatch):
        created = []

        class FakeCreatorService:
            def __init__(self):
                self.creators = created

            def add(self, creator):
                created.append(creator)

        monkeypatch.setattr(
            "creo.services.creator_service.CreatorService",
            FakeCreatorService,
        )
        svc = self._make_service(tmp_path)
        c1 = svc.create_mock_creator("Demo Creator", "demo@example.com", "+911", "Gaming", "English")
        c2 = svc.create_mock_creator("Demo Creator", "demo@example.com", "+911", "Gaming", "English")
        assert c1.id == c2.id
        assert len(created) == 1

    def test_stats(self, tmp_path):
        svc = self._make_service(tmp_path)
        svc.receive_question("creator-1", "How do I apply for a campaign?", "whatsapp")
        svc.receive_question("creator-1", "What is the meaning of life?", "email")
        stats = svc.stats()
        assert stats["threads"] == 1
        assert stats["auto"] == 1
        assert stats["pending"] == 1

    def test_multiple_creators_get_independent_threads(self, tmp_path):
        svc = self._make_service(tmp_path)
        svc.receive_question("creator-a", "How do I apply for a campaign?", "whatsapp")
        svc.receive_question("creator-b", "What is the meaning of life?", "email")
        assert svc.creator_ids() == ["creator-a", "creator-b"]
        assert len(svc.thread("creator-a")) == 2
        assert len(svc.thread("creator-b")) == 1
        assert svc.pending_count("creator-a") == 0
        assert svc.pending_count("creator-b") == 1

    def test_reply_only_touches_its_creator_thread(self, tmp_path):
        svc = self._make_service(tmp_path)
        svc.receive_question("creator-a", "What is the meaning of life?", "whatsapp")
        svc.receive_question("creator-b", "When does the new season start?", "whatsapp")
        svc.send_reply("creator-a", "Let me check with the team.")
        assert svc.pending_count("creator-a") == 0
        assert svc.pending_count("creator-b") == 1
        thread_a = svc.thread("creator-a")
        thread_b = svc.thread("creator-b")
        assert thread_a[-1].role == "agent"
        assert all(m.role == "creator" for m in thread_b)

    def test_create_mock_creator_makes_distinct_creators(self, tmp_path, monkeypatch):
        created = []

        class FakeCreatorService:
            def __init__(self):
                self.creators = created

            def add(self, creator):
                created.append(creator)

        monkeypatch.setattr(
            "creo.services.creator_service.CreatorService",
            FakeCreatorService,
        )
        svc = self._make_service(tmp_path)
        c1 = svc.create_mock_creator("Alice", "alice@example.com", "+911", "Gaming", "English")
        c2 = svc.create_mock_creator("Bob", "bob@example.com", "+912", "Fashion", "English")
        assert c1.id != c2.id
        assert len(created) == 2
