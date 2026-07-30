from typing import Optional

from creo.runtime_config import get_provider, get_openai_key, get_gemini_key


class ONNXEmbeddings:
    def __init__(self):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        self._model = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._model([text])[0]


_default_embeddings: Optional[ONNXEmbeddings] = None


def _get_onnx():
    global _default_embeddings
    if _default_embeddings is None:
        _default_embeddings = ONNXEmbeddings()
    return _default_embeddings


def get_embeddings():
    provider = get_provider()
    if provider == "openai":
        key = get_openai_key()
        if key:
            from langchain_openai import OpenAIEmbeddings
            from creo.config import EMBEDDING_MODEL
            return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=key)

    if provider == "gemini":
        key = get_gemini_key()
        if key:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                return GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=key,
                )
            except ImportError:
                pass

    return _get_onnx()
