import streamlit as st
import pandas as pd
import uuid

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.services.assignment_service import AssignmentService, STATUS_LABELS, STATUS_COLORS, NEXT_STATUS, AssignmentStatus
from creo.agents.matching_agent import MatchingAgent
from creo.models import Campaign
from creo.config import get_all_niches, LANGUAGES
from creo.storage.csv_handler import export_campaigns_to_csv, import_campaigns_from_csv

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
if "asvc" not in st.session_state:
    st.session_state.asvc = AssignmentService()
cs = st.session_state.cs
cams = st.session_state.cams
asvc = st.session_state.asvc

for c in cams.campaigns:
    for cid in c.assigned_creators:
        if not asvc.is_assigned(c.id, cid):
            asvc.assign(c.id, cid)

matcher = MatchingAgent()

st.title("Match Creators")
st.caption("AI-powered creator–campaign matchmaking with assignment workflow")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Active campaigns", cams.get_active_count())
m2.metric("Total creators", len(cs.creators))
m3.metric("Total budget", f"₹{cams.get_total_budget():,.0f}")
m4.metric("Assignments", len(asvc.assignments))

left, right = st.columns([1, 2])

with left:
    with st.container(border=True):
        st.markdown("**Campaign**")
        opts = [("all", "All active campaigns")] + [
            (c.id, f"{c.title} ({c.brand})") for c in cams.get_active_campaigns()
        ]
        selected = st.selectbox("Select", options=opts, format_func=lambda x: x[1], label_visibility="collapsed")

        st.markdown("**Creator filters**")
        niches = sorted(cs.get_niche_distribution().keys())
        niche_f = st.selectbox("Niche", ["All"] + niches, label_visibility="collapsed")
        langs = sorted(cs.get_language_distribution().keys())
        lang_f = st.selectbox("Language", ["All"] + langs, label_visibility="collapsed")
        min_f = st.number_input("Min followers", min_value=0, value=0, step=10000, label_visibility="collapsed")

        run = st.button("Run AI matching", type="primary", icon=":material/target:", use_container_width=True)

pool = cs.creators
if niche_f != "All":
    pool = [c for c in pool if c.primary_niche == niche_f or niche_f in c.secondary_niches]
if lang_f != "All":
    pool = [c for c in pool if c.primary_language == lang_f or lang_f in c.secondary_languages]
if min_f > 0:
    pool = [c for c in pool if c.total_followers >= min_f]

