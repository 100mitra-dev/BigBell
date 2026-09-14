import logging

from creo.rag.faq_kb import FAQKnowledgeBase

logger = logging.getLogger(__name__)


class FAQRetriever(FAQKnowledgeBase):
    """Back-compat alias: the FAQ knowledge base is the sole retrieval facade."""

    def search_by_category(self, query: str, category: str, k: int = 5) -> list:
        try:
            return [h for h in self.search(query, k=max(k * 3, k)) if h.get("category") == category][:k]
        except (ValueError, RuntimeError, OSError) as exc:
            logger.warning("FAQRetriever.search_by_category failed: %s", exc)
            return []
