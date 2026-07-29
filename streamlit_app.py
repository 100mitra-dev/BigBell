import streamlit as st

st.set_page_config(
    page_title="Creo — Creator Success Platform",
    page_icon=":material/rocket_launch:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo("app/components/logo.svg", size="medium")

from app.components.layout import init_app_state, sync_config, render_sidebar_stats

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
    "Operations": [
        st.Page("app_pages/applications.py", title="Applications", icon=":material/description:"),
        st.Page("app_pages/verification.py", title="Verification", icon=":material/verified:"),
        st.Page("app_pages/categorization.py", title="Categorization", icon=":material/label:"),
    ],
    "Management": [
        st.Page("app_pages/campaign_matching.py", title="Campaign matching", icon=":material/target:"),
        st.Page("app_pages/follow_ups.py", title="Follow-ups", icon=":material/calendar_clock:"),
        st.Page("app_pages/payments.py", title="Payments", icon=":material/payments:"),
    ],
    "Insights": [
        st.Page("app_pages/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
        st.Page("app_pages/creator_crm.py", title="Creator CRM", icon=":material/group:"),
        st.Page("app_pages/creator_queries.py", title="Creator queries", icon=":material/chat:"),
    ],
    "Configuration": [
        st.Page("app_pages/settings.py", title="Settings", icon=":material/settings:"),
    ],
}, position="sidebar")

page.run()
