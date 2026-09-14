import os
from pathlib import Path
from dotenv import load_dotenv, set_key

from creo.config import AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY, META_API_KEY, META_API_TOKEN, ENV_PATH

_RUNTIME_CONFIG = {
    "provider": AI_PROVIDER,
    "openai_key": OPENAI_API_KEY,
    "gemini_key": GEMINI_API_KEY,
    "meta_api_key": META_API_KEY,
    "meta_api_token": META_API_TOKEN,
    "openai_model": "gpt-4o",
    "gemini_model": "gemini-3.5-flash-lite",
    "youtube_key": "",
    "instagram_key": "",
    "whatsapp_key": "",
    "data_source": "json",
    "debug_logging": False,
}

_ENV_MAP = {
    "provider": "AI_PROVIDER",
    "openai_key": "OPENAI_API_KEY",
    "gemini_key": "GEMINI_API_KEY",
    "meta_api_key": "META_API_KEY",
    "meta_api_token": "META_API_TOKEN",
    "openai_model": "OPENAI_MODEL",
    "gemini_model": "GEMINI_MODEL",
    "youtube_key": "YOUTUBE_API_KEY",
    "instagram_key": "INSTAGRAM_API_KEY",
    "whatsapp_key": "WHATSAPP_API_KEY",
    "debug_logging": "DEBUG_LOGGING",
}


def load_persisted_config():
    load_dotenv(str(ENV_PATH), override=True)
    for key, env_key in _ENV_MAP.items():
        val = os.getenv(env_key)
        if val is not None and val != "":
            if key == "debug_logging":
                _RUNTIME_CONFIG[key] = val.lower() == "true"
            else:
                _RUNTIME_CONFIG[key] = val


def persist_config():
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    for key, env_key in _ENV_MAP.items():
        val = _RUNTIME_CONFIG.get(key, "")
        if isinstance(val, bool):
            val = "true" if val else "false"
        set_key(str(ENV_PATH), env_key, val)
        os.environ[env_key] = str(val) if not isinstance(val, str) else val


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


def get_meta_api_key() -> str:
    key = _RUNTIME_CONFIG.get("meta_api_key", "")
    if not key:
        import os as _os
        key = _os.getenv("META_MARKETPLACE_API_KEY", "") or _os.getenv("MODASH_API_KEY", "")
    return key


def set_meta_api_key(key: str):
    _RUNTIME_CONFIG["meta_api_key"] = key
    key = _RUNTIME_CONFIG.get("meta_api_key", "")
    if not key:
        import os as _os
        key = _os.getenv("META_MARKETPLACE_API_KEY", "") or _os.getenv("MODASH_API_KEY", "")
    return key


def get_meta_api_token() -> str:
    return _RUNTIME_CONFIG.get("meta_api_token", "")


def set_meta_api_token(token: str):
    _RUNTIME_CONFIG["meta_api_token"] = token


def get_openai_model() -> str:
    return _RUNTIME_CONFIG.get("openai_model", "gpt-4o")


def set_openai_model(model: str):
    _RUNTIME_CONFIG["openai_model"] = model


def get_gemini_model() -> str:
    return _RUNTIME_CONFIG.get("gemini_model", "gemini-3.5-flash-lite")


def set_gemini_model(model: str):
    _RUNTIME_CONFIG["gemini_model"] = model


def get_debug_logging() -> bool:
    return _RUNTIME_CONFIG.get("debug_logging", False)


def set_debug_logging(enabled: bool):
    _RUNTIME_CONFIG["debug_logging"] = enabled


def get_data_source() -> str:
    return _RUNTIME_CONFIG.get("data_source", "json")


def set_data_source(source: str):
    _RUNTIME_CONFIG["data_source"] = source


def update_from_env():
    _RUNTIME_CONFIG["provider"] = AI_PROVIDER
    _RUNTIME_CONFIG["openai_key"] = OPENAI_API_KEY
    _RUNTIME_CONFIG["gemini_key"] = GEMINI_API_KEY
    _RUNTIME_CONFIG["meta_api_key"] = META_API_KEY
    _RUNTIME_CONFIG["meta_api_token"] = META_API_TOKEN
