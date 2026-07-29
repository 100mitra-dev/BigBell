from creo.config import AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY

_RUNTIME_CONFIG = {
    "provider": AI_PROVIDER,
    "openai_key": OPENAI_API_KEY,
    "gemini_key": GEMINI_API_KEY,
    "youtube_key": "",
    "instagram_key": "",
    "whatsapp_key": "",
    "data_source": "json",
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


def get_youtube_key() -> str:
    return _RUNTIME_CONFIG.get("youtube_key", "")


def set_youtube_key(key: str):
    _RUNTIME_CONFIG["youtube_key"] = key


def get_instagram_key() -> str:
    return _RUNTIME_CONFIG.get("instagram_key", "")


def set_instagram_key(key: str):
    _RUNTIME_CONFIG["instagram_key"] = key


def get_whatsapp_key() -> str:
    return _RUNTIME_CONFIG.get("whatsapp_key", "")


def set_whatsapp_key(key: str):
    _RUNTIME_CONFIG["whatsapp_key"] = key


def get_data_source() -> str:
    return _RUNTIME_CONFIG.get("data_source", "json")


def set_data_source(source: str):
    _RUNTIME_CONFIG["data_source"] = source


def update_from_env():
    _RUNTIME_CONFIG["provider"] = AI_PROVIDER
    _RUNTIME_CONFIG["openai_key"] = OPENAI_API_KEY
    _RUNTIME_CONFIG["gemini_key"] = GEMINI_API_KEY
