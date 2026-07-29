from src.core.config import AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY

_RUNTIME_CONFIG = {
    "provider": AI_PROVIDER,
    "openai_key": OPENAI_API_KEY,
    "gemini_key": GEMINI_API_KEY,
}


def get_provider() -> str:
    return _RUNTIME_CONFIG.get("provider", "mock")


def set_provider(provider: str):
    _RUNTIME_CONFIG["provider"] = provider


def get_openai_key() -> str:
    return _RUNTIME_CONFIG.get("openai_key", "")


def set_openai_key(key: str):
    _RUNTIME_CONFIG["openai_key"] = key


def get_gemini_key() -> str:
    return _RUNTIME_CONFIG.get("gemini_key", "")


def set_gemini_key(key: str):
    _RUNTIME_CONFIG["gemini_key"] = key


def update_from_env():
    _RUNTIME_CONFIG["provider"] = AI_PROVIDER
    _RUNTIME_CONFIG["openai_key"] = OPENAI_API_KEY
    _RUNTIME_CONFIG["gemini_key"] = GEMINI_API_KEY
