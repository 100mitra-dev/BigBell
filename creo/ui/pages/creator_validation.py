import logging

import pandas as pd
import streamlit as st

from creo.agents.application_reviewer import ApplicationReviewerAgent
from creo.agents.categorization import CategorizationAgent
from creo.agents.verification import VerificationAgent
from creo.config import LANGUAGES, get_all_niches
from creo.models import CreatorStatus
from creo.services.campaign_service import CampaignService
from creo.services.creator_service import CreatorService
from creo.ui.components.cards import creator_avatar
from creo.ui.components.platforms import platform_link_markdown, render_platform_grid
from creo.utils.dates import today_str
from creo.utils.json_io import load_applications, save_applications

logger = logging.getLogger(__name__)

STAGE_OPTIONS = ["Needs review", "Needs verification", "Needs classification", "All"]
STAGE_KEYS = {
    "Needs review": "review",
    "Needs verification": "verify",
    "Needs classification": "classify",
    "All": "all",
}

STATUS_BADGES = {
    CreatorStatus.PENDING: ("orange", ":material/schedule:"),
    CreatorStatus.ONBOARDING: ("blue", ":material/person_add:"),
    CreatorStatus.ACTIVE: ("green", ":material/check_circle:"),
    CreatorStatus.INACTIVE: ("gray", ":material/pause_circle:"),
    CreatorStatus.REJECTED: ("red", ":material/block:"),
}

APP_STATUS_COLORS = {
    "pending": "orange",
    "reviewed": "blue",
    "shortlisted": "violet",
    "rejected": "red",
    "accepted": "green",
}


def pipeline_badges(creator, apps) -> str:
    has_pending = any(a.status == "pending" for a in apps if a.creator_id == creator.id)
    needs_verify = creator.status in (CreatorStatus.PENDING, CreatorStatus.ONBOARDING) and not creator.verified
    needs_classify = not creator.classified_at
    badges = []
    if has_pending:
        badges.append(":orange-badge[Awaiting review]")
    if needs_verify:
        badges.append(":blue-badge[Needs verification]")
    if needs_classify:
        badges.append(":violet-badge[Needs classification]")
    if creator.verified and creator.classified_at:
        badges.append(":green-badge[Complete]")
    return " ".join(badges)


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

