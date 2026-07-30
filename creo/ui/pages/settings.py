import streamlit as st

from creo.ui.components.layout import sync_config
from creo.runtime_config import set_youtube_key, set_instagram_key, set_whatsapp_key, set_data_source, get_data_source, persist_config
import logging

logger = logging.getLogger(__name__)

DEFAULT_OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
DEFAULT_GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]


@st.cache_data(ttl=300)
def _fetch_openai_models(api_key: str) -> list[str]:
    if not api_key:
        return DEFAULT_OPENAI_MODELS
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        models = [m.id for m in client.models.list() if m.id.startswith("gpt-")]
        return sorted(models, reverse=True) if models else DEFAULT_OPENAI_MODELS
    except Exception as e:
        logger.warning("Failed to fetch OpenAI models: %s", e)
        return DEFAULT_OPENAI_MODELS


@st.cache_data(ttl=300)
def _fetch_gemini_models(api_key: str) -> list[str]:
    if not api_key:
        return DEFAULT_GEMINI_MODELS
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        models = [
            m.name.removeprefix("models/")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        return sorted(models, reverse=True) if models else DEFAULT_GEMINI_MODELS
    except Exception as e:
        logger.warning("Failed to fetch Gemini models: %s", e)
        return DEFAULT_GEMINI_MODELS


st.title("Settings")
st.caption("Configure AI providers, API keys, and data sources")
try:

    with st.container(border=True):
        st.subheader("AI provider configuration")

        p = st.session_state.provider
        icons = {"mock": ":material/build:", "openai": ":material/psychology:", "gemini": ":material/google:"}
        st.markdown(f"**Current provider:** {icons.get(p, '')} {p.title()}")
        st.caption("Change the provider in the sidebar")

        if p == "openai":
            st.text_input(
                "OpenAI API key",
                key="openai_key",
                type="password",
                placeholder="sk-...",
                on_change=sync_config,
            )

            def _on_openai_model():
                from creo.runtime_config import set_openai_model, persist_config
                set_openai_model(st.session_state.openai_model)
                persist_config()

            openai_models = _fetch_openai_models(st.session_state.openai_key)
            st.selectbox(
                "Model",
                options=openai_models,
                key="openai_model",
                on_change=_on_openai_model,
                help="OpenAI chat model to use for AI features",
            )
        elif p == "gemini":
            st.text_input(
                "Gemini API key",
                key="gemini_key",
                type="password",
                placeholder="Your Gemini key",
                on_change=sync_config,
            )

            def _on_gemini_model():
                from creo.runtime_config import set_gemini_model, persist_config
                set_gemini_model(st.session_state.gemini_model)
                persist_config()

            gemini_models = _fetch_gemini_models(st.session_state.gemini_key)
            st.selectbox(
                "Model",
                options=gemini_models,
                key="gemini_model",
                on_change=_on_gemini_model,
                help="Gemini model to use for AI features",
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
            persist_config()
            st.success("API keys saved and persisted")

    with st.container(border=True):
        st.subheader("Data source")
        st.caption("Choose where to pull data from")

        current = get_data_source()
        source = st.radio("Data source", options=["json", "db", "api"], index=["json", "db", "api"].index(current), horizontal=True, format_func=lambda x: {"json": "JSON files", "db": "SQLite database", "api": "External APIs"}[x])
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
        st.subheader("Developer tools")
        st.caption("Debug logging for API calls")

        def _on_debug_toggle():
            from creo.runtime_config import set_debug_logging, persist_config
            set_debug_logging(st.session_state.debug_logging)
            persist_config()

        st.toggle(
            "Enable debug API logging",
            key="debug_logging",
            on_change=_on_debug_toggle,
            help="Logs all LLM API calls with timing and previews. View logs in the API Logs page.",
        )
        if st.session_state.debug_logging:
            count = len(st.session_state.get("api_logs", []))
            st.caption(f"{count} log entries captured so far")
            if count > 0 and st.button("Clear logs", icon=":material/delete_sweep:"):
                from creo.debug_logger import clear_logs
                clear_logs()
                st.rerun()


    with st.container(border=True):
        st.subheader("Mock data")
        st.caption("Reset sample data to default state after testing")

        with st.popover("Reset all mock data", icon=":material/refresh:"):
            st.warning("This will permanently discard all changes to sample data.")
            st.caption("Creators, campaigns, payments, applications, assignments, and notes will be restored to defaults.")
            if st.button("Yes, reset everything", type="primary", use_container_width=True):
                import subprocess
                from creo.config import ROOT_DIR
                try:
                    subprocess.run(
                        ["git", "checkout", "--", "data/sample_data/"],
                        cwd=str(ROOT_DIR),
                        capture_output=True, text=True, check=True,
                    )
                    st.success("Mock data reset to defaults")
                    st.rerun()
                except subprocess.CalledProcessError as e:
                    st.error(f"Reset failed: {e.stderr or e.stdout}")
                except FileNotFoundError:
                    st.error("git not found — cannot reset")

    with st.container(border=True):
        st.subheader("About Creo")
        st.markdown("""
        **Creo** is an AI-powered platform for creator onboarding, management, and campaign operations.

        - **Mock mode** — fully functional with simulated AI responses
        - **OpenAI** — configurable model selection (default: GPT-4o)
        - **Gemini** — configurable model selection (default: Gemini 1.5 Pro)

        Configuration is persisted to `.env` (excluded from version control).
        """)

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in settings")
