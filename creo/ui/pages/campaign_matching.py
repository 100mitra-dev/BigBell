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
import logging

logger = logging.getLogger(__name__)

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
try:

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active campaigns", cams.get_active_count())
    m2.metric("Total creators", len(cs.creators))
    m3.metric("Total budget", f"₹{cams.get_total_budget():,.0f}")
    m4.metric("Assignments", len(asvc.assignments))

    picker_col, add_col, import_col, export_col = st.columns([2, 1, 1, 1])
    with picker_col:
        camp_opts = [("", "Select a campaign...")] + [(c.id, f"{c.title} ({c.brand})") for c in cams.campaigns]
        selected = st.selectbox("Campaign", options=camp_opts, format_func=lambda x: x[1], label_visibility="collapsed")
        selected_id = selected[0] if selected else ""
    with add_col:
        add_btn = st.button("Add campaign", use_container_width=True, icon=":material/add:")
        if add_btn:
            st.session_state.show_add_campaign = not st.session_state.get("show_add_campaign", False)
    with import_col:
        import_btn = st.button("Import CSV", use_container_width=True, icon=":material/file_upload:")
        if import_btn:
            st.session_state.show_import_camp = not st.session_state.get("show_import_camp", False)
    with export_col:
        csv_data = export_campaigns_to_csv(cams.campaigns)
        st.download_button("Export CSV", data=csv_data, file_name="campaigns.csv", mime="text/csv", use_container_width=True, icon=":material/file_download:")

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

    if st.session_state.get("show_add_campaign"):
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
                    st.session_state.show_add_campaign = False
                    st.rerun()

    if not selected_id:
        st.info("Select a campaign above to view details and manage assignments.", icon=":material/campaign:")
    else:
        campaign = cams.get_by_id(selected_id)
        if not campaign:
            st.error("Campaign not found.")
        else:
            if st.session_state.get("match_cid") != selected_id:
                st.session_state.match_results = None
                st.session_state.match_cid = selected_id

            with st.container(border=True):
                h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 1, 1])
                with h1:
                    st.markdown(f"### {campaign.title}")
                    st.caption(campaign.brand)
                with h2:
                    st.metric("Budget", f"₹{campaign.budget:,.0f}")
                with h3:
                    st.metric("Deadline", campaign.deadline)
                with h4:
                    st.metric("Status", campaign.status.title())
                with h5:
                    assignments = asvc.get_for_campaign(campaign.id)
                    st.metric("Assigned", len(assignments))

                niche_tags = " ".join(
                    f'<span style="background:#7C3AED15;color:#7C3AED;padding:2px 10px;border-radius:10px;font-size:0.8rem;margin-right:4px">{n}</span>'
                    for n in campaign.target_niches
                )
                lang_tags = " ".join(
                    f'<span style="background:#2563EB15;color:#2563EB;padding:2px 10px;border-radius:10px;font-size:0.8rem;margin-right:4px">{l}</span>'
                    for l in campaign.target_languages
                )
                if campaign.description:
                    st.markdown(campaign.description)
                st.markdown(f"**Target niches:** {niche_tags} &nbsp;&nbsp; **Languages:** {lang_tags}", unsafe_allow_html=True)

                if assignments:
                    summary = asvc.get_campaign_summary(campaign.id)
                    pct = min(100, int(len(assignments) / max(len(assignments) * 2, 1) * 100))
                    st.markdown(f"**Assignment progress** — {len(assignments)} assigned")
                    st.progress(pct / 100)
                    status_html = ""
                    for se, label in STATUS_LABELS.items():
                        count = summary.get(se.value, 0)
                        if count > 0:
                            color = STATUS_COLORS.get(se.value, "#95A5A6")
                            status_html += f'<span style="background:{color}22;color:{color};padding:2px 14px;border-radius:10px;font-size:0.8rem;font-weight:600;margin-right:6px">{label}: {count}</span> '
                    st.markdown(status_html, unsafe_allow_html=True)
                else:
                    st.info("No creators assigned yet. Use **Find Creators** to match creators.")

            left_col, right_col = st.columns([0.45, 0.55])

            with left_col:
                st.markdown("### Assigned Creators")
                assignments = asvc.get_for_campaign(campaign.id)

                if not assignments:
                    st.info("No creators assigned yet.")
                else:
                    for a in assignments:
                        creator = cs.get_by_id(a.creator_id)
                        if not creator:
                            continue
                        with st.container(border=True):
                            r1 = st.columns([3, 1])
                            with r1[0]:
                                st.markdown(f"**{creator.name}**")
                                st.caption(f"{creator.primary_niche} \u00b7 {creator.primary_language}")
                            with r1[1]:
                                sc = a.score
                                sc_color = "green" if sc >= 8 else "orange" if sc >= 6 else "red"
                                st.markdown(
                                    f'<div style="text-align:right"><span style="font-size:1.3rem;font-weight:700;color:{sc_color}">{sc}/10</span></div>',
                                    unsafe_allow_html=True,
                                )
                            st.markdown(
                                f":material/people: {creator.total_followers:,} followers \u00b7 "
                                f":material/timeline: {creator.avg_engagement_rate}% engagement"
                            )
                            sc_enum = a.status
                            badge_color = STATUS_COLORS.get(sc_enum.value, "#95A5A6")
                            label = STATUS_LABELS.get(sc_enum, sc_enum.value)
                            st.markdown(
                                f'<span style="background:{badge_color}22;color:{badge_color};padding:2px 14px;'
                                f'border-radius:10px;font-size:0.85rem;font-weight:600">{label}</span>',
                                unsafe_allow_html=True,
                            )
                            act = st.columns([1, 1, 1])
                            with act[0]:
                                nxt_status = NEXT_STATUS.get(sc_enum)
                                if nxt_status:
                                    nxt_label = STATUS_LABELS.get(nxt_status, nxt_status.value)
                                    if st.button(f"\u2192 {nxt_label}", key=f"adv_{a.id}", use_container_width=True):
                                        nxt = asvc.advance_status(a.id)
                                        if nxt:
                                            st.success(f"Advanced to **{STATUS_LABELS.get(nxt, nxt.value)}**")
                                        st.rerun()
                            with act[1]:
                                if sc_enum != AssignmentStatus.REJECTED:
                                    if st.button("Reject", key=f"rej_{a.id}", use_container_width=True):
                                        asvc.update_status(a.id, AssignmentStatus.REJECTED)
                                        st.rerun()
                            with act[2]:
                                if st.button("Unassign", key=f"unas_{a.id}", use_container_width=True):
                                    asvc.unassign(campaign.id, creator.id)
                                    if creator.id in campaign.assigned_creators:
                                        campaign.assigned_creators.remove(creator.id)
                                        cams.repo.save_all(cams.campaigns)
                                    st.rerun()

            with right_col:
                st.markdown("### Find Creators")
                niches = sorted(cs.get_niche_distribution().keys())
                f_niche = st.selectbox("Niche", ["All"] + niches, label_visibility="collapsed", key="find_niche")
                f_lang = st.selectbox(
                    "Language",
                    ["All"] + sorted(cs.get_language_distribution().keys()),
                    label_visibility="collapsed",
                    key="find_lang",
                )
                f_min = st.number_input("Min followers", min_value=0, value=0, step=10000, label_visibility="collapsed", key="find_min")

                pool = [c for c in cs.creators]
                if f_niche != "All":
                    pool = [c for c in pool if c.primary_niche == f_niche or f_niche in c.secondary_niches]
                if f_lang != "All":
                    pool = [c for c in pool if c.primary_language == f_lang or f_lang in c.secondary_languages]
                if f_min > 0:
                    pool = [c for c in pool if c.total_followers >= f_min]

                with st.container(border=True):
                    run_match = st.button("Run AI matching", type="primary", icon=":material/target:", use_container_width=True)
                    unassigned_pool = [c for c in pool if not asvc.is_assigned(campaign.id, c.id)]
                    st.markdown("**Or assign manually**")
                    if unassigned_pool:
                        assign_opts = {
                            f"{c.name} ({c.primary_niche}, {c.total_followers:,} followers)": c
                            for c in sorted(unassigned_pool, key=lambda x: -x.total_followers)
                        }
                        selected_labels = st.multiselect("Select creators", options=list(assign_opts.keys()), label_visibility="collapsed", key="manual_assign")
                        if selected_labels and st.button("Assign selected", icon=":material/person_add:", use_container_width=True):
                            for label in selected_labels:
                                c = assign_opts[label]
                                if not asvc.is_assigned(campaign.id, c.id):
                                    asvc.assign(campaign.id, c.id, score=5.0)
                                    if c.id not in campaign.assigned_creators:
                                        campaign.assigned_creators.append(c.id)
                                        cams.repo.save_all(cams.campaigns)
                            st.success(f"Assigned {len(selected_labels)} creator(s)")
                            st.rerun()
                    else:
                        st.caption("All visible creators are already assigned to this campaign.")

                if run_match:
                    with st.spinner("Running AI matching..."):
                        all_matches = []
                        for creator in pool:
                            all_matches.append({"creator": creator, "match": matcher.match(creator, campaign)})
                        all_matches.sort(key=lambda x: x["match"]["overall_score"], reverse=True)
                        st.session_state.match_results = all_matches[:30]
                        st.session_state.match_total = len(all_matches)
                    st.rerun()

                if st.session_state.get("match_results"):
                    top_matches = st.session_state.match_results
                    total_evaluated = st.session_state.match_total
                    st.markdown(f"**Match results** \u2014 {total_evaluated} evaluated, showing top {len(top_matches)}")

                    unassigned_in_results = [m for m in top_matches if not asvc.is_assigned(campaign.id, m["creator"].id)]
                    if unassigned_in_results:
                        if st.button(f"Assign all ({len(unassigned_in_results)} unassigned)", type="primary", icon=":material/select_all:", use_container_width=True):
                            for m in unassigned_in_results:
                                creator = m["creator"]
                                score = m["match"]["overall_score"]
                                if not asvc.is_assigned(campaign.id, creator.id):
                                    asvc.assign(campaign.id, creator.id, score=score)
                                    if creator.id not in campaign.assigned_creators:
                                        campaign.assigned_creators.append(creator.id)
                                        cams.repo.save_all(cams.campaigns)
                            st.success(f"Assigned {len(unassigned_in_results)} creators")
                            st.rerun()

                    for m in top_matches:
                        creator = m["creator"]
                        match = m["match"]
                        score = match["overall_score"]
                        assignment = asvc.get_for_campaign_creator(campaign.id, creator.id)
                        with st.container(border=True):
                            cols = st.columns([3, 1])
                            with cols[0]:
                                st.markdown(f"**{creator.name}**")
                                st.caption(f"{creator.primary_niche} \u00b7 {creator.primary_language} \u00b7 {creator.total_followers:,} followers")
                            with cols[1]:
                                color = "green" if score >= 8 else "orange" if score >= 6 else "red"
                                st.markdown(
                                    f'<div style="text-align:right">'
                                    f'<span style="font-size:1.3rem;font-weight:700;color:{color}">{score}/10</span><br>'
                                    f'<span style="font-size:0.75rem;color:{color}">{match.get("match_quality", "").title()}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                            if assignment:
                                sc = assignment.status
                                badge_color = STATUS_COLORS.get(sc.value, "#95A5A6")
                                label = STATUS_LABELS.get(sc, sc.value)
                                st.markdown(
                                    f'<span style="background:{badge_color}22;color:{badge_color};padding:2px 14px;'
                                    f'border-radius:10px;font-size:0.8rem;font-weight:600">{label}</span>'
                                    f' <span style="font-size:0.8rem;color:#6B7280;">(score: {assignment.score}/10)</span>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                if st.button("Assign", key=f"match_ass_{creator.id}", icon=":material/person_add:", type="primary", use_container_width=True):
                                    asvc.assign(campaign.id, creator.id, score=score)
                                    if creator.id not in campaign.assigned_creators:
                                        campaign.assigned_creators.append(creator.id)
                                        cams.repo.save_all(cams.campaigns)
                                    st.success(f"Assigned {creator.name}")
                                    st.rerun()
                            with st.expander("Match breakdown", icon=":material/insights:"):
                                for pt in match.get("alignment_points", []):
                                    st.markdown(f":material/check: {pt}")
                                sc1, sc2, sc3, sc4 = st.columns(4)
                                sc1.metric("Niche", f'{match.get("niche_overlap", 0)}/10')
                                sc2.metric("Language", f'{match.get("language_overlap", 0)}/10')
                                sc3.metric("Engagement", f'{match.get("engagement_score", 0)}/10')
                                sc4.metric("Quality", f'{match.get("quality_score", 0)}/10')
                                sc1.metric("Reach", f'{match.get("reach_score", 0)}/10')
                                sc2.metric("Budget fit", f'{match.get("budget_fit", 0)}/10')
                                if creator.total_campaigns_completed > 0:
                                    sc3.metric("Avg earnings/campaign", f"₹{creator.total_earnings / creator.total_campaigns_completed:,.0f}")

            st.divider()
            with st.expander("Campaign Settings", expanded=False):
                with st.container(border=True):
                    st.markdown("**Edit campaign**")
                    with st.form(f"edit_camp_{campaign.id}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            e_title = st.text_input("Title", value=campaign.title)
                            e_brand = st.text_input("Brand", value=campaign.brand)
                            e_budget = st.number_input("Budget (₹)", min_value=0.0, value=campaign.budget, step=5000.0)
                        with e2:
                            e_deadline = st.date_input("Deadline", value=pd.to_datetime(campaign.deadline).date() if campaign.deadline else None)
                            e_niches = st.multiselect("Target niches", get_all_niches(), default=[n for n in campaign.target_niches if n in get_all_niches()])
                            e_langs = st.multiselect("Target languages", LANGUAGES, default=campaign.target_languages)
                        e_desc = st.text_area("Description", value=campaign.description)
                        if st.form_submit_button("Save changes", type="primary", icon=":material/save:", use_container_width=True):
                            campaign.title = e_title
                            campaign.brand = e_brand
                            campaign.description = e_desc
                            campaign.budget = e_budget
                            campaign.deadline = e_deadline.isoformat() if e_deadline else campaign.deadline
                            campaign.target_niches = e_niches
                            campaign.target_languages = e_langs
                            cams.repo.save_all(cams.campaigns)
                            st.success("Campaign updated!")
                            st.rerun()

                st.markdown("**Danger zone**")
                if st.button("Delete this campaign", icon=":material/delete:", type="primary", use_container_width=True):
                    for a in asvc.get_for_campaign(campaign.id):
                        asvc.repo.delete(a.id)
                    asvc.refresh()
                    cams.delete(campaign.id)
                    st.rerun()

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in campaign_matching")