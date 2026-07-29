import streamlit as st

CONFIG_DEFAULTS = {
    "provider": "mock",
    "openai_key": "",
    "gemini_key": "",
}


def init_app_state():
    from src.core.runtime_config import _RUNTIME_CONFIG
    for key, default in CONFIG_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = _RUNTIME_CONFIG.get(key, default)


def sync_config():
    from src.core.runtime_config import (
        set_provider, set_openai_key, set_gemini_key,
    )
    set_provider(st.session_state.provider)
    set_openai_key(st.session_state.openai_key)
    set_gemini_key(st.session_state.gemini_key)


def render_sidebar_stats():
    try:
        from src.core.services.creator_service import CreatorService
        from src.core.services.campaign_service import CampaignService
        from src.core.services.payment_service import PaymentService

        cs = CreatorService()
        cams = CampaignService()
        ps = PaymentService()

        st.metric("Total creators", len(cs.creators))
        st.metric("Active campaigns", cams.get_active_count())
        st.metric("Pending payments", ps.get_pending_count())
    except Exception:
        pass
