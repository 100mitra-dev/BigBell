import streamlit as st

from app.components.layout import sync_config

st.title("Settings")
st.caption("Configure AI providers and app preferences")

with st.container(border=True):
    st.subheader("AI provider configuration")

    p = st.session_state.provider
    icons = {"mock": ":material/build:", "openai": ":material/psychology:", "gemini": ":material/google:"}
    st.markdown(f"**Current provider:** {icons.get(p, '')} {p.title()}")
    st.caption("Change the provider in the sidebar")

    st.text_input(
        "OpenAI API key",
        key="openai_key",
        type="password",
        placeholder="sk-...",
        on_change=sync_config,
        label_visibility="collapsed" if p != "openai" else "visible",
        disabled=p != "openai",
    )

    st.text_input(
        "Gemini API key",
        key="gemini_key",
        type="password",
        placeholder="Your Gemini key",
        on_change=sync_config,
        label_visibility="collapsed" if p != "gemini" else "visible",
        disabled=p != "gemini",
    )

    if p == "openai" and st.session_state.openai_key:
        st.success(":material/check_circle: OpenAI configured and ready")
    elif p == "gemini" and st.session_state.gemini_key:
        st.success(":material/check_circle: Gemini configured and ready")
    elif p != "mock":
        st.warning(":material/warning: Enter an API key to enable AI features")

with st.container(border=True):
    st.subheader("About Creo")
    st.markdown("""
    **Creo** is an AI-powered platform for creator onboarding, management, and campaign operations.

    - **Mock mode** — fully functional with simulated AI responses
    - **OpenAI** — uses GPT-4o for review, matching, and query answering
    - **Gemini** — uses Google Gemini 1.5 Pro for AI features

    Configuration is stored in your browser session. API keys are never saved to disk.
    """)
