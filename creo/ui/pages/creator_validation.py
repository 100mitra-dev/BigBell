import streamlit as st
import pandas as pd

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.ui.components.cards import creator_avatar
from creo.models import CreatorStatus
from creo.agents.application_reviewer import ApplicationReviewerAgent
from creo.agents.verification_agent import VerificationAgent
from creo.agents.categorization_agent import CategorizationAgent
from creo.config import NICHES, LANGUAGES
from creo.utils.helpers import load_applications, save_applications, today_str

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
cs = st.session_state.cs
cams = st.session_state.cams

reviewer = ApplicationReviewerAgent()
verifier = VerificationAgent()
cat_agent = CategorizationAgent()

if "review_selected_creator" not in st.session_state:
    st.session_state.review_selected_creator = None

st.title("Review & Classify")
st.caption("Creator pipeline — review applications, verify authenticity, and classify profiles")

apps = load_applications()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Pending reviews", len([a for a in apps if a.status == "pending"]))
m2.metric("Needs verification", len(cs.filter_by_status("pending") + cs.filter_by_status("onboarding")))
m3.metric("Needs classification", len([c for c in cs.creators if not c.classified_at]))
m4.metric("Active creators", cs.get_active_count())

left, right = st.columns([1, 1.8])

# ═══════════════════════════════════════════════
# LEFT PANEL — Pipeline queue
# ═══════════════════════════════════════════════
with left:
    stage = st.segmented_control(
        "Pipeline stage", label_visibility="collapsed",
        options=["Needs Review", "Needs Verification", "Needs Classification", "All"],
        default="Needs Review",
    )

    sq = st.text_input("Search", placeholder="Search by name, email, or niche...", label_visibility="collapsed")

    # Build queue
    pool = cs.creators
    if sq:
        pool = cs.search(sq)

    pending_app_creator_ids = {a.creator_id for a in apps if a.status == "pending"}
    if stage == "Needs Review":
        pool = [c for c in pool if c.id in pending_app_creator_ids]
    elif stage == "Needs Verification":
        pool = [c for c in pool if c.status in (CreatorStatus.PENDING, CreatorStatus.ONBOARDING) and not c.verified]
    elif stage == "Needs Classification":
        pool = [c for c in pool if not c.classified_at]

    # Export
    if pool:
        export_rows = []
        for c in pool:
            c_apps = [a for a in apps if a.creator_id == c.id]
            export_rows.append({
                "Name": c.name, "Niche": c.primary_niche, "Language": c.primary_language,
                "Tier": c.tier, "Followers": c.total_followers,
                "Verified": "Yes" if c.verified else "No",
                "Classified": "Yes" if c.classified_at else "No",
                "Applications": len(c_apps),
            })
        csv_str = pd.DataFrame(export_rows).to_csv(index=False)
        st.download_button(
            "Export CSV", data=csv_str,
            file_name=f"pipeline_{stage.lower().replace(' ', '_')}.csv",
            mime="text/csv", use_container_width=True, icon=":material/file_download:",
        )

    st.caption(f"{len(pool)} creator(s)")

    for creator in pool:
        c_apps = [a for a in apps if a.creator_id == creator.id]
        has_pending = any(a.status == "pending" for a in c_apps)
        needs_verify = creator.status in (CreatorStatus.PENDING, CreatorStatus.ONBOARDING) and not creator.verified
        needs_classify = not creator.classified_at

        # Status badges
        badges = []
        if has_pending:
            badges.append(f":material/rate_review: Review")
        if needs_verify:
            badges.append(f":material/verified: Verify")
        if needs_classify:
            badges.append(f":material/category: Classify")
        if creator.verified and creator.classified_at:
            badges.append(f":material/check_circle: Complete")

        selected = st.session_state.review_selected_creator == creator.id
        border_color = "#1E88E5" if selected else None

        with st.container(border=True):
            if selected:
                st.markdown(f"<div style='border-left:3px solid #1E88E5;padding-left:8px;'>", unsafe_allow_html=True)

            cr1, cr2 = st.columns([1, 2])
            with cr1:
                creator_avatar(creator.name, size=48)
            with cr2:
                st.markdown(f"**{creator.name}**")
                st.caption(f"{creator.primary_niche} · {creator.tier}")
                if badges:
                    st.markdown(" ".join(badges[:2]))

            if st.button("Open", key=f"sel_{creator.id}", use_container_width=True, icon=":material/open_in_new:", type="secondary" if not selected else "primary"):
                st.session_state.review_selected_creator = creator.id
                st.rerun()

