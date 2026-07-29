import streamlit as st
import pandas as pd
import uuid

from creo.services.payment_service import PaymentService
from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.models import Payment
from creo.storage.csv_handler import export_payments_to_csv, import_payments_from_csv

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

tool1, tool2, tool3 = st.columns([1, 1, 2])
with tool1:
    st.toggle("Add payment", key="show_add_payment_toggle", help="Show add payment form")
with tool2:
    csv_data = export_payments_to_csv(ps.payments)
    st.download_button("Export CSV", data=csv_data, file_name="payments.csv", mime="text/csv", icon=":material/download:", use_container_width=True)
with tool3:
    uploaded = st.file_uploader("Import payments from CSV", type="csv", label_visibility="collapsed")
    if uploaded:
        content = uploaded.getvalue().decode("utf-8")
        imported = import_payments_from_csv(content)
        for pmt in imported:
            ps.add(pmt)
        st.success(f"Imported {len(imported)} payments")
        st.rerun()

if st.session_state.get("show_add_payment_toggle"):
    with st.container(border=True):
        st.markdown("**Add payment**")
        with st.form("add_payment_form"):
            creator_opts = [(c.id, f"{c.name} ({c.email})") for c in cs.creators]
            creator_id = st.selectbox("Creator", options=creator_opts, format_func=lambda x: x[1])
            campaign_opts = [(c.id, f"{c.title} ({c.brand})") for c in cams.campaigns]
            campaign_id = st.selectbox("Campaign", options=campaign_opts, format_func=lambda x: x[1])
            col_amount, col_due = st.columns(2)
            with col_amount:
                amount = st.number_input("Amount (₹)", min_value=0.0, value=10000.0, step=1000.0)
            with col_due:
                due_date = st.date_input("Due date")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True)
            if submitted and creator_id and campaign_id:
                cid = creator_id[0] if isinstance(creator_id, (list, tuple)) else creator_id
                camid = campaign_id[0] if isinstance(campaign_id, (list, tuple)) else campaign_id
                payment = Payment(
                    id=str(uuid.uuid4()),
                    creator_id=cid,
                    campaign_id=camid,
                    amount=amount,
                    due_date=due_date.isoformat(),
                    notes=notes or None,
                    status="pending",
                )
                ps.add(payment)
                st.session_state.show_add_payment_toggle = False
                st.rerun()

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
    for p in ps.payments:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c2:
            st.toggle("Edit", key=f"edit_pay_{p.id}", help="Edit this payment")
        with c3:
            if st.button("Delete", key=f"del_pay_{p.id}", icon=":material/delete:"):
                ps.delete(p.id)
                st.rerun()

        if st.session_state.get(f"edit_pay_{p.id}"):
            with st.container(border=True):
                st.markdown(f"**Edit payment**")
                with st.form(f"edit_pay_form_{p.id}"):
                    e_amount = st.number_input("Amount (₹)", min_value=0.0, value=p.amount, step=1000.0)
                    e_status = st.selectbox("Status", ["pending", "processed", "paid", "disputed"], index=["pending", "processed", "paid", "disputed"].index(p.status))
                    e_notes = st.text_area("Notes", value=p.notes or "")
                    saved = st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True)
                    if saved:
                        p.amount = e_amount
                        p.status = e_status
                        p.notes = e_notes or None
                        ps.repo.save_all(ps.payments)
                        st.session_state[f"edit_pay_{p.id}"] = False
                        st.rerun()

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
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    if st.button("Mark processed", key=f"proc_{p.id}", icon=":material/done_all:", use_container_width=True):
                        ps.update_status(p.id, "processed")
                        st.rerun()
                with c2:
                    if st.button("Delete", key=f"del_{p.id}", icon=":material/delete:", use_container_width=True):
                        ps.delete(p.id)
                        st.rerun()
                with c3:
                    with st.expander("Details", icon=":material/info:"):
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
                    if st.button("Resolve — mark as paid", key=f"rpaid_{p.id}", icon=":material/check:", use_container_width=True):
                        ps.update_status(p.id, "paid")
                        st.rerun()
                with c2:
                    if st.button("Resolve — mark as processed", key=f"rproc_{p.id}", icon=":material/done_all:", use_container_width=True):
                        ps.update_status(p.id, "processed")
                        st.rerun()
