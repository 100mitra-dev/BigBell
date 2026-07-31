import streamlit as st
import pandas as pd
from collections import Counter
from datetime import date, timedelta

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.services.payment_service import PaymentService
from creo.utils.json_io import load_applications
import logging

logger = logging.getLogger(__name__)

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
if "ps" not in st.session_state:
    st.session_state.ps = PaymentService()

cs = st.session_state.cs
cams = st.session_state.cams
ps = st.session_state.ps

CREATORS_PAGE = "creo/ui/pages/creators.py"
REVIEW_PAGE = "creo/ui/pages/creator_validation.py"
MATCHING_PAGE = "creo/ui/pages/campaigns.py"
DEADLINES_PAGE = "creo/ui/pages/deadlines.py"
PAYMENTS_PAGE = "creo/ui/pages/payments.py"

STATUS_ORDER = ["pending", "onboarding", "active", "inactive", "rejected"]
STATUS_LABELS = {
    "pending": "Pending",
    "onboarding": "Onboarding",
    "active": "Active",
    "inactive": "Inactive",
    "rejected": "Rejected",
}
PAYMENT_ORDER = ["pending", "processed", "paid", "disputed"]


try:
    creators = cs.creators
    campaigns = cams.campaigns
    payments = ps.payments
    applications = load_applications()

    status_counts = Counter(c.status.value for c in creators)
    paid_amount = sum(p.amount for p in payments if p.status == "paid")
    pending_amount = sum(p.amount for p in payments if p.status == "pending")
    total_budget = sum(c.budget for c in campaigns)

    today = date.today()
    deadline_window = (today + timedelta(days=14)).isoformat()
    upcoming_deadlines = sum(
        1 for c in campaigns
        if c.status == "active" and c.deadline and today.isoformat() <= c.deadline <= deadline_window
    )

    apps_needing_review = sum(1 for a in applications if a.status in ("pending", "reviewed"))

    st.title("Dashboard")
    st.caption("Real-time overview of creators, campaigns, payments, and your review pipeline.")

    st.markdown("#### Overview")
    kpi_cols = st.columns(4, border=True)
    with kpi_cols[0]:
        st.metric(
            "Total creators",
            len(creators),
            delta=f"{status_counts.get('active', 0)} active",
            help="All creators in your network.",
        )
        st.page_link(CREATORS_PAGE, label="All creators", icon=":material/group:", width="content")
    with kpi_cols[1]:
        st.metric(
            "Active campaigns",
            cams.get_active_count(),
            delta=f"₹{total_budget:,.0f} committed",
            help="Live campaigns and total committed budget.",
        )
        st.page_link(MATCHING_PAGE, label="Match creators", icon=":material/target:", width="content")
    with kpi_cols[2]:
        st.metric(
            "Pending reviews",
            status_counts.get("pending", 0) + status_counts.get("onboarding", 0),
            delta=f"{status_counts.get('onboarding', 0)} onboarding",
            help="Creators waiting for review, verification, or classification.",
        )
        st.page_link(REVIEW_PAGE, label="Review & classify", icon=":material/verified:", width="content")
    with kpi_cols[3]:
        st.metric(
            "Total paid out",
            f"₹{paid_amount:,.0f}",
            delta=f"₹{pending_amount:,.0f} pending",
            delta_color="inverse",
            help="Total money already paid to creators, with pending payouts as delta.",
        )
        st.page_link(PAYMENTS_PAGE, label="Manage payments", icon=":material/payments:", width="content")

    st.markdown("#### Needs attention")
    att_cols = st.columns(4, border=True)
    with att_cols[0]:
        st.metric("Applications to review", apps_needing_review, help="Applications not yet accepted or rejected.")
        st.page_link(REVIEW_PAGE, label="Review applications", icon=":material/rate_review:", width="content")
    with att_cols[1]:
        accepted_app_ids = {a.creator_id for a in applications if a.status == "accepted"}
        awaiting_verify = sum(1 for c in creators if c.id in accepted_app_ids and not c.verified)
        st.metric("Creators awaiting verification", awaiting_verify, help="Accepted creators waiting for AI verification.")
        st.page_link(REVIEW_PAGE, label="Verify creators", icon=":material/verified:", width="content")
    with att_cols[2]:
        st.metric("Deadlines in next 14 days", upcoming_deadlines, help="Active campaigns ending soon.")
        st.page_link(DEADLINES_PAGE, label="Upcoming deadlines", icon=":material/calendar_clock:", width="content")
    with att_cols[3]:
        st.metric("Pending payouts", ps.get_pending_count(), help="Payments scheduled but not yet paid.")
        st.page_link(PAYMENTS_PAGE, label="Process payouts", icon=":material/payments:", width="content")

    st.markdown("#### Insights")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader(":material/group: Creator status")
            status_df = pd.DataFrame({
                "Status": [STATUS_LABELS[s] for s in STATUS_ORDER],
                "Count": [status_counts.get(s, 0) for s in STATUS_ORDER],
            })
            if status_df["Count"].sum():
                st.bar_chart(status_df, x="Status", y="Count", color="Status", horizontal=True)
            else:
                st.info("No creators yet.")

    with col2:
        with st.container(border=True):
            st.subheader(":material/travel_explore: Top niches")
            niche_dist = cs.get_niche_distribution()
            if niche_dist:
                niche_df = pd.DataFrame(list(niche_dist.items()), columns=["Niche", "Creators"])
                niche_df = niche_df.sort_values("Creators", ascending=False).head(8)
                st.bar_chart(niche_df, x="Niche", y="Creators", color="Niche", horizontal=True)
            else:
                st.info("No creator data yet.")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader(":material/payments: Payment amounts by status")
            pay_amounts = {
                STATUS_LABELS.get(s, s.title()): sum(p.amount for p in payments if p.status == s)
                for s in PAYMENT_ORDER
            }
            pay_df = pd.DataFrame(
                [{"Status": k, "Amount": v} for k, v in pay_amounts.items() if v]
            )
            if not pay_df.empty:
                st.bar_chart(pay_df, x="Status", y="Amount", color="Status", horizontal=True)
            else:
                st.info("No payments yet.")

    with col2:
        with st.container(border=True):
            st.subheader(":material/campaign: Top campaigns by budget")
            active = [c for c in campaigns if c.status == "active"]
            if active:
                top = sorted(active, key=lambda c: c.budget, reverse=True)[:6]
                camp_df = pd.DataFrame({
                    "Campaign": [c.title[:28] + ("…" if len(c.title) > 28 else "") for c in top],
                    "Budget": [c.budget for c in top],
                    "Brand": [c.brand for c in top],
                })
                st.bar_chart(camp_df, x="Campaign", y="Budget", color="Brand", horizontal=True)
            else:
                st.info("No active campaigns.")

    st.markdown("#### Latest activity")

    creators_tab, campaigns_tab, payments_tab = st.tabs(
        [":material/person: Recent creators", ":material/campaign: Active campaigns", ":material/payments: Payments"]
    )

    with creators_tab:
        recent = sorted(creators, key=lambda c: c.id, reverse=True)[:6]
        if recent:
            creator_df = pd.DataFrame({
                "Creator": [c.name for c in recent],
                "Niche": [c.primary_niche for c in recent],
                "Language": [c.primary_language for c in recent],
                "Tier": [c.tier for c in recent],
                "Followers": [c.total_followers for c in recent],
                "Engagement": [c.avg_engagement_rate for c in recent],
                "Status": [c.status.value for c in recent],
            })
            st.dataframe(
                creator_df,
                hide_index=True,
                column_config={
                    "Followers": st.column_config.NumberColumn("Followers", format="%d"),
                    "Engagement": st.column_config.NumberColumn("Engagement %", format="%.1f%%"),
                },
            )
        else:
            st.info("No creators yet.")
        st.page_link(CREATORS_PAGE, label="View all creators", icon=":material/arrow_forward:", width="content")

    with campaigns_tab:
        active = sorted(active, key=lambda c: c.budget, reverse=True)[:6]
        if active:
            active_camp_df = pd.DataFrame({
                "Campaign": [c.title for c in active],
                "Brand": [c.brand for c in active],
                "Budget": [c.budget for c in active],
                "Deadline": [c.deadline for c in active],
                "Creators": [len(c.assigned_creators) for c in active],
            })
            st.dataframe(
                active_camp_df,
                hide_index=True,
                column_config={
                    "Budget": st.column_config.NumberColumn("Budget", format="₹%.0f"),
                },
            )
        else:
            st.info("No active campaigns.")
        st.page_link(MATCHING_PAGE, label="Match creators to campaigns", icon=":material/arrow_forward:", width="content")

    with payments_tab:
        creator_names = {c.id: c.name for c in creators}
        campaign_brands = {c.id: c.brand for c in campaigns}
        recent_pays = sorted(payments, key=lambda p: p.due_date or "", reverse=True)[:6]
        if recent_pays:
            pay_df = pd.DataFrame({
                "Payment": [p.id for p in recent_pays],
                "Creator": [creator_names.get(p.creator_id, p.creator_id) for p in recent_pays],
                "Campaign": [campaign_brands.get(p.campaign_id, p.campaign_id) for p in recent_pays],
                "Amount": [p.amount for p in recent_pays],
                "Status": [p.status for p in recent_pays],
                "Due": [p.due_date or "—" for p in recent_pays],
            })
            st.dataframe(
                pay_df,
                hide_index=True,
                column_config={
                    "Amount": st.column_config.NumberColumn("Amount", format="₹%.0f"),
                },
            )
        else:
            st.info("No payments yet.")
        st.page_link(PAYMENTS_PAGE, label="View all payments", icon=":material/arrow_forward:", width="content")

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in dashboard")
