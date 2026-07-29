import streamlit as st
import pandas as pd

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.agents.application_reviewer import ApplicationReviewerAgent
from creo.utils.helpers import load_applications, save_applications, today_str

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
cs = st.session_state.cs
cams = st.session_state.cams

reviewer = ApplicationReviewerAgent()
all_apps = load_applications()

st.title("Applications")
st.caption("AI-powered review of creator applications")

tab1, tab2, tab3 = st.tabs(["Pending reviews", "Reviewed", "All applications"])

with tab1:
    pending = [a for a in all_apps if a.status == "pending"]
    if not pending:
        st.info("No pending applications to review.", icon=":material/inbox:")
    else:
        for app in pending:
            creator = cs.get_by_id(app.creator_id)
            campaign = cams.get_by_id(app.campaign_id)
            if not creator or not campaign:
                continue

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{creator.name}** → *{campaign.title}* ({campaign.brand})")
                    st.caption(f"Applied: {app.applied_at} | Niche: {creator.primary_niche} | Language: {creator.primary_language}")
                with c2:
                    st.badge(app.status, icon=":material/schedule:")

                result_key = f"review_result_{app.id}"
                if st.button("AI review", key=f"btn_{app.id}", icon=":material/rate_review:", type="primary"):
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
                        st.session_state[result_key] = result
                    st.rerun()

                result = st.session_state.get(result_key)
                if app.score:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Score", f"{app.score}/10")
                    c2.metric("Niche", f'{result.get("niche_alignment", "N/A")}/10' if result else "N/A")
                    c3.metric("Quality", f'{result.get("quality_score", "N/A")}/10' if result else "N/A")
                    c4.metric("Engagement", f'{result.get("engagement_score", "N/A")}/10' if result else "N/A")

                    if result and result.get("risks"):
                        with st.expander("Risk flags", icon=":material/warning:"):
                            for r in result["risks"]:
                                st.warning(r, icon=":material/warning:")

                    if result and result.get("recommendation"):
                        rec = result["recommendation"]
                        msg = result.get("feedback", "")
                        if rec == "accept":
                            st.success(f":material/check_circle: Recommend: **Accept** — {msg}")
                        elif rec == "shortlist":
                            st.warning(f":material/format_list_bulleted: Recommend: **Shortlist** — {msg}")
                        else:
                            st.error(f":material/block: Recommend: **Reject** — {msg}")

with tab2:
    reviewed = [a for a in all_apps if a.status != "pending"]
    if not reviewed:
        st.info("No reviewed applications yet.", icon=":material/inbox:")
    else:
        for app in reviewed:
            creator = cs.get_by_id(app.creator_id)
            campaign = cams.get_by_id(app.campaign_id)
            if not creator or not campaign:
                continue
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.markdown(f"**{creator.name}**")
                with c2:
                    st.write(campaign.title[:30] + "..." if len(campaign.title) > 30 else campaign.title)
                with c3:
                    ic = ":material/check:" if app.status in ("accepted", "shortlisted") else ":material/close:"
                    st.badge(app.status, icon=ic)
                if app.ai_notes:
                    with st.expander("AI notes", icon=":material/description:"):
                        st.write(app.ai_notes)

with tab3:
    rows = []
    for app in all_apps:
        creator = cs.get_by_id(app.creator_id)
        campaign = cams.get_by_id(app.campaign_id)
        rows.append({
            "ID": app.id,
            "Creator": creator.name if creator else "Unknown",
            "Campaign": campaign.title if campaign else "Unknown",
            "Brand": campaign.brand if campaign else "Unknown",
            "Status": app.status,
            "Score": app.score or 0,
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True)
