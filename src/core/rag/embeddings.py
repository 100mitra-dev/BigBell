from src.core.runtime_config import get_provider, get_openai_key, get_gemini_key


def get_embeddings():
    provider = get_provider()
    if provider == "openai":
        key = get_openai_key()
        if key:
            from langchain_openai import OpenAIEmbeddings
            from src.core.config import EMBEDDING_MODEL
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

    from langchain_community.embeddings import FakeEmbeddings
    return FakeEmbeddings(size=384)
