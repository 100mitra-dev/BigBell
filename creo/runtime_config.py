import os
from pathlib import Path

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

SECRETS_PATH = Path(__file__).resolve().parent.parent.parent / ".streamlit" / "secrets.toml"


def _load_config_from_file() -> dict:
    config = {}
    if not SECRETS_PATH.exists():
        return config
    with open(SECRETS_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                config[key] = val
    return config


def _write_config_file(config: dict):
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Creo AI configuration",
        "# AI_PROVIDER options: mock, openai, gemini",
    ]
    for key in ("AI_PROVIDER", "OPENAI_API_KEY", "GEMINI_API_KEY", "YOUTUBE_API_KEY", "INSTAGRAM_API_KEY", "WHATSAPP_API_KEY"):
        val = config.get(key, "")
        lines.append(f'{key} = "{val}"')
    with open(SECRETS_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


def load_persisted_config():
    cfg = _load_config_from_file()
    if cfg.get("AI_PROVIDER"):
        _RUNTIME_CONFIG["provider"] = cfg["AI_PROVIDER"]
    if cfg.get("OPENAI_API_KEY"):
        _RUNTIME_CONFIG["openai_key"] = cfg["OPENAI_API_KEY"]
    if cfg.get("GEMINI_API_KEY"):
        _RUNTIME_CONFIG["gemini_key"] = cfg["GEMINI_API_KEY"]
    if cfg.get("YOUTUBE_API_KEY"):
        _RUNTIME_CONFIG["youtube_key"] = cfg["YOUTUBE_API_KEY"]
    if cfg.get("INSTAGRAM_API_KEY"):
        _RUNTIME_CONFIG["instagram_key"] = cfg["INSTAGRAM_API_KEY"]
    if cfg.get("WHATSAPP_API_KEY"):
        _RUNTIME_CONFIG["whatsapp_key"] = cfg["WHATSAPP_API_KEY"]


def persist_config():
    cfg = _load_config_from_file()
    cfg["AI_PROVIDER"] = _RUNTIME_CONFIG.get("provider", "mock")
    cfg["OPENAI_API_KEY"] = _RUNTIME_CONFIG.get("openai_key", "")
    cfg["GEMINI_API_KEY"] = _RUNTIME_CONFIG.get("gemini_key", "")
    cfg["YOUTUBE_API_KEY"] = _RUNTIME_CONFIG.get("youtube_key", "")
    cfg["INSTAGRAM_API_KEY"] = _RUNTIME_CONFIG.get("instagram_key", "")
    cfg["WHATSAPP_API_KEY"] = _RUNTIME_CONFIG.get("whatsapp_key", "")
    _write_config_file(cfg)


def get_provider() -> str:
    return _RUNTIME_CONFIG.get("provider", "mock")


def set_provider(provider: str):
    _RUNTIME_CONFIG["provider"] = provider
    persist_config()


def get_openai_key() -> str:
    return _RUNTIME_CONFIG.get("openai_key", "")


def set_openai_key(key: str):
    _RUNTIME_CONFIG["openai_key"] = key
    persist_config()


def get_gemini_key() -> str:
    return _RUNTIME_CONFIG.get("gemini_key", "")


def set_gemini_key(key: str):
    _RUNTIME_CONFIG["gemini_key"] = key
    persist_config()


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