# ═══════════════════════════════════════════════
# RIGHT PANEL — Creator detail
# ═══════════════════════════════════════════════
with right:
    selected_id = st.session_state.review_selected_creator
    creator = cs.get_by_id(selected_id) if selected_id else None

    if not creator:
        st.info("Select a creator from the pipeline to view details.", icon=":material/touch_app:")
        st.stop()

    # Profile header
    ph1, ph2 = st.columns([1, 3])
    with ph1:
        creator_avatar(creator.name, size=80)
    with ph2:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(f"**{creator.name}**")
            st.markdown(f"{creator.primary_niche} · {creator.primary_language} · {creator.tier}")
            cols = st.columns(4)
            cols[0].metric("Followers", f"{creator.total_followers:,}")
            cols[1].metric("Engagement", f"{creator.avg_engagement_rate}%")
            cols[2].metric("Quality", f"{creator.content_quality_score}/10")
            cols[3].metric("Completeness", f"{creator.profile_completeness}%")
            if creator.suggested_tags:
                st.markdown(" ".join(f":material/tag: `{t}`" for t in creator.suggested_tags))
        with col_b:
            st.markdown(f"**Status:**")
            st.badge(creator.status.value)

    detail_tab = st.tabs(["Applications", "Verification", "Classification"])

    # ── TAB: APPLICATIONS ──
    with detail_tab[0]:
        creator_apps = [a for a in apps if a.creator_id == creator.id]
        if not creator_apps:
            st.info("No applications from this creator.", icon=":material/inbox:")
        else:
            for app in creator_apps:
                campaign = cams.get_by_id(app.campaign_id)
                camp_label = f"{campaign.title} ({campaign.brand})" if campaign else "Unknown"

                with st.container(border=True):
                    row = st.columns([2, 1, 1, 1])
                    with row[0]:
                        st.markdown(f"**{camp_label}**")
                        st.caption(f"Applied: {app.applied_at}")
                    with row[1]:
                        st.badge(app.status)
                    if app.score:
                        with row[2]:
                            st.metric("Score", f"{app.score}/10")

                    rk = f"rr_{app.id}"
                    if app.status == "pending":
                        with row[3]:
                            if st.button("AI review", key=f"b_{app.id}", icon=":material/rate_review:", type="primary", use_container_width=True):
                                with st.spinner("Reviewing..."):
                                    r = reviewer.review(creator, campaign)
                                    app.score = r["score"]
                                    app.ai_notes = r["feedback"]
                                    app.reviewed_at = today_str()
                                    if r.get("recommendation") == "accept":
                                        app.status = "shortlisted"
                                    elif r.get("recommendation") == "reject":
                                        app.status = "rejected"
                                    else:
                                        app.status = "reviewed"
                                    save_applications(apps)
                                    st.session_state[rk] = r
                                st.rerun()
                    else:
                        with row[3]:
                            if st.button("Re-review", key=f"b_{app.id}", icon=":material/refresh:", use_container_width=True):
                                with st.spinner("Re-reviewing..."):
                                    r = reviewer.review(creator, campaign)
                                    app.score = r["score"]
                                    app.ai_notes = r["feedback"]
                                    app.reviewed_at = today_str()
                                    save_applications(apps)
                                    st.session_state[rk] = r
                                st.rerun()

                    result = st.session_state.get(rk)
                    if result:
                        sc = st.columns(4)
                        sc[0].metric("Niche", f'{result.get("niche_alignment", "N/A")}/10')
                        sc[1].metric("Quality", f'{result.get("quality_score", "N/A")}/10')
                        sc[2].metric("Engagement", f'{result.get("engagement_score", "N/A")}/10')
                        sc[3].metric("Language", f'{result.get("language_match", "N/A")}/10')

                        if result.get("risks"):
                            with st.expander("Risks", icon=":material/warning:"):
                                for r2 in result["risks"]:
                                    st.warning(r2)

                        rec = result.get("recommendation", "")
                        msg = result.get("feedback", "")
                        if rec == "accept":
                            st.success(f":material/check_circle: **Accept** — {msg}")
                        elif rec == "shortlist":
                            st.warning(f":material/format_list_bulleted: **Shortlist** — {msg}")
                        else:
                            st.error(f":material/block: **Reject** — {msg}")

    # ── TAB: VERIFICATION ──
    with detail_tab[1]:
        vk = f"vr_{creator.id}"
        vrow1 = st.columns([1, 1, 1])

        with vrow1[0]:
            if creator.verified:
                st.success(f":material/check_circle: Verified ({creator.verification_score:.0f}/100)")
            else:
                st.warning(":material/cancel: Not verified")

        with vrow1[1]:
            btn_icon = ":material/verified:" if not creator.verified else ":material/refresh:"
            if st.button("Run verification", key=f"v_{creator.id}", icon=btn_icon, use_container_width=True):
                with st.spinner(f"Verifying {creator.name}..."):
                    st.session_state[vk] = verifier.verify(creator)
                st.rerun()

        with vrow1[2]:
            if not creator.verified and st.session_state.get(vk, {}).get("verified"):
                if st.button("Approve & activate", key=f"ap_{creator.id}", icon=":material/check:", type="primary", use_container_width=True):
                    creator.verified = True
                    creator.verification_score = st.session_state[vk].get("overall_score", 0)
                    creator.verification_issues = st.session_state[vk].get("issues", [])
                    creator.verified_at = today_str()
                    cs.update_status(creator.id, CreatorStatus.ACTIVE)
                    cs.repo.save_all(cs.creators)
                    st.success(f"{creator.name} approved and activated")
                    st.rerun()

        vresult = st.session_state.get(vk)
        if vresult:
            vc1, vc2 = st.columns(2)
            with vc1:
                st.metric("Overall score", f'{vresult.get("overall_score", 0)}/100')
            with vc2:
                for issue in vresult.get("issues", []):
                    st.warning(issue)

            cq = vresult.get("content_quality")
            if cq:
                st.markdown("**Content quality breakdown**")
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Quality", f'{cq.get("score", 0)}/10')
                cc2.metric("Consistency", f'{cq.get("consistency", 0)}/10')
                cc3.metric("Originality", f'{cq.get("originality", 0)}/10')

            if vresult.get("platforms"):
                with st.expander("Platform details", icon=":material/account_circle:"):
                    for plat, pdata in vresult["platforms"].items():
                        st.write(f"**{plat.title()}**")
                        st.json(pdata)

    # ── TAB: CLASSIFICATION ──
    with detail_tab[2]:
        ck = f"cr_{creator.id}"

        ctop = st.columns([1, 1])
        with ctop[0]:
            if creator.classified_at:
                st.success(f":material/check_circle: Classified ({creator.classified_at})")
            else:
                st.warning(":material/cancel: Not classified yet")
        with ctop[1]:
            if st.button("Run AI classification", key=f"c_{creator.id}", icon=":material/category:", use_container_width=True):
                with st.spinner("Analysing..."):
                    st.session_state[ck] = cat_agent.categorize(creator)
                st.rerun()

        cres = st.session_state.get(ck)
        if cres:
            st.success("AI classification complete")

            nr1, nr2 = st.columns(2)
            with nr1:
                st.markdown("**Niche scores**")
                st.bar_chart(
                    pd.DataFrame(list(cres["niche_scores"].items()), columns=["Niche", "Score"]),
                    x="Niche", y="Score", horizontal=True,
                )
            with nr2:
                st.markdown("**Language scores**")
                st.bar_chart(
                    pd.DataFrame(list(cres["language_scores"].items()), columns=["Language", "Score"]),
                    x="Language", y="Score", horizontal=True,
                )

            ca, cb, cc = st.columns(3)
            ca.metric("Primary niche", cres["primary_niche"])
            cb.metric("Primary language", cres["primary_language"])
            cc.metric("Tier", cres["tier"])
            st.markdown("**Suggested tags:** " + " ".join(f":material/tag: `{t}`" for t in cres["suggested_tags"]))

            st.divider()
            st.markdown("**Manual overrides**")
            ov1, ov2 = st.columns(2)
            with ov1:
                over_niche = st.selectbox("Primary niche", NICHES, index=NICHES.index(cres["primary_niche"]) if cres["primary_niche"] in NICHES else 0, key=f"on_{creator.id}")
                over_lang = st.selectbox("Primary language", LANGUAGES, index=LANGUAGES.index(cres["primary_language"]) if cres["primary_language"] in LANGUAGES else 0, key=f"ol_{creator.id}")
            with ov2:
                over_tags = st.text_input("Tags (comma-separated)", value=", ".join(cres["suggested_tags"]), key=f"ot_{creator.id}")

            if st.button("Save classification", key=f"sv_{creator.id}", type="primary", icon=":material/save:", use_container_width=True):
                creator.primary_niche = over_niche
                creator.primary_language = over_lang
                creator.suggested_tags = [t.strip() for t in over_tags.split(",") if t.strip()]
                creator.classified_at = today_str()
                cs.repo.save_all(cs.creators)
                st.success(f"Classification saved for {creator.name}")
                st.rerun()

        elif creator.classified_at:
            st.info("Already classified. Re-run AI or edit overrides below.")
            ov1, ov2 = st.columns(2)
            with ov1:
                over_niche = st.selectbox("Primary niche", NICHES, index=NICHES.index(creator.primary_niche) if creator.primary_niche in NICHES else 0, key=f"on_{creator.id}")
                over_lang = st.selectbox("Primary language", LANGUAGES, index=LANGUAGES.index(creator.primary_language) if creator.primary_language in LANGUAGES else 0, key=f"ol_{creator.id}")
            with ov2:
                over_tags = st.text_input("Tags (comma-separated)", value=", ".join(creator.suggested_tags) if creator.suggested_tags else "", key=f"ot_{creator.id}")
            if st.button("Save overrides", key=f"sv_{creator.id}", type="primary", icon=":material/save:", use_container_width=True):
                creator.primary_niche = over_niche
                creator.primary_language = over_lang
                creator.suggested_tags = [t.strip() for t in over_tags.split(",") if t.strip()]
                creator.classified_at = today_str()
                cs.repo.save_all(cs.creators)
                st.success(f"Overrides saved for {creator.name}")
                st.rerun()
