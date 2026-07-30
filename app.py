import streamlit as st

st.set_page_config(
    page_title="Creo — Creator Success Platform",
    page_icon=":material/rocket_launch:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo("creo/ui/components/logo.svg", size="large")

from creo.ui.components.layout import init_app_state, sync_config, render_sidebar_stats

init_app_state()
sync_config()

with st.sidebar:
    st.segmented_control(
        "AI provider",
        options=["mock", "openai", "gemini"],
        key="provider",
        on_change=sync_config,
        label_visibility="collapsed",
    )

    p = st.session_state.provider
    if p == "mock":
        st.badge("Mock mode", icon=":material/build:", color="blue")
        st.caption("Rule-based AI responses")
    elif p == "openai":
        if st.session_state.openai_key:
            st.badge("OpenAI ready", icon=":material/check_circle:", color="green")
        else:
            st.badge("Key missing", icon=":material/warning:", color="orange")
            st.caption("Add your OpenAI key in Settings")
    elif p == "gemini":
        if st.session_state.gemini_key:
            st.badge("Gemini ready", icon=":material/check_circle:", color="green")
        else:
            st.badge("Key missing", icon=":material/warning:", color="orange")
            st.caption("Add your Gemini key in Settings")

    with st.expander("Quick stats", icon=":material/analytics:"):
        render_sidebar_stats()

page = st.navigation({
    "Overview": [
        st.Page("creo/ui/pages/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
    ],
    "Creators": [
        st.Page("creo/ui/pages/creator_crm.py", title="All Creators", icon=":material/group:"),
        st.Page("creo/ui/pages/creator_validation.py", title="Review & Classify", icon=":material/verified:"),
    ],
    "Campaigns": [
        st.Page("creo/ui/pages/campaign_matching.py", title="Match Creators", icon=":material/target:"),
        st.Page("creo/ui/pages/follow_ups.py", title="Deadlines & Notes", icon=":material/calendar_clock:"),
    ],
    "Finance": [
        st.Page("creo/ui/pages/payments.py", title="Payments", icon=":material/payments:"),
    ],
    "AI Tools": [
        st.Page("creo/ui/pages/creator_queries.py", title="AI Helpdesk", icon=":material/chat:"),
    ],
    "Settings": [
        st.Page("creo/ui/pages/settings.py", title="Configure", icon=":material/settings:"),
        st.Page("creo/ui/pages/api_logs.py", title="API Logs", icon=":material/list_alt:"),
    ],
}, position="sidebar")

page.run()
