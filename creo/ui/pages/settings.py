import streamlit as st

from creo.ui.components.layout import sync_config
from creo.runtime_config import set_youtube_key, set_instagram_key, set_whatsapp_key, set_data_source, get_data_source

st.title("Settings")
st.caption("Configure AI providers, API keys, and data sources")

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
    st.subheader("API integrations")
    st.caption("Configure external API keys for data sources")

    yt_key = st.text_input("YouTube API key", type="password", placeholder="AIza...", value=st.session_state.get("youtube_key", ""))
    ig_key = st.text_input("Instagram API key", type="password", placeholder="IG access token...", value=st.session_state.get("instagram_key", ""))
    wa_key = st.text_input("WhatsApp API key", type="password", placeholder="Twilio/WhatsApp token...", value=st.session_state.get("whatsapp_key", ""))

    if st.button("Save API keys", icon=":material/save:"):
        st.session_state.youtube_key = yt_key
        st.session_state.instagram_key = ig_key
        st.session_state.whatsapp_key = wa_key
        set_youtube_key(yt_key)
        set_instagram_key(ig_key)
        set_whatsapp_key(wa_key)
        st.success("API keys saved for this session")

with st.container(border=True):
    st.subheader("Data source")
    st.caption("Choose where to pull data from")

    current = get_data_source()
    source = st.radio("Data source", options=["json", "api"], index=0 if current == "json" else 1, horizontal=True, format_func=lambda x: "JSON files (local)" if x == "json" else "External APIs (YouTube/Instagram)")
    if source != current:
        set_data_source(source)
        st.session_state.data_source = source
        st.info("Data source changed. Refresh pages to see changes.")
        st.rerun()

    if source == "api":
        st.warning("API mode requires valid API keys configured above. Falls back to mock data if keys are missing or invalid.")

with st.container(border=True):
    st.subheader("Custom niches")
    st.caption("Add or remove custom niches beyond the default list")

    from creo.config import load_custom_niches, add_custom_niche, remove_custom_niche, NICHES

    custom = load_custom_niches()
    if custom:
        for n in custom:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"- {n}")
            with c2:
                if st.button("Remove", key=f"rm_n_{n}", icon=":material/delete:", use_container_width=True):
                    remove_custom_niche(n)
                    st.rerun()
    else:
        st.caption("No custom niches yet")

    new_niche = st.text_input("New niche name", placeholder="e.g. Crypto & Web3", key="new_niche_input")
    if st.button("Add custom niche", icon=":material/add:", use_container_width=True) and new_niche:
        if new_niche not in NICHES and new_niche not in custom:
            add_custom_niche(new_niche)
            st.success(f"Added: {new_niche}")
            st.rerun()
        else:
            st.warning("Niche already exists")

with st.container(border=True):
    st.subheader("About Creo")
    st.markdown("""
    **Creo** is an AI-powered platform for creator onboarding, management, and campaign operations.

    - **Mock mode** — fully functional with simulated AI responses
    - **OpenAI** — uses GPT-4o for review, matching, and query answering
    - **Gemini** — uses Google Gemini 1.5 Pro for AI features

    Configuration is stored in your browser session. API keys are never saved to disk.
    """)
