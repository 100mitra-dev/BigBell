import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

import streamlit as st


@dataclass
class APILogEntry:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds"))
    provider: str = ""
    model: str = ""
    endpoint: str = ""
    request_preview: str = ""
    response_preview: str = ""
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


MAX_LOGS = 500


def is_enabled() -> bool:
    return st.session_state.get("debug_logging", False)


def add_log(entry: APILogEntry):
    if not is_enabled():
        return
    if "api_logs" not in st.session_state:
        st.session_state.api_logs = []
    st.session_state.api_logs.append(asdict(entry))
    if len(st.session_state.api_logs) > MAX_LOGS:
        st.session_state.api_logs = st.session_state.api_logs[-MAX_LOGS:]


def clear_logs():
    st.session_state.api_logs = []


def get_logs() -> list[dict]:
    return st.session_state.get("api_logs", [])
