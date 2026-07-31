import streamlit as st

CONFIG_DEFAULTS = {
    "provider": "mock",
    "openai_key": "",
    "gemini_key": "",
    "openai_model": "gpt-4o",
    "gemini_model": "gemini-3.5-flash-lite",
    "debug_logging": False,
}


def init_app_state():
    from creo.runtime_config import _RUNTIME_CONFIG, load_persisted_config
    load_persisted_config()
    for key, default in CONFIG_DEFAULTS.items():
        st.session_state[key] = _RUNTIME_CONFIG.get(key, default)


def sync_config():
    from creo.runtime_config import (
        set_provider, set_openai_key, set_gemini_key, persist_config,
    )
    set_provider(st.session_state.provider)
    set_openai_key(st.session_state.openai_key)
    set_gemini_key(st.session_state.gemini_key)
    persist_config()


def render_sidebar_stats():
    try:
        from creo.services.creator_service import CreatorService
        from creo.services.campaign_service import CampaignService
        from creo.services.payment_service import PaymentService

        cs = CreatorService()
        cams = CampaignService()
        ps = PaymentService()

        st.metric("Total creators", len(cs.creators))
        st.metric("Active campaigns", cams.get_active_count())
        st.metric("Pending payments", ps.get_pending_count())
    except Exception:
        pass
