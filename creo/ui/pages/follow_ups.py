import streamlit as st
import pandas as pd

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.utils.helpers import days_until

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
cs = st.session_state.cs
cams = st.session_state.cams

st.title("Follow-ups")
st.caption("Deadline tracking and deliverable management")

active = cams.get_active_campaigns()
overdue = sum(1 for c in active if days_until(c.deadline) < 0)
due_soon = sum(1 for c in active if 0 <= days_until(c.deadline) <= 7)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Active campaigns", len(active))
col2.metric("Overdue", overdue, delta_color="inverse")
col3.metric("Due soon (7 days)", due_soon)
col4.metric("Total assigned", sum(len(c.assigned_creators) for c in active))

tab1, tab2 = st.tabs(["Campaign deadlines", "Pending deliverables"])

with tab1:
    for campaign in sorted(active, key=lambda c: c.deadline):
        d = days_until(campaign.deadline)
        color, label = ("#E74C3C", "Overdue") if d < 0 else ("#F39C12", "Critical") if d <= 3 else ("#E67E22", "Due soon") if d <= 7 else ("#3498DB", "Approaching") if d <= 14 else ("#2ECC71", "On track")
        icon = ":material/error:" if d < 0 else ":material/schedule:" if d <= 7 else ":material/check_circle:"

        with st.container(border=True):
            st.markdown(f"**{campaign.title}** — *{campaign.brand}*")
            st.caption(f"Assigned: {len(campaign.assigned_creators)} creators | Budget: ₹{campaign.budget:,.0f}")

            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"**Deadline:** {campaign.deadline} ({d} days)")
            with c2:
                st.html(f'<span style="color:{color};font-weight:600;">{icon} {label}</span>')
            with c3:
                if d <= 7 and st.button("Send follow-up", key=f"fu_{campaign.id}", icon=":material/send:"):
                    names = [cs.get_by_id(cid).name for cid in campaign.assigned_creators if cs.get_by_id(cid)]
                    st.success(f":material/check: Follow-up sent to {', '.join(names)}")

with tab2:
    deliverables = []
    for campaign in active:
        for cid in campaign.assigned_creators:
            creator = cs.get_by_id(cid)
            if creator:
                d = days_until(campaign.deadline)
                deliverables.append({
                    "Creator": creator.name,
                    "Campaign": campaign.title,
                    "Deadline": campaign.deadline,
                    "Days left": d,
                    "Status": "Overdue" if d < 0 else "Pending" if d <= 7 else "On track",
                })

    if deliverables:
        df = pd.DataFrame(deliverables)
        st.dataframe(df, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Send reminders to all overdue", type="primary", icon=":material/notifications:"):
                overdue_items = [d for d in deliverables if d["Days left"] < 0]
                if overdue_items:
                    st.success(f":material/check: Reminders sent to {len(overdue_items)} creators")
                else:
                    st.info("No overdue deliverables found.")
        with c2:
            if active:
                sample = active[0]
                msg = f"Hi team! Reminder about the upcoming deadline for **{sample.title}** ({sample.brand}). Please submit deliverables by {sample.deadline}. Reach out if you need support!"
                st.code(msg, language="text")
    else:
        st.info("No pending deliverables.", icon=":material/inbox:")
