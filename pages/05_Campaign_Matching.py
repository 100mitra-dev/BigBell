import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Campaign Matching", page_icon="🎯", layout="wide")

from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.core.agents.matching_agent import MatchingAgent
from src.utils.display import section_header, status_badge


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    if "campaign_service" not in st.session_state:
        st.session_state.campaign_service = CampaignService()
    return st.session_state.creator_service, st.session_state.campaign_service


cs, cams = load_data()
matcher = MatchingAgent()

section_header("Creator-Campaign Matching", "AI-powered semantic matching with explainability")

col1, col2 = st.columns([1, 2])

with col1:
    campaign_options = [("all", "All Active Campaigns")] + [
        (c.id, f"{c.title} ({c.brand})") for c in cams.get_active_campaigns()
    ]
    selected_campaign_id = st.selectbox(
        "Select Campaign",
        options=campaign_options,
        format_func=lambda x: x[1],
    )

    niche_filter = st.selectbox("Filter by Niche", ["All"] + sorted(cs.get_niche_distribution().keys()))
    lang_filter = st.selectbox("Filter by Language", ["All"] + sorted(cs.get_language_distribution().keys()))
    min_followers = st.number_input("Min Followers", min_value=0, value=0, step=10000)

    run_match = st.button("Run AI Matching", type="primary", use_container_width=True)

creators_pool = cs.creators
if niche_filter != "All":
    creators_pool = [c for c in creators_pool if c.primary_niche == niche_filter or niche_filter in c.secondary_niches]
if lang_filter != "All":
    creators_pool = [c for c in creators_pool if c.primary_language == lang_filter or lang_filter in c.secondary_languages]
if min_followers > 0:
    creators_pool = [c for c in creators_pool if c.total_followers >= min_followers]

with col2:
    if run_match and selected_campaign_id:
        campaign_id = selected_campaign_id[0]
        if campaign_id == "all":
            campaigns = cams.get_active_campaigns()
        else:
            campaigns = [cams.get_by_id(campaign_id)]

        all_matches = []
        for campaign in campaigns:
            if not campaign:
                continue
            with st.spinner(f"Matching creators for {campaign.title}..."):
                for creator in creators_pool:
                    result = matcher.match(creator, campaign)
                    all_matches.append({
                        "campaign": campaign,
                        "creator": creator,
                        "match": result,
                    })

        all_matches.sort(key=lambda x: x["match"]["overall_score"], reverse=True)

        st.subheader(f"Top Matches ({len(all_matches)} evaluated)")

        for m in all_matches[:10]:
            campaign = m["campaign"]
            creator = m["creator"]
            match = m["match"]

            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.markdown(f"**{creator.name}**")
                    st.caption(f"{creator.primary_niche} | {creator.primary_language}")
                    st.write(f"📊 {creator.total_followers:,} followers | ❤️ {creator.avg_engagement_rate}% engagement")

                with col2:
                    score = match["overall_score"]
                    color = "#2ECC71" if score >= 8 else "#F39C12" if score >= 6 else "#E74C3C"
                    st.markdown(f"<span style='font-size:2rem;font-weight:700;color:{color}'>{score}/10</span>", unsafe_allow_html=True)
                    st.markdown(f"**Quality:** {match.get('match_quality', 'N/A').title()}")

                    with st.expander("Why this match?"):
                        for point in match.get("alignment_points", []):
                            st.markdown(f"✅ {point}")
                        st.divider()
                        st.markdown("**Detailed Scores:**")
                        scores = {k: v for k, v in match.items() if k.endswith("_score")}
                        for k, v in scores.items():
                            label = k.replace("_score", "").replace("_", " ").title()
                            st.markdown(f"- {label}: {v}/10")

                with col3:
                    st.markdown(f"**{campaign.title}**")
                    st.caption(campaign.brand)
                    st.write(f"💰 ₹{campaign.budget:,.0f}")

    else:
        st.info("Select a campaign and click 'Run AI Matching' to find the best creator matches.")

st.divider()
st.subheader("Active Campaigns Overview")
active = cams.get_active_campaigns()
if active:
    df = pd.DataFrame([
        {"Campaign": c.title, "Brand": c.brand, "Budget": f"₹{c.budget:,.0f}", "Deadline": c.deadline, "Assigned": len(c.assigned_creators)}
        for c in active
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
