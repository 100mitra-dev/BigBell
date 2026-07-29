from src.core.config import AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY


class BaseAgent:
    def __init__(self):
        self.provider = AI_PROVIDER

    @property
    def use_openai(self) -> bool:
        return self.provider == "openai" and bool(OPENAI_API_KEY)

    @property
    def use_gemini(self) -> bool:
        return self.provider == "gemini" and bool(GEMINI_API_KEY)

    @property
    def use_mock(self) -> bool:
        return not (self.use_openai or self.use_gemini)

    def _get_llm(self):
        if self.use_openai:
            from langchain_openai import ChatOpenAI
            from src.core.config import OPENAI_MODEL
            return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.3)
        elif self.use_gemini:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from src.core.config import GEMINI_MODEL
            return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY, temperature=0.3)
        return None

    def _run_llm_chain(self, prompt: str) -> str:
        llm = self._get_llm()
        if llm is None:
            return ""
        try:
            response = llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return f"Error: {e}"
