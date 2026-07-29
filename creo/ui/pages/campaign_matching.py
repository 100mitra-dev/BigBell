import streamlit as st
import pandas as pd
import uuid

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.agents.matching_agent import MatchingAgent
from creo.models import Campaign
from creo.config import NICHES, LANGUAGES
from creo.storage.csv_handler import export_campaigns_to_csv, import_campaigns_from_csv

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

    run = st.button("Run AI matching", type="primary", icon=":material/target:", use_container_width=True)

    st.markdown("---")
    st.subheader("Campaign management")

    c1, c2 = st.columns(2)
    with c1:
        st.toggle("Add", key="show_add_campaign_toggle", help="Show add campaign form")
    with c2:
        csv_data = export_campaigns_to_csv(cams.campaigns)
        st.download_button("Export CSV", data=csv_data, file_name="campaigns.csv", mime="text/csv", icon=":material/download:", use_container_width=True)

    uploaded = st.file_uploader("Import campaigns from CSV", type="csv", label_visibility="collapsed")
    if uploaded:
        content = uploaded.getvalue().decode("utf-8")
        imported = import_campaigns_from_csv(content)
        for camp in imported:
            cams.add(camp)
        st.success(f"Imported {len(imported)} campaigns")
        st.rerun()

    if st.session_state.get("show_add_campaign_toggle"):
        with st.container(border=True):
            st.markdown("**Add campaign**")
            with st.form("add_campaign_form"):
                title = st.text_input("Campaign title")
                brand = st.text_input("Brand")
                description = st.text_area("Description")
                col_budget, col_deadline = st.columns(2)
                with col_budget:
                    budget = st.number_input("Budget (₹)", min_value=0.0, value=10000.0, step=5000.0)
                with col_deadline:
                    deadline = st.date_input("Deadline")
                target_niches = st.multiselect("Target niches", NICHES)
                target_languages = st.multiselect("Target languages", LANGUAGES)
                submitted = st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True)
                if submitted and title and brand:
                    campaign = Campaign(
                        id=str(uuid.uuid4()),
                        title=title,
                        brand=brand,
                        description=description,
                        budget=budget,
                        deadline=deadline.isoformat(),
                        target_niches=target_niches,
                        target_languages=target_languages,
                        status="active",
                    )
                    cams.add(campaign)
                    st.session_state.show_add_campaign_toggle = False
                    st.rerun()

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

                if st.button("Delete campaign", key=f"del_camp_{campaign.id}", icon=":material/delete:"):
                    cams.delete(campaign.id)
                    st.rerun()

    else:
        st.info("Select a campaign and click **Run AI matching** to find the best creator matches.")

st.subheader("Active campaigns overview")
active = cams.get_active_campaigns()
if active:
    rows = [{"Campaign": c.title, "Brand": c.brand, "Budget": f"₹{c.budget:,.0f}", "Deadline": c.deadline, "Assigned": len(c.assigned_creators)} for c in active]
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True)
    for _, row in df.iterrows():
        c = cams.get_by_id([x.id for x in active if x.title == row["Campaign"]][0])
        if c:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c2:
                st.toggle("Edit", key=f"edit_camp_{c.id}", help="Edit this campaign")
            with c3:
                if st.button("Delete", key=f"del_camp_overview_{c.id}", icon=":material/delete:"):
                    cams.delete(c.id)
                    st.rerun()

            if st.session_state.get(f"edit_camp_{c.id}"):
                with st.container(border=True):
                    st.markdown(f"**Edit: {c.title}**")
                    with st.form(f"edit_camp_form_{c.id}"):
                        e_title = st.text_input("Title", value=c.title)
                        e_brand = st.text_input("Brand", value=c.brand)
                        e_desc = st.text_area("Description", value=c.description)
                        e_budget = st.number_input("Budget (₹)", min_value=0.0, value=c.budget, step=5000.0)
                        e_deadline = st.date_input("Deadline", value=pd.to_datetime(c.deadline).date() if c.deadline else None)
                        e_niches = st.multiselect("Target niches", NICHES, default=c.target_niches)
                        e_langs = st.multiselect("Target languages", LANGUAGES, default=c.target_languages)
                        saved = st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True)
                        if saved:
                            c.title = e_title
                            c.brand = e_brand
                            c.description = e_desc
                            c.budget = e_budget
                            c.deadline = e_deadline.isoformat() if e_deadline else c.deadline
                            c.target_niches = e_niches
                            c.target_languages = e_langs
                            cams.repo.save_all(cams.campaigns)
                            st.session_state[f"edit_camp_{c.id}"] = False
                            st.rerun()
