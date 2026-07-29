import streamlit as st

st.set_page_config(
    page_title="Creo — Creator Success Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.core.config import AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY
from src.core.rag.retrieval import FAQRetriever
from src.core.rag.vector_store import VectorStoreManager
from src.utils.helpers import load_faqs


def init_vector_store():
    if "vector_initialized" not in st.session_state:
        with st.spinner("Initializing knowledge base..."):
            try:
                retriever = FAQRetriever()
                retriever.initialize()
                st.session_state.vector_initialized = True
            except Exception as e:
                st.session_state.vector_initialized = False


def sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:1rem 0;">
                <span style="font-size:2rem;font-weight:800;color:#1E88E5;">CREO</span>
                <br>
                <span style="font-size:0.8rem;color:#666;">Creator Success Platform</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown("### AI Provider")
        provider = st.selectbox(
            "Select AI provider",
            options=["mock", "openai", "gemini"],
            index=0,
            help="Mock uses rule-based logic. OpenAI/Gemini require API keys.",
        )

        if provider == "openai" and not OPENAI_API_KEY:
            st.warning("⚠️ OpenAI key not configured. Set OPENAI_API_KEY in .streamlit/secrets.toml")
        elif provider == "gemini" and not GEMINI_API_KEY:
            st.warning("⚠️ Gemini key not configured. Set GEMINI_API_KEY in .streamlit/secrets.toml")
        elif provider != "mock":
            st.success(f"✅ {provider.title()} mode active")

        st.divider()

        st.markdown("### Quick Stats")
        try:
            from src.core.services.creator_service import CreatorService
            from src.core.services.campaign_service import CampaignService
            from src.core.services.payment_service import PaymentService

            cs = CreatorService()
            cams = CampaignService()
            ps = PaymentService()

            st.metric("Total Creators", len(cs.creators))
            st.metric("Active Campaigns", cams.get_active_count())
            st.metric("Pending Payments", ps.get_pending_count())
        except Exception:
            pass

        st.divider()

        st.markdown(
            """
            <div style="font-size:0.7rem;color:#999;text-align:center;">
                Built with Streamlit + LangChain<br>
                © 2026 Creo
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    sidebar()
    init_vector_store()

    st.markdown(
        """
        <div style="text-align:center;padding:3rem 1rem;">
            <span style="font-size:3rem;font-weight:800;color:#1E88E5;">CREO</span>
            <p style="font-size:1.2rem;color:#666;margin-top:0.5rem;">
                AI-Powered Creator Success Platform
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("### 📋 Applications")
            st.write("Review and score creator applications with AI-powered insights.")
    with col2:
        with st.container(border=True):
            st.markdown("### ✅ Verification")
            st.write("Automated profile and social media verification.")
    with col3:
        with st.container(border=True):
            st.markdown("### 🏷️ Categorization")
            st.write("AI-driven niche and language tagging.")

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("### 🎯 Campaign Matching")
            st.write("Semantic matching with explainable AI scores.")
    with col2:
        with st.container(border=True):
            st.markdown("### 💬 Creator Queries")
            st.write("RAG-powered FAQ chatbot with source citations.")
    with col3:
        with st.container(border=True):
            st.markdown("### 📅 Follow-Ups")
            st.write("Deadline tracking and automated reminders.")

    st.divider()

    st.markdown("### 🚀 Quick Navigation")
    st.markdown("""
    | Page | Description |
    |------|-------------|
    | 📊 **Dashboard** | Executive overview with KPIs and charts |
    | 📋 **Applications** | AI review of creator applications |
    | ✅ **Verification** | Profile and social media verification |
    | 🏷️ **Categorization** | Niche and language classification |
    | 🎯 **Campaign Matching** | Creator-campaign matchmaking |
    | 💬 **Creator Queries** | AI FAQ chatbot |
    | 📅 **Follow-Ups** | Deadline and deliverable tracking |
    | 💰 **Payments** | Payment status and coordination |
    | 👥 **Creator CRM** | Full creator record management |
    """)

    st.info(
        "👈 Select a page from the sidebar to get started. "
        "The app works in **mock mode** by default — add API keys in `.streamlit/secrets.toml` for full AI features."
    )


if __name__ == "__main__":
    main()
