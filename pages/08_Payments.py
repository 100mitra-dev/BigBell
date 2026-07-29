import streamlit as st
import pandas as pd

st.set_page_config(page_title="Payments", page_icon="💰", layout="wide")

from src.core.services.payment_service import PaymentService
from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.utils.display import section_header, status_badge, metric_card


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    if "campaign_service" not in st.session_state:
        st.session_state.campaign_service = CampaignService()
    if "payment_service" not in st.session_state:
        st.session_state.payment_service = PaymentService()
    return st.session_state.creator_service, st.session_state.campaign_service, st.session_state.payment_service


cs, cams, ps = load_data()

section_header("Payment Management", "Track and manage creator payments")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    metric_card("Total Payments", str(len(ps.payments)))
with col2:
    metric_card("Pending", str(ps.get_pending_count()), f"₹{ps.get_total_pending_amount():,.0f}")
with col3:
    metric_card("Processed", str(ps.get_processed_count()))
with col4:
    metric_card("Paid", str(ps.get_paid_count()), f"₹{ps.get_total_paid_amount():,.0f}")
with col5:
    metric_card("Disputed", str(ps.get_disputed_count()), "Needs attention", "Payments under dispute")

st.divider()

tab1, tab2, tab3 = st.tabs(["All Payments", "Pending Payments", "Disputed"])

with tab1:
    payments_data = []
    for p in ps.payments:
        creator = cs.get_by_id(p.creator_id)
        campaign = cams.get_by_id(p.campaign_id)
        payments_data.append({
            "ID": p.id,
            "Creator": creator.name if creator else "Unknown",
            "Campaign": campaign.title if campaign else "Unknown",
            "Amount": f"₹{p.amount:,.0f}",
            "Status": p.status,
            "Due Date": p.due_date,
            "Processed": p.processed_at or "-",
        })

    df = pd.DataFrame(payments_data)
    st.dataframe(
        df,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    pending = ps.filter_by_status("pending")
    if not pending:
        st.info("No pending payments.")
    else:
        for p in pending:
            creator = cs.get_by_id(p.creator_id)
            campaign = cams.get_by_id(p.campaign_id)
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                col1.write(f"**{creator.name if creator else 'Unknown'}**")
                col2.write(campaign.title if campaign else "Unknown")
                col3.write(f"**₹{p.amount:,.0f}**")
                col4.markdown(status_badge(p.status), unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)
                col1.write(f"Due: {p.due_date}")
                col2.write(f"Notes: {p.notes or '-'}")
                if col3.button(f"Mark Processed", key=f"proc_{p.id}"):
                    ps.update_status(p.id, "processed")
                    st.rerun()

                with st.expander("Payment Info"):
                    st.json({
                        "Payment ID": p.id,
                        "Creator ID": p.creator_id,
                        "Campaign ID": p.campaign_id,
                        "Amount": p.amount,
                        "Due Date": p.due_date,
                        "Notes": p.notes,
                    })

with tab3:
    disputed = ps.filter_by_status("disputed")
    if not disputed:
        st.info("No disputed payments.")
    else:
        for p in disputed:
            creator = cs.get_by_id(p.creator_id)
            campaign = cams.get_by_id(p.campaign_id)
            with st.container(border=True):
                st.error(f"**Dispute:** {creator.name if creator else 'Unknown'} - {campaign.title if campaign else 'Unknown'} - ₹{p.amount:,.0f}")
                st.write(f"**Notes:** {p.notes}")

                col1, col2 = st.columns(2)
                if col1.button("Resolve - Mark as Paid", key=f"resolve_paid_{p.id}"):
                    ps.update_status(p.id, "paid")
                    st.rerun()
                if col2.button("Resolve - Mark as Processed", key=f"resolve_proc_{p.id}"):
                    ps.update_status(p.id, "processed")
                    st.rerun()
