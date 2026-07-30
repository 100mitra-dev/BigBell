import logging

from creo.runtime_config import get_provider, get_openai_key, get_gemini_key

logger = logging.getLogger(__name__)


class BaseAgent:
    @property
    def use_openai(self) -> bool:
        return get_provider() == "openai" and bool(get_openai_key())

    @property
    def use_gemini(self) -> bool:
        return get_provider() == "gemini" and bool(get_gemini_key())

    @property
    def use_mock(self) -> bool:
        return not (self.use_openai or self.use_gemini)

    def _get_llm(self):
        if self.use_openai:
            from langchain_openai import ChatOpenAI
            from creo.config import OPENAI_MODEL
            logger.debug("Using OpenAI LLM (%s)", OPENAI_MODEL)
            return ChatOpenAI(model=OPENAI_MODEL, api_key=get_openai_key(), temperature=0.3)
        elif self.use_gemini:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from creo.config import GEMINI_MODEL
            logger.debug("Using Gemini LLM (%s)", GEMINI_MODEL)
            return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=get_gemini_key(), temperature=0.3)
        return None

    def _run_llm_chain(self, prompt: str) -> str | None:
        llm = self._get_llm()
        if llm is None:
            logger.warning("No LLM available (provider=mock or missing API key)")
            return None
        try:
            response = llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error("LLM invocation failed: %s", e)
            return None

    def _stream_llm(self, prompt: str):
        llm = self._get_llm()
        if llm is None:
            yield "AI mode requires an API key. Set it in Settings."
            return
        try:
            for chunk in llm.stream(prompt):
                yield chunk.content if hasattr(chunk, "content") else str(chunk)
        except Exception as e:
            logger.error("LLM streaming failed: %s", e)
            yield f"Error: {e}"
