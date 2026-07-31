import logging
import time

from creo.utils.runtime_settings import get_provider, get_openai_key, get_gemini_key, get_openai_model, get_gemini_model
from creo.utils.debug_logging import APILogEntry, add_log

logger = logging.getLogger(__name__)


def _classify_llm_error(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()
    if "timeout" in lowered or "timed out" in lowered or "deadline" in lowered or "504" in message:
        return f"TIMEOUT (>{BaseAgent.LLM_TIMEOUT_SECONDS}s): {message}"
    return message


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

    LLM_TIMEOUT_SECONDS = 10

    def _get_llm(self):
        if self.use_openai:
            from langchain_openai import ChatOpenAI
            model = get_openai_model()
            logger.debug("Using OpenAI LLM (%s)", model)
            return ChatOpenAI(
                model=model,
                api_key=get_openai_key(),
                temperature=0.3,
                request_timeout=self.LLM_TIMEOUT_SECONDS,
                max_retries=1,
            )
        elif self.use_gemini:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model = get_gemini_model()
            logger.debug("Using Gemini LLM (%s)", model)
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=get_gemini_key(),
                temperature=0.3,
                request_timeout=self.LLM_TIMEOUT_SECONDS,
            )
        return None

    def _run_llm_chain(self, prompt: str) -> str | None:
        llm = self._get_llm()
        if llm is None:
            logger.warning("No LLM available (provider=mock or missing API key)")
            return None
        entry = APILogEntry(
            provider=get_provider(),
            model=getattr(llm, "model", ""),
            endpoint="chat",
            request_preview=prompt[:500],
        )
        start = time.perf_counter()
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else response
            result = content if isinstance(content, str) else str(content)
            entry.response_preview = result[:2000]
            entry.success = True
            return result
        except Exception as e:
            logger.error("LLM invocation failed: %s", e)
            entry.success = False
            entry.error = _classify_llm_error(e)
            return None
        finally:
            entry.duration_ms = round((time.perf_counter() - start) * 1000, 1)
            add_log(entry)

    def _stream_llm(self, prompt: str):
        llm = self._get_llm()
        if llm is None:
            yield "AI mode requires an API key. Set it in Settings."
            return
        entry = APILogEntry(
            provider=get_provider(),
            model=getattr(llm, "model", ""),
            endpoint="stream",
            request_preview=prompt[:500],
        )
        start = time.perf_counter()
        chunks = []
        try:
            for chunk in llm.stream(prompt):
                content = chunk.content if hasattr(chunk, "content") else chunk
                content = content if isinstance(content, str) else str(content)
                chunks.append(content)
                yield content
            entry.response_preview = "".join(chunks)[:2000]
            entry.success = True
        except Exception as e:
            logger.error("LLM streaming failed: %s", e)
            entry.success = False
            entry.error = _classify_llm_error(e)
            yield f"Error: {e}"
        finally:
            entry.duration_ms = round((time.perf_counter() - start) * 1000, 1)
            add_log(entry)
