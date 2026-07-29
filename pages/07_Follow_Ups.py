import streamlit as st
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Follow-Ups", page_icon="📅", layout="wide")

from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.utils.display import section_header, status_badge, metric_card
from src.utils.helpers import days_until


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    if "campaign_service" not in st.session_state:
        st.session_state.campaign_service = CampaignService()
    return st.session_state.creator_service, st.session_state.campaign_service


cs, cams = load_data()

section_header("Follow-Ups & Deadlines", "Track pending deliverables and campaign deadlines")

active_campaigns = cams.get_active_campaigns()

overdue_count = 0
due_soon_count = 0
for c in active_campaigns:
    d = days_until(c.deadline)
    if d < 0:
        overdue_count += 1
    elif d <= 7:
        due_soon_count += 1

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Active Campaigns", str(len(active_campaigns)))
with col2:
    metric_card("Overdue", str(overdue_count), f"-{overdue_count} campaigns", "Past deadline")
with col3:
    metric_card("Due Soon (7 days)", str(due_soon_count), "Needs attention")
with col4:
    total_assigned = sum(len(c.assigned_creators) for c in active_campaigns)
    metric_card("Total Assigned", str(total_assigned), "Creator assignments")

st.divider()

tab1, tab2 = st.tabs(["Campaign Deadlines", "Pending Deliverables"])

with tab1:
    st.subheader("Campaign Timeline")
    for campaign in sorted(active_campaigns, key=lambda c: c.deadline):
        d = days_until(campaign.deadline)
        if d < 0:
            status = "🔴 Overdue"
            color = "#E74C3C"
        elif d <= 3:
            status = "🟡 Critical"
            color = "#F39C12"
        elif d <= 7:
            status = "🟠 Due Soon"
            color = "#E67E22"
        elif d <= 14:
            status = "🔵 Approaching"
            color = "#3498DB"
        else:
            status = "🟢 On Track"
            color = "#2ECC71"

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{campaign.title}** *— {campaign.brand}*")
                st.caption(f"Assigned creators: {len(campaign.assigned_creators)} | Budget: ₹{campaign.budget:,.0f}")
            with col2:
                st.markdown(f"**Deadline:** {campaign.deadline}")
            with col3:
                st.markdown(f"**{d} days**")
            with col4:
                st.markdown(f"<span style='color:{color};font-weight:600;'>{status}</span>", unsafe_allow_html=True)

            if d <= 7:
                if st.button(f"Send Follow-up", key=f"follow_{campaign.id}"):
                    assigned = [cs.get_by_id(cid) for cid in campaign.assigned_creators]
                    assigned_names = [c.name for c in assigned if c]
                    st.success(f"📧 Follow-up sent to {', '.join(assigned_names)} for *{campaign.title}*")

with tab2:
    st.subheader("Creator Deliverable Tracker")
    deliverables = []
    for campaign in active_campaigns:
        for cid in campaign.assigned_creators:
            creator = cs.get_by_id(cid)
            if creator:
                d = days_until(campaign.deadline)
                deliverables.append({
                    "Creator": creator.name,
                    "Campaign": campaign.title,
                    "Brand": campaign.brand,
                    "Deadline": campaign.deadline,
                    "Days Left": d,
                    "Status": "Overdue" if d < 0 else "Pending" if d <= 7 else "On Track",
                })

    if deliverables:
        df = pd.DataFrame(deliverables)
        st.dataframe(
            df,
            column_config={
                "Status": st.column_config.TextColumn(
                    "Status",
                    help="Deliverable status",
                    width="small",
                ),
            },
            use_container_width=True,
            hide_index=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Bulk Follow-up")
            if st.button("Send Reminders to All Overdue", type="primary"):
                overdue = [d for d in deliverables if d["Days Left"] < 0]
                if overdue:
                    st.success(f"📧 Reminders sent to {len(overdue)} creators for overdue deliverables")
                else:
                    st.info("No overdue deliverables found.")
        with col2:
            st.subheader("Auto-generate Message")
            sample_campaign = active_campaigns[0] if active_campaigns else None
            if sample_campaign:
                msg = f"Hi Team! This is a gentle reminder about the upcoming deadline for **{sample_campaign.title}** ({sample_campaign.brand}). Please ensure all deliverables are submitted by {sample_campaign.deadline}. Reach out if you need any support! 🚀"
                st.code(msg, language="text")