with right:
    if run and selected:
        cid = selected[0]
        targets = cams.get_active_campaigns() if cid == "all" else [cams.get_by_id(cid)]

        all_matches = []
        for campaign in targets:
            if not campaign:
                continue
            with st.spinner(f"Matching for {campaign.title}..."):
                for creator in pool:
                    all_matches.append({"campaign": campaign, "creator": creator, "match": matcher.match(creator, campaign)})

        all_matches.sort(key=lambda x: x["match"]["overall_score"], reverse=True)
        top_matches = all_matches[:30]

        st.markdown(f"### Top matches")
        st.caption(f"{len(all_matches)} evaluated, showing top {len(top_matches)}")

        bulk_col1, bulk_col2 = st.columns([3, 1])
        with bulk_col1:
            assign_all = st.button("Assign all visible", type="primary", icon=":material/select_all:", use_container_width=True)
        with bulk_col2:
            st.markdown('<div style="height:0.25rem"></div>', unsafe_allow_html=True)
            show_board = st.toggle("Status board", key="show_status_board", value=False)

        if assign_all:
            for m in top_matches:
                campaign = m["campaign"]
                creator = m["creator"]
                score = m["match"]["overall_score"]
                if not asvc.is_assigned(campaign.id, creator.id):
                    asvc.assign(campaign.id, creator.id, score=score)
                    if creator.id not in campaign.assigned_creators:
                        campaign.assigned_creators.append(creator.id)
                        cams.repo.save_all(cams.campaigns)
            st.success(f"Assigned {len(top_matches)} creators")
            st.rerun()

        for idx, m in enumerate(top_matches):
            campaign = m["campaign"]
            creator = m["creator"]
            match = m["match"]
            score = match["overall_score"]
            assignment = asvc.get_for_campaign_creator(campaign.id, creator.id)

            with st.container(border=True):
                row = st.columns([2, 1, 1.2])
                with row[0]:
                    st.markdown(f"**{creator.name}**")
                    st.caption(f"{creator.primary_niche} · {creator.primary_language}")
                    st.markdown(f":material/people: {creator.total_followers:,} followers · :material/timeline: {creator.avg_engagement_rate}% engagement")
                with row[1]:
                    color = "green" if score >= 8 else "orange" if score >= 6 else "red"
                    st.markdown(f":material/{'check_circle' if score>=8 else 'warning' if score>=6 else 'error'}:")
                    st.markdown(f"<span style='font-size:1.5rem;font-weight:700;color:{color}'>{score}/10</span>", unsafe_allow_html=True)
                    st.markdown(f"*{match.get('match_quality', '').title()}*")
                with row[2]:
                    if assignment:
                        sc = assignment.status
                        badge_color = STATUS_COLORS.get(sc.value, "#95A5A6")
                        label = STATUS_LABELS.get(sc, sc.value)
                        st.markdown(f'<span style="background:{badge_color}22;color:{badge_color};padding:2px 10px;border-radius:10px;font-size:0.8rem;font-weight:600">{label}</span>', unsafe_allow_html=True)

                        nxt_status = NEXT_STATUS.get(sc)
                        if nxt_status:
                            if st.button(f"Advance to {STATUS_LABELS.get(nxt_status, nxt_status.value)}", key=f"adv_{assignment.id}", icon=":material/arrow_forward:", use_container_width=True):
                                nxt = asvc.advance_status(assignment.id)
                                if nxt:
                                    st.success(f"Advanced to **{STATUS_LABELS.get(nxt, nxt.value)}**")
                                st.rerun()
                        if st.button("Unassign", key=f"unas_{assignment.id}", icon=":material/person_remove:", use_container_width=True):
                            asvc.unassign(campaign.id, creator.id)
                            if creator.id in campaign.assigned_creators:
                                campaign.assigned_creators.remove(creator.id)
                                cams.repo.save_all(cams.campaigns)
                            st.success(f"Unassigned {creator.name}")
                            st.rerun()
                    else:
                        if st.button("Assign", key=f"ass_{creator.id}_{campaign.id}", icon=":material/person_add:", type="primary", use_container_width=True):
                            asvc.assign(campaign.id, creator.id, score=score)
                            if creator.id not in campaign.assigned_creators:
                                campaign.assigned_creators.append(creator.id)
                                cams.repo.save_all(cams.campaigns)
                            st.success(f"Assigned {creator.name}")
                            st.rerun()

                if not assignment:
                    with st.expander("Match breakdown", icon=":material/insights:"):
                        for pt in match.get("alignment_points", []):
                            st.markdown(f":material/check: {pt}")
                        st.markdown("**Scores**")
                        sc1, sc2, sc3, sc4 = st.columns(4)
                        sc1.metric("Niche", f'{match.get("niche_overlap", 0)}/10')
                        sc2.metric("Language", f'{match.get("language_overlap", 0)}/10')
                        sc3.metric("Engagement", f'{match.get("engagement_score", 0)}/10')
                        sc4.metric("Quality", f'{match.get("quality_score", 0)}/10')
                        sc1.metric("Reach", f'{match.get("reach_score", 0)}/10')
                        sc2.metric("Budget fit", f'{match.get("budget_fit", 0)}/10')
                        if creator.total_campaigns_completed > 0:
                            sc3.metric("Avg earnings/ campaign", f"₹{creator.total_earnings / creator.total_campaigns_completed:,.0f}")

                st.caption(f":material/campaign: {campaign.title} ({campaign.brand}) — ₹{campaign.budget:,.0f}")

        if show_board:
            st.divider()
            st.markdown("### Assignment status board")
            board_targets = targets if cid != "all" else cams.get_active_campaigns()
            for campaign in board_targets:
                if not campaign:
                    continue
                assignments = asvc.get_for_campaign(campaign.id)
                if not assignments:
                    continue
                with st.container(border=True):
                    st.markdown(f"**{campaign.title}** ({campaign.brand}) — {len(assignments)} assignments")
                    status_data = []
                    for a in assignments:
                        creator = cs.get_by_id(a.creator_id)
                        if not creator:
                            continue
                        sc = a.status
                        badge_color = STATUS_COLORS.get(sc.value, "#95A5A6")
                        label = STATUS_LABELS.get(sc, sc.value)
                        badge = f'<span style="background:{badge_color}22;color:{badge_color};padding:2px 10px;border-radius:10px;font-size:0.8rem;font-weight:600">{label}</span>'
                        status_data.append({"Creator": creator.name, "Status": badge, "Score": f"{a.score}/10", "Assigned": a.assigned_at})
                    df_status = pd.DataFrame(status_data)
                    st.write(df_status.to_html(escape=False, index=False), unsafe_allow_html=True)

    else:
        st.info("Select a campaign and filters on the left, then click **Run AI matching**.")

