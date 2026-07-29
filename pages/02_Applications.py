import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Applications", page_icon="📋", layout="wide")

from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.core.agents.application_reviewer import ApplicationReviewerAgent
from src.utils.display import section_header, status_badge
from src.utils.helpers import load_applications, save_applications, today_str
from src.core.models import Application


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    if "campaign_service" not in st.session_state:
        st.session_state.campaign_service = CampaignService()
    return st.session_state.creator_service, st.session_state.campaign_service


cs, cams = load_data()
reviewer = ApplicationReviewerAgent()

all_apps = load_applications()

section_header("Application Review", "AI-powered review of creator applications")

tab1, tab2, tab3 = st.tabs(["Pending Reviews", "Reviewed", "All Applications"])

with tab1:
    pending = [a for a in all_apps if a.status == "pending"]
    if not pending:
        st.info("No pending applications to review.")
    else:
        for app in pending:
            creator = cs.get_by_id(app.creator_id)
            campaign = cams.get_by_id(app.campaign_id)
            if not creator or not campaign:
                continue

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{creator.name}** → *{campaign.title}* ({campaign.brand})")
                    st.caption(f"Applied: {app.applied_at} | Niche: {creator.primary_niche} | Language: {creator.primary_language}")
                with col2:
                    st.markdown(status_badge(app.status), unsafe_allow_html=True)

                if st.button(f"AI Review #{app.id}", key=f"review_{app.id}"):
                    with st.spinner("AI reviewing application..."):
                        result = reviewer.review(creator, campaign)
                        app.score = result["score"]
                        app.ai_notes = result["feedback"]
                        app.reviewed_at = today_str()
                        app.status = "reviewed"

                        if result.get("recommendation") == "accept":
                            app.status = "shortlisted"
                        elif result.get("recommendation") == "reject":
                            app.status = "rejected"

                        save_applications(all_apps)
                        st.rerun()

                if app.score:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Score", f"{app.score}/10")
                    col2.metric("Niche", f'{result.get("niche_alignment", "N/A")}/10')
                    col3.metric("Quality", f'{result.get("quality_score", "N/A")}/10')
                    col4.metric("Engagement", f'{result.get("engagement_score", "N/A")}/10')

                    if result and result.get("risks"):
                        with st.expander("⚠️ Risk Flags"):
                            for r in result["risks"]:
                                st.warning(r)

                    if result and result.get("recommendation"):
                        rec = result["recommendation"]
                        if rec == "accept":
                            st.success(f"✅ Recommendation: **Accept** - {result.get('feedback', '')}")
                        elif rec == "shortlist":
                            st.warning(f"📋 Recommendation: **Shortlist** - {result.get('feedback', '')}")
                        else:
                            st.error(f"❌ Recommendation: **Reject** - {result.get('feedback', '')}")

with tab2:
    reviewed = [a for a in all_apps if a.status != "pending"]
    if not reviewed:
        st.info("No reviewed applications yet.")
    else:
        for app in reviewed:
            creator = cs.get_by_id(app.creator_id)
            campaign = cams.get_by_id(app.campaign_id)
            if not creator or not campaign:
                continue
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                col1.write(f"**{creator.name}**")
                col2.write(campaign.title[:30] + "...")
                col3.write(f"Score: {app.score or 'N/A'}/10")
                col4.markdown(status_badge(app.status), unsafe_allow_html=True)
                if app.ai_notes:
                    with st.expander("AI Notes"):
                        st.write(app.ai_notes)

with tab3:
    df_data = []
    for app in all_apps:
        creator = cs.get_by_id(app.creator_id)
        campaign = cams.get_by_id(app.campaign_id)
        df_data.append({
            "ID": app.id,
            "Creator": creator.name if creator else "Unknown",
            "Campaign": campaign.title if campaign else "Unknown",
            "Brand": campaign.brand if campaign else "Unknown",
            "Status": app.status,
            "Score": app.score or "-",
            "Applied": app.applied_at,
        })
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
