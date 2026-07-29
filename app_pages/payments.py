import streamlit as st
import pandas as pd

from src.core.services.payment_service import PaymentService
from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService

if "ps" not in st.session_state:
    st.session_state.ps = PaymentService()
if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
ps = st.session_state.ps
cs = st.session_state.cs
cams = st.session_state.cams

st.title("Payments")
st.caption("Track and manage creator payments")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total payments", len(ps.payments))
col2.metric("Pending", ps.get_pending_count(), f"₹{ps.get_total_pending_amount():,.0f}")
col3.metric("Paid", ps.get_paid_count(), f"₹{ps.get_total_paid_amount():,.0f}")
col4.metric("Disputed", ps.get_disputed_count())

tab1, tab2, tab3 = st.tabs(["All payments", "Pending payments", "Disputed"])

with tab1:
    rows = []
    for p in ps.payments:
        creator = cs.get_by_id(p.creator_id)
        campaign = cams.get_by_id(p.campaign_id)
        rows.append({
            "ID": p.id,
            "Creator": creator.name if creator else "Unknown",
            "Campaign": campaign.title if campaign else "Unknown",
            "Amount": f"₹{p.amount:,.0f}",
            "Status": p.status,
            "Due": p.due_date,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True)

with tab2:
    pending = ps.filter_by_status("pending")
    if not pending:
        st.info("No pending payments.", icon=":material/check_circle:")
    else:
        for p in pending:
            creator = cs.get_by_id(p.creator_id)
            campaign = cams.get_by_id(p.campaign_id)
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.markdown(f"**{creator.name if creator else 'Unknown'}**")
                with c2:
                    st.write(campaign.title if campaign else "Unknown")
                with c3:
                    st.badge(p.status, icon=":material/schedule:")
                st.markdown(f"**₹{p.amount:,.0f}** | Due: {p.due_date} | Notes: {p.notes or '-'}")
                c1, c2 = st.columns([1, 3])
                with c1:
                    if st.button("Mark processed", key=f"proc_{p.id}", icon=":material/done_all:"):
                        ps.update_status(p.id, "processed")
                        st.rerun()
                with c2:
                    with st.expander("Payment details", icon=":material/info:"):
                        st.json({
                            "Payment ID": p.id, "Creator ID": p.creator_id,
                            "Campaign ID": p.campaign_id, "Amount": p.amount,
                            "Due Date": p.due_date, "Notes": p.notes,
                        })

with tab3:
    disputed = ps.filter_by_status("disputed")
    if not disputed:
        st.info("No disputed payments.", icon=":material/check_circle:")
    else:
        for p in disputed:
            creator = cs.get_by_id(p.creator_id)
            campaign = cams.get_by_id(p.campaign_id)
            with st.container(border=True):
                st.error(f"**Dispute:** {creator.name if creator else 'Unknown'} — {campaign.title if campaign else 'Unknown'} — ₹{p.amount:,.0f}")
                st.write(f"**Notes:** {p.notes}")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Resolve — mark as paid", key=f"rpaid_{p.id}", icon=":material/check:"):
                        ps.update_status(p.id, "paid")
                        st.rerun()
                with c2:
                    if st.button("Resolve — mark as processed", key=f"rproc_{p.id}", icon=":material/done_all:"):
                        ps.update_status(p.id, "processed")
                        st.rerun()
