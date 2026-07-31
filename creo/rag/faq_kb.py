import io
import logging
import re
import uuid

from langchain_core.documents import Document
from langchain_chroma import Chroma

from creo.config import VECTOR_STORE_DIR
from creo.models import FAQ
from creo.rag.embeddings import get_local_embeddings
from creo.utils.helpers import load_faqs, load_json, save_json

logger = logging.getLogger(__name__)

UPLOADED_FAQS_FILE = "faq_uploaded.json"
COLLECTION_NAME = "faq_helpdesk"

# Chroma returns L2 distance (lower = more similar) with ONNX MiniLM-L6-v2 embeddings.
AUTO_ANSWER_MAX_DIST = 1.30
HIGH_CONFIDENCE_MAX_DIST = 1.15
MEDIUM_CONFIDENCE_MAX_DIST = 1.45


def confidence_for_distance(distance: float) -> str:
    if distance <= HIGH_CONFIDENCE_MAX_DIST:
        return "high"
    if distance <= MEDIUM_CONFIDENCE_MAX_DIST:
        return "medium"
    return "low"


def parse_faq_pdf(file_bytes: bytes) -> list[FAQ]:
    """Extract Q&A entries from an uploaded PDF."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    faqs = _parse_faq_text(text)
    if not faqs:
        raise ValueError(
            "No Q&A entries found in the PDF. Use a format like 'Q1: Question?\\nA1: Answer'."
        )
    return faqs


def _parse_faq_text(text: str) -> list[FAQ]:
    normalized = re.sub(r"\r\n?", "\n", text)
    pattern = re.compile(
        r"(?:^|\n)\s*Q(?:uestion)?\s*\d*\s*[:.)\-]\s*(?P<question>.+?)\s*\n"
        r"\s*A(?:nswer|ns)?\s*\d*\s*[:.)\-]\s*(?P<answer>.+?)"
        r"(?=\n\s*Q(?:uestion)?\s*\d*\s*[:.)\-]|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    faqs = []
    for m in pattern.finditer("\n" + normalized):
        question = " ".join(m.group("question").split())
        answer = " ".join(m.group("answer").split())
        if question and answer:
            faqs.append(_new_faq(question, answer))
    if len(faqs) >= 2:
        return faqs
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n(?=[A-Z0-9])", normalized) if p.strip()]
    pending_question = None
    for para in paragraphs:
        if pending_question is None and para.endswith("?") and len(para) < 300:
            pending_question = para
        elif pending_question is not None:
            faqs.append(_new_faq(pending_question, para))
            pending_question = None
    return faqs


def _new_faq(question: str, answer: str) -> FAQ:
    return FAQ(
        id=f"FAQ-{uuid.uuid4().hex[:8].upper()}",
        question=question,
        answer=answer,
        category="uploaded",
    )


def generate_faq_pdf_bytes(faqs: list[FAQ]) -> bytes:
    """Build a demo FAQ PDF that can be re-ingested (Q1:/A: format)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph("Creator FAQ", styles["Heading1"])]
    for i, faq in enumerate(faqs, 1):
        story.append(Paragraph(f"Q{i}: {faq.question}", styles["Heading2"]))
        story.append(Paragraph(f"A: {faq.answer}", styles["BodyText"]))
        story.append(Spacer(1, 5 * mm))
    doc.build(story)
    return buf.getvalue()


class FAQKnowledgeBase:
    def __init__(self, persist_dir=None):
        self._store = None
        self._persist_dir = persist_dir or VECTOR_STORE_DIR

    def _get_store(self) -> Chroma:
        if self._store is None:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._store = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=get_local_embeddings(),
                persist_directory=str(self._persist_dir),
            )
        return self._store

    def ensure_seeded(self):
        store = self._get_store()
        if store._collection.count() == 0:
            faqs = self._all_faqs()
            if faqs:
                store.add_documents(self._faq_documents(faqs))

    def _all_faqs(self) -> list[FAQ]:
        faqs = list(load_faqs())
        for item in load_json(UPLOADED_FAQS_FILE):
            try:
                faqs.append(FAQ(**item))
            except Exception:
                continue
        return faqs

    def _faq_documents(self, faqs: list[FAQ]) -> list[Document]:
        return [
            Document(
                page_content=f"Q: {f.question}\nA: {f.answer}",
                metadata={"id": f.id, "category": f.category, "question": f.question},
            )
            for f in faqs
        ]

    def add_uploaded_faqs(self, faqs: list[FAQ]):
        existing = load_json(UPLOADED_FAQS_FILE)
        known = {f.get("question", "").lower() for f in existing}
        known |= {f.question.lower() for f in load_faqs()}
        fresh = [f for f in faqs if f.question.strip().lower() not in known]
        if not fresh:
            logger.info("No new FAQ entries to ingest (all already in knowledge base)")
            return 0
        existing.extend(f.model_dump() for f in fresh)
        save_json(UPLOADED_FAQS_FILE, existing)
        self._get_store().add_documents(self._faq_documents(fresh))
        logger.info("Ingested %d FAQ entries from PDF", len(fresh))
        return len(fresh)

    def count(self) -> int:
        self.ensure_seeded()
        return self._get_store()._collection.count()

    def categories(self) -> list[str]:
        self.ensure_seeded()
        metas = self._get_store()._collection.get()["metadatas"]
        return sorted({m.get("category", "") for m in metas if m})

    def search(self, query: str, k: int = 4) -> list[dict]:
        self.ensure_seeded()
        results = self._get_store().similarity_search_with_score(query, k=k)
        return [
            {
                "faq_id": doc.metadata.get("id", ""),
                "question": doc.metadata.get("question", ""),
                "category": doc.metadata.get("category", ""),
                "answer": self._answer_from_doc(doc.page_content),
                "distance": round(score, 3),
            }
            for doc, score in results
        ]

    @staticmethod
    def _answer_from_doc(page_content: str) -> str:
        if "A: " in page_content:
            return page_content.split("A: ", 1)[1]
        return page_content

    def reindex(self):
        store = self._get_store()
        try:
            store.delete_collection()
        except Exception:
            pass
        self._store = None
        faqs = self._all_faqs()
        if faqs:
            self._get_store().add_documents(self._faq_documents(faqs))
