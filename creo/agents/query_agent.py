import logging

from creo.agents.base import BaseAgent
from creo.rag.retrieval import FAQRetriever

logger = logging.getLogger(__name__)


class QueryAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.retriever = FAQRetriever()
        logger.debug("QueryAgent initialized with FAQRetriever")

    def answer(self, question: str, category: str = None) -> dict:
        if self.use_mock:
            return self._mock_answer(question, category)
        logger.debug("AI answering question (category=%s)", category)
        return self._ai_answer(question, category)

    def stream_answer(self, question: str, category: str = None):
        if self.use_mock:
            result = self._mock_answer(question, category)
            for char in result["answer"]:
                yield char
            return
        if category:
            results = self.retriever.search_by_category(question, category, k=5)
        else:
            results = self.retriever.search(question, k=5)
        context = "\n\n".join(doc.page_content for doc in results) if results else "No relevant documents found."
        prompt = f"""You are a helpful support assistant for a creator management platform. Answer the creator's question based on the provided FAQ context.

Context:
{context}

Question: {question}

Provide a helpful, accurate answer. If the context doesn't contain relevant information, say so and suggest contacting the Creator Success team."""
        yield from self._stream_llm(prompt)

    def _mock_answer(self, question: str, category: str = None) -> dict:
        if category:
            results = self.retriever.search_by_category(question, category, k=3)
        else:
            results = self.retriever.search(question, k=3)

        if not results:
            return {
                "answer": "I don't have enough information to answer this question. Please contact your Creator Success manager for assistance.",
                "sources": [],
                "confidence": "low",
            }

        best = results[0]
        source_text = best.page_content
        answer = source_text.split("A: ", 1)[1] if "A: " in source_text else source_text

        sources = []
        for doc in results[:2]:
            sources.append({
                "question": doc.metadata.get("question", ""),
                "category": doc.metadata.get("category", ""),
            })

        return {
            "answer": answer,
            "sources": sources,
            "confidence": "high" if len(results) >= 2 else "medium",
        }

    def _ai_answer(self, question: str, category: str = None) -> dict:
        if category:
            results = self.retriever.search_by_category(question, category, k=5)
        else:
            results = self.retriever.search(question, k=5)

        context = "\n\n".join(doc.page_content for doc in results) if results else "No relevant documents found."

        prompt = f"""You are a helpful support assistant for a creator management platform. Answer the creator's question based on the provided FAQ context.

Context:
{context}

Question: {question}

Provide a helpful, accurate answer. If the context doesn't contain relevant information, say so and suggest contacting the Creator Success team.

Return a JSON with:
1. answer (string - the response)
2. confidence ("high"/"medium"/"low")

Return ONLY valid JSON, no markdown formatting."""
        result = self._run_llm_chain(prompt)
        try:
            import json
            parsed = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
            sources = []
            for doc in results[:2]:
                sources.append({
                    "question": doc.metadata.get("question", ""),
                    "category": doc.metadata.get("category", ""),
                })
            return {
                "answer": parsed.get("answer", ""),
                "sources": sources,
                "confidence": parsed.get("confidence", "medium"),
            }
        except Exception as e:
            logger.error("AI answer failed, falling back to mock: %s", e)
            return self._mock_answer(question, category)