try:
    apps = load_applications()

    st.title("Review & classify")
    st.caption("Creator onboarding pipeline \u2014 review applications, verify authenticity, and classify profiles.")

    with st.container(horizontal=True):
        st.metric("Pending reviews", len([a for a in apps if a.status == "pending"]), border=True)
        st.metric(
            "Awaiting verification",
            len(cs.filter_by_status("pending") + cs.filter_by_status("onboarding")),
            border=True,
        )
        st.metric("Awaiting classification", len([c for c in cs.creators if not c.classified_at]), border=True)
        st.metric("Active creators", cs.get_active_count(), border=True)

    stage_label = st.segmented_control(
        "Pipeline stage",
        options=STAGE_OPTIONS,
        default="Needs review",
        label_visibility="collapsed",
        width="stretch",
    )
    stage = STAGE_KEYS[stage_label]

    queue_col, detail_col = st.columns([1, 1.9], gap="large")

    # ═══════════════════════════════════════════════
    # QUEUE PANEL
    # ═══════════════════════════════════════════════
    with queue_col:
        sq = st.text_input(
            "Search creators",
            placeholder="Name, email or niche",
            label_visibility="collapsed",
            icon=":material/search:",
        )

        pool = cs.search(sq) if sq else cs.creators
        pending_app_creator_ids = {a.creator_id for a in apps if a.status == "pending"}
        if stage == "review":
            pool = [c for c in pool if c.id in pending_app_creator_ids]
        elif stage == "verify":
            pool = [
                c for c in pool
                if c.status in (CreatorStatus.PENDING, CreatorStatus.ONBOARDING) and not c.verified
            ]
        elif stage == "classify":
            pool = [c for c in pool if not c.classified_at]

        with st.container(border=True):
            qh1, qh2 = st.columns([1.8, 1], vertical_alignment="center")
            with qh1:
                st.markdown("**Pipeline queue**")
            with qh2:
                if pool:
                    export_rows = []
                    for c in pool:
                        export_rows.append({
                            "Name": c.name, "Niche": c.primary_niche, "Language": c.primary_language,
                            "Tier": c.tier, "Followers": c.total_followers,
                            "Verified": "Yes" if c.verified else "No",
                            "Classified": "Yes" if c.classified_at else "No",
                            "Applications": len([a for a in apps if a.creator_id == c.id]),
                        })
                    st.download_button(
                        "Export",
                        data=pd.DataFrame(export_rows).to_csv(index=False),
                        file_name=f"pipeline_{stage}.csv",
                        mime="text/csv",
                        icon=":material/file_download:",
                        width="stretch",
                    )
            st.caption(f"{len(pool)} creator(s) \u00b7 {stage_label}")

            if not pool:
                st.caption("No creators match this stage.")

            for creator in pool:
                selected = st.session_state.review_selected_creator == creator.id
                with st.container(border=True):
                    h1, h2 = st.columns([2.6, 1.4], vertical_alignment="center")
                    with h1:
                        ic, tx = st.columns([1, 3.2], vertical_alignment="center")
                        with ic:
                            creator_avatar(creator.name, size=46)
                        with tx:
                            st.markdown(f"**{creator.name}**")
                            st.caption(f"{creator.primary_niche} \u00b7 {creator.primary_language}")
                    with h2:
                        if selected:
                            st.button(
                                "Viewing",
                                key=f"sel_{creator.id}",
                                icon=":material/visibility:",
                                type="primary",
                                width="stretch",
                                disabled=True,
                            )
                        elif st.button(
                            "Review",
                            key=f"sel_{creator.id}",
                            icon=":material/open_in_new:",
                            width="stretch",
                        ):
                            st.session_state.review_selected_creator = creator.id
                            st.rerun()
                    st.markdown(pipeline_badges(creator, apps))
                    st.caption(
                        f":material/group: {creator.total_followers:,} followers  \u00b7  "
                        f":material/trending_up: {creator.avg_engagement_rate}% engagement  \u00b7  "
                        f":material/workspace_premium: {creator.tier}"
                    )

    # ═══════════════════════════════════════════════
    # DETAIL PANEL
    # ═══════════════════════════════════════════════
    with detail_col:
        selected_id = st.session_state.review_selected_creator
        creator = cs.get_by_id(selected_id) if selected_id else None

        if not creator:
            with st.container(border=True):
                st.info("Select a creator from the queue to review their profile.", icon=":material/touch_app:")
            st.stop()

        with st.container(border=True):
            hc1, hc2 = st.columns([1, 4], vertical_alignment="center")
            with hc1:
                creator_avatar(creator.name, size=80)
            with hc2:
                st.markdown(f"### {creator.name}")
                st.markdown(
                    f"{creator.primary_niche} \u00b7 {creator.primary_language} \u00b7 "
                    f":material/workspace_premium: {creator.tier}"
                )
                st.caption(
                    f":material/verified: {'Verified' if creator.verified else 'Not verified'}  \u00b7  "
                    f":material/category: {'Classified' if creator.classified_at else 'Not classified'}"
                )
            sc = st.columns(4)
            sc[0].metric("Followers", f"{creator.total_followers:,}", border=True)
            sc[1].metric("Engagement", f"{creator.avg_engagement_rate}%", border=True)
            sc[2].metric("Content quality", f"{creator.content_quality_score}/10", border=True)
            sc[3].metric("Profile completeness", f"{creator.profile_completeness}%", border=True)
            if creator.suggested_tags:
                st.markdown(" ".join(f":material/sell: `{t}`" for t in creator.suggested_tags))

            if creator.platforms:
                st.markdown("**:material/account_circle: Social profiles**")
                render_platform_grid(creator.platforms)

        status_color, status_icon = STATUS_BADGES.get(creator.status, ("gray", ":material/circle:"))
        st.badge(
            creator.status.value,
            icon=status_icon,
            color=status_color,
            help="Current pipeline status",
        )

        detail_tabs = st.tabs([
            ":material/rate_review: Applications",
            ":material/verified: Verification",
            ":material/category: Classification",
        ])

        # ── APPLICATIONS ──
        with detail_tabs[0]:
            creator_apps = [a for a in apps if a.creator_id == creator.id]
            if not creator_apps:
                st.caption("No applications from this creator yet.")
            for app in creator_apps:
                campaign = cams.get_by_id(app.campaign_id)
                camp_label = f"{campaign.title} \u00b7 {campaign.brand}" if campaign else "Unknown campaign"
                rk = f"rr_{app.id}"

                with st.container(border=True):
                    a1, a2 = st.columns([3, 1], vertical_alignment="center")
                    with a1:
                        st.markdown(f"**{camp_label}**")
                        st.caption(f"Applied {app.applied_at}" + (f" \u00b7 Score {app.score}/10" if app.score else ""))
                    with a2:
                        st.badge(app.status, color=APP_STATUS_COLORS.get(app.status, "gray"))

                    if campaign:
                        if app.status == "pending":
                            review_clicked = st.button(
                                "Run AI review",
                                key=f"b_{app.id}",
                                icon=":material/rate_review:",
                                type="primary",
                                width="stretch",
                            )
                        else:
                            review_clicked = st.button(
                                "Re-review",
                                key=f"b_{app.id}",
                                icon=":material/refresh:",
                                width="stretch",
                            )
                        if review_clicked:
                            with st.spinner(f"Reviewing {creator.name} for {campaign.title}..."):
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
                        st.caption("Campaign record unavailable \u2014 manual review not possible.")

                    result = st.session_state.get(rk)
                    if result:
                        rec = result.get("recommendation", "")
                        msg = result.get("feedback", "")
                        if rec == "accept":
                            st.success(f":material/check_circle: **Accept** \u2014 {msg}")
                        elif rec == "shortlist":
                            st.warning(f":material/format_list_bulleted: **Shortlist** \u2014 {msg}")
                        else:
                            st.error(f":material/block: **Reject** \u2014 {msg}")

                        sc = st.columns(4)
                        sc[0].metric("Niche alignment", f'{result.get("niche_alignment", "N/A")}/10')
                        sc[1].metric("Quality", f'{result.get("quality_score", "N/A")}/10')
                        sc[2].metric("Engagement", f'{result.get("engagement_score", "N/A")}/10')
                        sc[3].metric("Language", f'{result.get("language_match", "N/A")}/10')

                        if result.get("risks"):
                            with st.expander("Risks", icon=":material/warning:"):
                                for r2 in result["risks"]:
                                    st.markdown(f":orange[\u2022 {r2}]")

        # ── VERIFICATION ──
        with detail_tabs[1]:
            vk = f"vr_{creator.id}"
            vresult = st.session_state.get(vk)

            v_top = st.columns([2, 1.4], vertical_alignment="center")
            with v_top[0]:
                if creator.verified:
                    st.markdown(f":material/verified: **Verified** \u00b7 {creator.verification_score:.0f}/100")
                    st.caption(f"Verified {creator.verified_at or 'via manual override'}")
                else:
                    st.markdown(":material/pending: **Not verified yet**")
                    st.caption("Run verification to assess profile authenticity.")
            with v_top[1]:
                if st.button(
                    "Run verification",
                    key=f"v_{creator.id}",
                    icon=":material/verified:",
                    width="stretch",
                ):
                    with st.spinner(f"Verifying {creator.name}..."):
                        st.session_state[vk] = verifier.verify(creator)
                    st.rerun()

            if vresult:
                vc = st.columns([1, 2])
                with vc[0]:
                    st.metric("Overall score", f'{vresult.get("overall_score", 0)}/100', border=True)
                with vc[1]:
                    issues = vresult.get("issues", [])
                    if issues:
                        st.markdown("**Flagged issues**")
                        for issue in issues:
                            st.markdown(f":material/warning: {issue}")

                cq = vresult.get("content_quality")
                if cq:
                    st.markdown("**Content quality breakdown**")
                    cq1, cq2, cq3 = st.columns(3)
                    cq1.metric("Quality", f'{cq.get("score", 0)}/10', border=True)
                    cq2.metric("Consistency", f'{cq.get("consistency", 0)}/10', border=True)
                    cq3.metric("Originality", f'{cq.get("originality", 0)}/10', border=True)

                if vresult.get("platforms"):
                    with st.expander("Platform details", icon=":material/account_circle:"):
                        for plat, pdata in vresult["platforms"].items():
                            st.markdown(
                                platform_link_markdown(
                                    plat,
                                    pdata.get("handle", ""),
                                    pdata.get("followers", 0),
                                )
                            )
                            st.json(pdata)

                if vresult.get("verified"):
                    label = "Update & approve" if creator.verified else "Approve & activate"
                    if st.button(
                        label,
                        key=f"ap_{creator.id}",
                        icon=":material/check:",
                        type="primary",
                        width="stretch",
                    ):
                        creator.verified = True
                        creator.verification_score = vresult.get("overall_score", 0)
                        creator.verification_issues = vresult.get("issues", [])
                        creator.verified_at = today_str()
                        cs.update_status(creator.id, CreatorStatus.ACTIVE)
                        cs.repo.save_all(cs.creators)
                        st.success(f"{creator.name} approved and activated")
                        st.rerun()

            with st.container(border=True):
                st.markdown("**Manual override**")
                st.caption("Set verification values directly instead of using the AI result.")
                m1, m2 = st.columns(2)
                with m1:
                    manual_score = st.number_input(
                        "Verification score",
                        min_value=0,
                        max_value=100,
                        value=int(creator.verification_score) or 75,
                        key=f"vs_{creator.id}",
                    )
                    manual_verified = st.radio(
                        "Verification decision",
                        options=["Not verified", "Verified"],
                        index=0 if not creator.verified else 1,
                        horizontal=True,
                        key=f"vchk_{creator.id}",
                    )
                with m2:
                    manual_issues = st.text_area(
                        "Issues (one per line)",
                        value="\n".join(creator.verification_issues) if creator.verification_issues else "",
                        key=f"vi_{creator.id}",
                    )
                if st.button(
                    "Apply override",
                    key=f"vo_{creator.id}",
                    icon=":material/edit:",
                    width="stretch",
                ):
                    creator.verified = manual_verified == "Verified"
                    creator.verification_score = float(manual_score)
                    creator.verification_issues = [l.strip() for l in manual_issues.split("\n") if l.strip()]
                    creator.verified_at = today_str()
                    if creator.verified:
                        cs.update_status(creator.id, CreatorStatus.ACTIVE)
                    cs.repo.save_all(cs.creators)
                    st.success(f"Verification override applied for {creator.name}")
                    st.rerun()

        # ── CLASSIFICATION ──
        with detail_tabs[2]:
            ck = f"cr_{creator.id}"
            cres = st.session_state.get(ck)

            c_top = st.columns([2, 1.4], vertical_alignment="center")
            with c_top[0]:
                if creator.classified_at:
                    st.markdown(":material/check_circle: **Classified**")
                    st.caption(f"Classified {creator.classified_at}")
                else:
                    st.markdown(":material/category: **Awaiting classification**")
                    st.caption("Run classification to suggest niche, language and tier.")
            with c_top[1]:
                if st.button(
                    "Run AI classification",
                    key=f"c_{creator.id}",
                    icon=":material/category:",
                    type="primary",
                    width="stretch",
                ):
                    with st.spinner("Analysing..."):
                        st.session_state[ck] = cat_agent.categorize(creator)
                    st.rerun()

            if cres:
                st.success("AI classification complete")

                n1, n2 = st.columns(2)
                with n1:
                    st.markdown("**Niche scores**")
                    st.bar_chart(
                        pd.DataFrame(list(cres["niche_scores"].items()), columns=["Niche", "Score"]),
                        x="Niche",
                        y="Score",
                        horizontal=True,
                    )
                with n2:
                    st.markdown("**Language scores**")
                    st.bar_chart(
                        pd.DataFrame(list(cres["language_scores"].items()), columns=["Language", "Score"]),
                        x="Language",
                        y="Score",
                        horizontal=True,
                    )

                ca, cb, cc = st.columns(3)
                ca.metric("Primary niche", cres["primary_niche"], border=True)
                cb.metric("Primary language", cres["primary_language"], border=True)
                cc.metric("Tier", cres["tier"], border=True)
                st.markdown(
                    "**Suggested tags:** "
                    + " ".join(f":material/sell: `{t}`" for t in cres["suggested_tags"])
                )

            default_niche = (cres or {}).get("primary_niche") or creator.primary_niche
            default_lang = (cres or {}).get("primary_language") or creator.primary_language
            default_tags = (cres or {}).get("suggested_tags") or creator.suggested_tags

            with st.container(border=True):
                if cres:
                    override_heading = "Apply classification"
                elif creator.classified_at:
                    override_heading = "Classification overrides"
                else:
                    override_heading = "Manual classification"
                st.markdown(f"**{override_heading}**")
                st.caption("Review the suggested values and save to finalize classification, or set them manually.")
                ov1, ov2 = st.columns(2)
                with ov1:
                    over_niche = st.selectbox(
                        "Primary niche",
                        get_all_niches(),
                        index=get_all_niches().index(default_niche) if default_niche in get_all_niches() else 0,
                        key=f"on_{creator.id}",
                    )
                    over_lang = st.selectbox(
                        "Primary language",
                        LANGUAGES,
                        index=LANGUAGES.index(default_lang) if default_lang in LANGUAGES else 0,
                        key=f"ol_{creator.id}",
                    )
                with ov2:
                    over_tags = st.text_input(
                        "Tags (comma-separated)",
                        value=", ".join(default_tags) if default_tags else "",
                        key=f"ot_{creator.id}",
                    )
                save_label = "Save classification" if (cres or not creator.classified_at) else "Save overrides"
                if st.button(
                    save_label,
                    key=f"sv_{creator.id}",
                    type="primary",
                    icon=":material/save:",
                    width="stretch",
                ):
                    creator.primary_niche = over_niche
                    creator.primary_language = over_lang
                    creator.suggested_tags = [t.strip() for t in over_tags.split(",") if t.strip()]
                    creator.classified_at = today_str()
                    cs.repo.save_all(cs.creators)
                    st.success(f"Classification saved for {creator.name}")
                    st.rerun()

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in creator_validation")
