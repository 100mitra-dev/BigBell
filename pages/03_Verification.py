import streamlit as st
import pandas as pd

st.set_page_config(page_title="Verification", page_icon="✅", layout="wide")

from src.core.services.creator_service import CreatorService
from src.core.agents.verification_agent import VerificationAgent
from src.utils.display import section_header, status_badge, creator_card


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    return st.session_state.creator_service


cs = load_data()
verifier = VerificationAgent()

section_header("Profile Verification", "Automated social media and profile verification")

tab1, tab2 = st.tabs(["Pending Verification", "All Profiles"])

with tab1:
    pending = cs.filter_by_status("pending") + cs.filter_by_status("onboarding")
    if not pending:
        st.info("No creators pending verification.")
    else:
        for creator in pending[:10]:
            with st.container(border=True):
                creator_card(creator, compact=True)
                if st.button(f"Run Verification", key=f"verify_{creator.id}"):
                    with st.spinner(f"Verifying {creator.name}..."):
                        result = verifier.verify(creator)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Verification Score", f'{result.get("overall_score", 0)}/100')
                        if result.get("verified"):
                            st.success("✅ Verified")
                        else:
                            st.error("❌ Not Verified")

                    with col2:
                        if result.get("issues"):
                            for issue in result["issues"]:
                                st.warning(issue)

                    if result.get("content_quality"):
                        cq = result["content_quality"]
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Quality Score", f'{cq.get("score", 0)}/10')
                        col2.metric("Consistency", f'{cq.get("consistency", 0)}/10')
                        col3.metric("Originality", f'{cq.get("originality", 0)}/10')

                    with st.expander("Platform Details"):
                        for platform, pdata in result.get("platforms", {}).items():
                            st.write(f"**{platform.title()}**")
                            st.json(pdata)

                    if result.get("verified"):
                        if st.button(f"Approve {creator.name}", key=f"approve_{creator.id}"):
                            cs.update_status(creator.id, "active")
                            st.success(f"{creator.name} approved and moved to Active!")
                            st.rerun()

with tab2:
    search = st.text_input("Search creators...", placeholder="Name, niche, or language...")
    creators = cs.search(search) if search else cs.creators

    for creator in creators:
        with st.container(border=True):
            creator_card(creator)
            st.markdown(status_badge(creator.status.value), unsafe_allow_html=True)

            if creator.platforms:
                with st.expander("Platform Details"):
                    for name, info in creator.platforms.items():
                        st.write(f"**{name.title()}**: {info.handle} | {info.followers:,} followers | {'✅ Verified' if info.verified else '❌ Unverified'}")
