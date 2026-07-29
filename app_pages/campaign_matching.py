import streamlit as st
import pandas as pd

from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.core.agents.matching_agent import MatchingAgent

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
cs = st.session_state.cs
cams = st.session_state.cams

matcher = MatchingAgent()

st.title("Campaign matching")
st.caption("AI-powered creator-campaign matchmaking")

col1, col2 = st.columns([1, 2])

with col1:
    opts = [("all", "All active campaigns")] + [
        (c.id, f"{c.title} ({c.brand})") for c in cams.get_active_campaigns()
    ]
    selected = st.selectbox("Select campaign", options=opts, format_func=lambda x: x[1])

    niches = sorted(cs.get_niche_distribution().keys())
    niche_f = st.selectbox("Filter by niche", ["All"] + niches)

    langs = sorted(cs.get_language_distribution().keys())
    lang_f = st.selectbox("Filter by language", ["All"] + langs)

    min_f = st.number_input("Min followers", min_value=0, value=0, step=10000)

    run = st.button("Run AI matching", type="primary", icon=":material/target:")

pool = cs.creators
if niche_f != "All":
    pool = [c for c in pool if c.primary_niche == niche_f or niche_f in c.secondary_niches]
if lang_f != "All":
    pool = [c for c in pool if c.primary_language == lang_f or lang_f in c.secondary_languages]
if min_f > 0:
    pool = [c for c in pool if c.total_followers >= min_f]

with col2:
    if run and selected:
        cid = selected[0]
        campaigns = cams.get_active_campaigns() if cid == "all" else [cams.get_by_id(cid)]

        all_matches = []
        for campaign in campaigns:
            if not campaign:
                continue
            with st.spinner(f"Matching for {campaign.title}..."):
                for creator in pool:
                    m = matcher.match(creator, campaign)
                    all_matches.append({"campaign": campaign, "creator": creator, "match": m})

        all_matches.sort(key=lambda x: x["match"]["overall_score"], reverse=True)
        st.markdown(f"**Top matches** ({len(all_matches)} evaluated)")

        for m in all_matches[:10]:
            campaign = m["campaign"]
            creator = m["creator"]
            match = m["match"]

            with st.container(border=True):
                c1, c2 = st.columns([2, 2])
                with c1:
                    st.markdown(f"**{creator.name}**")
                    st.caption(f"{creator.primary_niche} | {creator.primary_language}")
                    st.write(f":material/people: {creator.total_followers:,} followers | :material/timeline: {creator.avg_engagement_rate}% engagement")
                with c2:
                    score = match["overall_score"]
                    if score >= 8:
                        st.success(f"**{score}/10** — {match.get('match_quality', '').title()}")
                    elif score >= 6:
                        st.warning(f"**{score}/10** — {match.get('match_quality', '').title()}")
                    else:
                        st.error(f"**{score}/10** — {match.get('match_quality', '').title()}")

                    with st.expander("Why this match?", icon=":material/insights:"):
                        for pt in match.get("alignment_points", []):
                            st.markdown(f":material/check: {pt}")
                        st.markdown("**Detailed scores:**")
                        for k, v in match.items():
                            if k.endswith("_score") or k.endswith("_overlap"):
                                label = k.replace("_score", "").replace("_overlap", "").replace("_", " ").title()
                                st.markdown(f"- {label}: {v}/10")

                st.caption(f"Campaign: **{campaign.title}** ({campaign.brand}) — ₹{campaign.budget:,.0f}")

    else:
        st.info("Select a campaign and click **Run AI matching** to find the best creator matches.")

st.subheader("Active campaigns overview")
active = cams.get_active_campaigns()
if active:
    rows = [{"Campaign": c.title, "Brand": c.brand, "Budget": f"₹{c.budget:,.0f}", "Deadline": c.deadline, "Assigned": len(c.assigned_creators)} for c in active]
    st.dataframe(pd.DataFrame(rows), hide_index=True)