st.divider()
st.subheader("Campaign management")

act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
with act_col1:
    st.toggle("Add campaign", key="show_add_campaign_toggle")
with act_col2:
    import_btn = st.button("Import CSV", use_container_width=True, icon=":material/file_upload:")
with act_col3:
    csv_data = export_campaigns_to_csv(cams.campaigns)
    st.download_button("Export CSV", data=csv_data, file_name="campaigns.csv", mime="text/csv", use_container_width=True, icon=":material/file_download:")

if import_btn:
    st.session_state.show_import_camp = not st.session_state.get("show_import_camp", False)
if st.session_state.get("show_import_camp"):
    uploaded = st.file_uploader("Import CSV", type="csv", key="camp_csv_import")
    if uploaded:
        content = uploaded.getvalue().decode("utf-8")
        imported = import_campaigns_from_csv(content)
        for camp in imported:
            cams.add(camp)
        st.session_state.show_import_camp = False
        st.success(f"Imported {len(imported)} campaigns")
        st.rerun()

if st.session_state.get("show_add_campaign_toggle"):
    with st.container(border=True):
        st.markdown("**New campaign**")
        with st.form("add_campaign_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                title = st.text_input("Campaign title")
                brand = st.text_input("Brand")
                budget = st.number_input("Budget (₹)", min_value=0.0, value=10000.0, step=5000.0)
            with col_b:
                deadline = st.date_input("Deadline")
                target_niches = st.multiselect("Target niches", get_all_niches())
                target_languages = st.multiselect("Target languages", LANGUAGES)
            description = st.text_area("Description")
            if st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True) and title and brand:
                cams.add(Campaign(
                    id=str(uuid.uuid4()), title=title, brand=brand, description=description,
                    budget=budget, deadline=deadline.isoformat(),
                    target_niches=target_niches, target_languages=target_languages, status="active",
                ))
                st.session_state.show_add_campaign_toggle = False
                st.rerun()

all_campaigns = cams.campaigns
if all_campaigns:
    camp_data = []
    for c in all_campaigns:
        summary = asvc.get_campaign_summary(c.id)
        status_parts = [f"{k}: {v}" for k, v in summary.items()]
        camp_data.append({
            "ID": c.id, "Title": c.title, "Brand": c.brand,
            "Budget": f"₹{c.budget:,.0f}", "Deadline": c.deadline,
            "Status": c.status, "Assigned": len(c.assigned_creators),
        })
    df = pd.DataFrame(camp_data)
    st.dataframe(df, hide_index=True, use_container_width=True)

    for c in all_campaigns:
        cc1, cc2, cc3 = st.columns([4, 1, 1])
        with cc1:
            summary = asvc.get_campaign_summary(c.id)
            parts = "; ".join(f"{k}: {v}" for k, v in summary.items()) if summary else "0 assigned"
            st.caption(f"**{c.title}** ({c.brand}) — {c.status} — {parts}")
        with cc2:
            edit_on = st.toggle("Edit", key=f"ec_{c.id}")
        with cc3:
            if st.button("Delete", key=f"dc_{c.id}", icon=":material/delete:", use_container_width=True):
                for a in asvc.get_for_campaign(c.id):
                    asvc.repo.delete(a.id)
                asvc.refresh()
                cams.delete(c.id)
                st.rerun()

        if edit_on:
            with st.container(border=True):
                with st.form(f"edit_{c.id}"):
                    e1, e2 = st.columns(2)
                    with e1:
                        e_title = st.text_input("Title", value=c.title)
                        e_brand = st.text_input("Brand", value=c.brand)
                        e_budget = st.number_input("Budget (₹)", min_value=0.0, value=c.budget, step=5000.0)
                    with e2:
                        e_deadline = st.date_input("Deadline", value=pd.to_datetime(c.deadline).date() if c.deadline else None)
                        e_niches = st.multiselect("Target niches", get_all_niches(), default=[n for n in c.target_niches if n in get_all_niches()])
                        e_langs = st.multiselect("Target languages", LANGUAGES, default=c.target_languages)
                    e_desc = st.text_area("Description", value=c.description)
                    if st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True):
                        c.title = e_title
                        c.brand = e_brand
                        c.description = e_desc
                        c.budget = e_budget
                        c.deadline = e_deadline.isoformat() if e_deadline else c.deadline
                        c.target_niches = e_niches
                        c.target_languages = e_langs
                        cams.repo.save_all(cams.campaigns)
                        st.session_state[f"ec_{c.id}"] = False
                        st.rerun()
else:
    st.info("No campaigns yet. Add one above.", icon=":material/inbox:")
