import json
import logging
import uuid
from datetime import datetime

from creo.agents.base import BaseAgent
from creo.models import ChatMessage, Creator
from creo.rag.faq_kb import FAQKnowledgeBase, AUTO_ANSWER_MAX_DIST, confidence_for_distance
from creo.utils.json_io import load_json, save_json

logger = logging.getLogger(__name__)

CHAT_HISTORY_FILE = "chat_history.json"
CHANNELS = ["whatsapp", "email", "in_app"]

DEMO_QUESTIONS = [
    "How do I apply for a campaign?",
    "When will I receive my payment?",
    "What documents do I need for onboarding?",
    "How many followers do I need to join?",
    "What happens if I miss a deadline?",
]


class HelpdeskService:
    def __init__(self, history_file: str = CHAT_HISTORY_FILE, kb: FAQKnowledgeBase | None = None):
        self.kb = kb or FAQKnowledgeBase()
        self._history_file = history_file
        self._messages: dict[str, list[ChatMessage]] = {}
        self._suggester = BaseAgent()
        self._load_history()

    def _load_history(self):
        for item in load_json(self._history_file):
            try:
                msg = ChatMessage(**item)
            except Exception:
                continue
            self._messages.setdefault(msg.creator_id, []).append(msg)

    def _save_history(self):
        all_msgs = [m for msgs in self._messages.values() for m in msgs]
        save_json(self._history_file, [m.model_dump() for m in all_msgs])

    def _append(self, msg: ChatMessage):
        self._messages.setdefault(msg.creator_id, []).append(msg)
        self._save_history()

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def creator_ids(self) -> list[str]:
        return sorted(self._messages.keys())

    def thread(self, creator_id: str) -> list[ChatMessage]:
        return list(self._messages.get(creator_id, []))

    def pending_count(self, creator_id: str) -> int:
        msgs = self._messages.get(creator_id, [])
        pending = 0
        for i, m in enumerate(msgs):
            if m.role == "creator" and not any(x.role == "agent" for x in msgs[i + 1:]):
                pending += 1
        return pending

    def unanswered_question(self, creator_id: str) -> ChatMessage | None:
        msgs = self._messages.get(creator_id, [])
        for i, m in enumerate(msgs):
            if m.role == "creator" and not any(x.role == "agent" for x in msgs[i + 1:]):
                return m
        return None

    def receive_question(self, creator_id: str, content: str, channel: str = "whatsapp") -> dict:
        incoming = ChatMessage(
            id=str(uuid.uuid4()),
            creator_id=creator_id,
            role="creator",
            content=content,
            channel=channel,
            kind="incoming",
            created_at=self._now(),
        )
        self._append(incoming)
        results = self.kb.search(content, k=3)
        best = results[0] if results else None
        if best and best["distance"] <= AUTO_ANSWER_MAX_DIST:
            confidence = confidence_for_distance(best["distance"])
            auto = ChatMessage(
                id=str(uuid.uuid4()),
                creator_id=creator_id,
                role="agent",
                content=best["answer"],
                channel=channel,
                kind="auto",
                faq_id=best["faq_id"],
                confidence=confidence,
                created_at=self._now(),
            )
            self._append(auto)
            return {
                "auto_answered": True,
                "message": auto,
                "match": best,
                "distance": best["distance"],
            }
        return {
            "auto_answered": False,
            "match": best,
            "distance": best["distance"] if best else None,
        }

    def suggest_replies(self, question: str, count: int = 3) -> list[str]:
        suggestions = []
        for hit in self.kb.search(question, k=count):
            text = hit["answer"].strip()
            if text and text not in suggestions:
                suggestions.append(text)
        if not self._suggester.use_mock:
            prompt = (
                "You are writing replies on behalf of a creator support agent at a creator "
                f"management platform. The creator asked: \"{question}\"\n\n"
                "Write 2-3 concise, friendly, accurate reply options. "
                "Return ONLY a JSON list of strings, no markdown."
            )
            result = self._suggester._run_llm_chain(prompt)
            if result:
                try:
                    cleaned = result.strip().removeprefix("```json").removesuffix("```").strip()
                    candidates = json.loads(cleaned)
                    if isinstance(candidates, list):
                        suggestions = [str(c).strip() for c in candidates if str(c).strip()] + suggestions
                except Exception:
                    logger.debug("Could not parse LLM suggestions, using knowledge-base replies")
        return suggestions[:count]

    def send_reply(self, creator_id: str, content: str, channel: str = "whatsapp",
                   kind: str = "manual", faq_id: str | None = None,
                   confidence: str | None = None) -> ChatMessage:
        msg = ChatMessage(
            id=str(uuid.uuid4()),
            creator_id=creator_id,
            role="agent",
            content=content,
            channel=channel,
            kind=kind,
            faq_id=faq_id,
            confidence=confidence,
            created_at=self._now(),
        )
        self._append(msg)
        return msg

    def create_mock_creator(self, name: str, email: str, phone: str, niche: str,
                            language: str = "English") -> Creator:
        from creo.models import CreatorStatus
        from creo.services.creator_service import CreatorService

        cs = CreatorService()
        for c in cs.creators:
            if c.name.lower() == name.lower():
                return c
        creator = Creator(
            id=f"creator-{uuid.uuid4().hex[:8]}",
            name=name,
            email=email,
            phone=phone,
            primary_niche=niche,
            secondary_niches=[],
            primary_language=language,
            secondary_languages=[],
            platforms={},
            content_quality_score=7.0,
            profile_completeness=80.0,
            avg_engagement_rate=3.5,
            status=CreatorStatus.ACTIVE,
        )
        cs.add(creator)
        return creator

    def stats(self) -> dict:
        all_msgs = [m for msgs in self._messages.values() for m in msgs]
        auto = sum(1 for m in all_msgs if m.kind == "auto")
        incoming = sum(1 for m in all_msgs if m.role == "creator")
        pending = sum(self.pending_count(cid) for cid in self._messages)
        try:
            faq_count = self.kb.count()
        except Exception:
            faq_count = 0
        return {
            "threads": len(self._messages),
            "messages": len(all_msgs),
            "auto": auto,
            "incoming": incoming,
            "pending": pending,
            "faqs": faq_count,
        }
