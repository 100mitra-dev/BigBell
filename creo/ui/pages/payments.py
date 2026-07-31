import logging
import uuid
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from creo.models import Payment
from creo.services.campaign_service import CampaignService
from creo.services.creator_service import CreatorService
from creo.services.payment_service import PaymentService
from creo.storage.csv_handler import export_payments_to_csv, import_payments_from_csv

logger = logging.getLogger(__name__)

if "ps" not in st.session_state:
    st.session_state.ps = PaymentService()
if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
ps = st.session_state.ps
cs = st.session_state.cs
cams = st.session_state.cams

STATUS_LABELS = {
    "pending": "Pending",
    "processed": "Processed",
    "paid": "Paid",
    "disputed": "Disputed",
}
STATUS_ICONS = {
    "pending": ":material/schedule:",
    "processed": ":material/done_all:",
    "paid": ":material/check_circle:",
    "disputed": ":material/error:",
}
STATUS_COLORS = {
    "pending": "orange",
    "processed": "blue",
    "paid": "green",
    "disputed": "red",
}

PAY_ACTIONS_KEY = "pay_actions"


def _creator_name(p) -> str:
    creator = cs.get_by_id(p.creator_id)
    return creator.name if creator else "Unknown"


def _campaign_title(p) -> str:
    campaign = cams.get_by_id(p.campaign_id)
    return campaign.title if campaign else "Unknown"


def on_payment_action():
    click = st.session_state.get(PAY_ACTIONS_KEY)
    if not click:
        return
    order = st.session_state.get("pay_id_order", [])
    row, label = click["row"], click["label"]
    if row >= len(order):
        return
    payment_id = order[row]
    if "Edit" in label:
        st.session_state.edit_payment_id = payment_id
    else:
        st.session_state.delete_payment_id = payment_id


def _open_add_payment():
    st.session_state.add_payment_open = True


def _open_import_payments():
    st.session_state.import_payments_open = True


def _clear_add_payment():
    st.session_state.pop("add_payment_open", None)


@st.dialog("Add payment", width="large", on_dismiss=_clear_add_payment)
def add_payment_dialog():
    creator_opts = [(c.id, f"{c.name} ({c.email})") for c in cs.creators]
    campaign_opts = [(c.id, f"{c.title} ({c.brand})") for c in cams.campaigns]
    creator_id = st.selectbox("Creator", options=creator_opts, format_func=lambda x: x[1], key="add_creator")
    campaign_id = st.selectbox("Campaign", options=campaign_opts, format_func=lambda x: x[1], key="add_campaign")
    c_amount, c_due = st.columns(2)
    with c_amount:
        amount = st.number_input("Amount (₹)", min_value=0.0, value=10000.0, step=1000.0, key="add_amount")
    with c_due:
        due_date = st.date_input("Due date", value=date.today(), key="add_due_date")
    notes = st.text_area("Notes", placeholder="Optional payment notes...", key="add_notes")
    if st.button("Save payment", type="primary", icon=":material/save:", width="stretch") and creator_id and campaign_id:
        creator_id = creator_id[0] if isinstance(creator_id, (list, tuple)) else creator_id
        campaign_id = campaign_id[0] if isinstance(campaign_id, (list, tuple)) else campaign_id
        ps.add(Payment(
            id=str(uuid.uuid4()),
            creator_id=creator_id,
            campaign_id=campaign_id,
            amount=amount,
            due_date=due_date.isoformat(),
            notes=notes or None,
            status="pending",
        ))
        st.session_state.pop("add_payment_open", None)
        st.toast("Payment added")
        st.rerun()


def _clear_import_payments():
    st.session_state.pop("import_payments_open", None)


@st.dialog("Import payments from CSV", width="large", on_dismiss=_clear_import_payments)
def import_payments_dialog():
    uploaded = st.file_uploader("Choose a CSV file", type="csv", key="pay_csv_import")
    if uploaded is not None:
        content = uploaded.getvalue().decode("utf-8")
        imported = import_payments_from_csv(content)
        for pmt in imported:
            ps.add(pmt)
        st.session_state.pop("import_payments_open", None)
        st.toast(f"Imported {len(imported)} payments")
        st.rerun()


def _clear_edit_payment():
    st.session_state.pop("edit_payment_id", None)


@st.dialog("Edit payment", width="large", on_dismiss=_clear_edit_payment)
def edit_payment_dialog(payment_id):
    p = ps.get_by_id(payment_id)
    if p is None:
        st.session_state.pop("edit_payment_id", None)
        st.rerun()
    creator = cs.get_by_id(p.creator_id)
    campaign = cams.get_by_id(p.campaign_id)
    st.caption(f"{creator.name if creator else 'Unknown'} · {campaign.title if campaign else 'Unknown'}")
    c_amount, c_status = st.columns(2)
    with c_amount:
        e_amount = st.number_input("Amount (₹)", min_value=0.0, value=p.amount, step=1000.0, key=f"edit_amount_{payment_id}")
    with c_status:
        status_opts = list(STATUS_LABELS)
        e_status = st.selectbox(
            "Status",
            options=status_opts,
            index=status_opts.index(p.status) if p.status in status_opts else 0,
            format_func=lambda s: STATUS_LABELS[s],
            key=f"edit_status_{payment_id}",
        )
    e_notes = st.text_area("Notes", value=p.notes or "", key=f"edit_notes_{payment_id}")
    if st.button("Save changes", type="primary", icon=":material/save:", width="stretch"):
        p.amount = e_amount
        p.status = e_status
        p.notes = e_notes or None
        ps.repo.save_all(ps.payments)
        st.session_state.pop("edit_payment_id", None)
        st.toast("Payment updated")
        st.rerun()


def _clear_delete_payment():
    st.session_state.pop("delete_payment_id", None)


@st.dialog("Delete payment", width="small", on_dismiss=_clear_delete_payment)
def delete_payment_dialog(payment_id):
    p = ps.get_by_id(payment_id)
    if p is None:
        st.session_state.pop("delete_payment_id", None)
        st.rerun()
    creator = cs.get_by_id(p.creator_id)
    campaign = cams.get_by_id(p.campaign_id)
    st.write(
        f"Delete the payment of **₹{p.amount:,.0f}** to **{creator.name if creator else 'Unknown'}** "
        f"for **{campaign.title if campaign else 'Unknown'}**? This cannot be undone."
    )
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("Cancel"):
            st.session_state.pop("delete_payment_id", None)
            st.rerun()
        if st.button("Delete", type="primary", icon=":material/delete:"):
            ps.delete(payment_id)
            st.session_state.pop("delete_payment_id", None)
            st.toast("Payment deleted")
            st.rerun()


st.title("Payments")
st.caption("Track creator payments from due to paid, resolve disputes, and review per-creator payouts.")

try:
    payments = ps.payments

    kpi_cols = st.columns(4, border=True)
    with kpi_cols[0]:
        st.metric("Total payments", len(payments), help="All payment records.")
    with kpi_cols[1]:
        st.metric("Pending", ps.get_pending_count(), f"₹{ps.get_total_pending_amount():,.0f} due")
    with kpi_cols[2]:
        st.metric("Paid", ps.get_paid_count(), f"₹{ps.get_total_paid_amount():,.0f} paid")
    with kpi_cols[3]:
        st.metric("Disputed", ps.get_disputed_count())

    with st.container(horizontal=True, horizontal_alignment="distribute"):
        st.button("Add payment", icon=":material/add:", on_click=_open_add_payment)
        st.button("Import CSV", icon=":material/file_upload:", on_click=_open_import_payments)
        st.download_button(
            "Export CSV",
            data=export_payments_to_csv(payments),
            file_name="payments.csv",
            mime="text/csv",
            icon=":material/file_download:",
        )

    tab1, tab2, tab3, tab4 = st.tabs([
        "All payments",
        "Pending payments",
        "Disputed",
        "Per-creator payouts",
    ])

    with tab1:
        if not payments:
            st.info("No payments yet. Add one above or import a CSV.", icon=":material/inbox:")
        else:
            rows = [{
                "Creator": _creator_name(p),
                "Campaign": _campaign_title(p),
                "Amount": p.amount,
                "Status": STATUS_LABELS.get(p.status, p.status),
                "Due date": pd.to_datetime(p.due_date, errors="coerce") if p.due_date else pd.NaT,
                "Actions": [":material/edit: Edit", ":material/delete: Delete"],
            } for p in payments]
            st.session_state["pay_id_order"] = [p.id for p in payments]
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                column_config={
                    "Creator": st.column_config.TextColumn("Creator", pinned=True),
                    "Campaign": st.column_config.TextColumn("Campaign"),
                    "Amount": st.column_config.NumberColumn("Amount", format="₹%,.0f"),
                    "Status": st.column_config.TextColumn("Status"),
                    "Due date": st.column_config.DateColumn("Due date", format="MMM DD, YYYY"),
                    "Actions": st.column_config.ButtonColumn("Actions", on_click=on_payment_action, key=PAY_ACTIONS_KEY),
                },
            )

    with tab2:
        pending = ps.filter_by_status("pending")
        if not pending:
            st.info("No pending payments.", icon=":material/check_circle:")
        else:
            for p in pending:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{_creator_name(p)}**")
                        st.caption(f"{_campaign_title(p)} · Due {p.due_date}")
                        if p.notes:
                            st.caption(p.notes)
                    with c2:
                        st.markdown(f"**₹{p.amount:,.0f}**", text_alignment="right")
                        st.badge(STATUS_LABELS["pending"], icon=STATUS_ICONS["pending"], color=STATUS_COLORS["pending"])
                    with st.container(horizontal=True):
                        if st.button("Mark processed", key=f"proc_{p.id}", type="primary", icon=":material/done_all:"):
                            ps.update_status(p.id, "processed")
                            st.toast("Payment marked as processed")
                            st.rerun()
                        if st.button("Delete", key=f"del_{p.id}", icon=":material/delete:"):
                            ps.delete(p.id)
                            st.toast("Payment deleted")
                            st.rerun()
                        with st.popover("Details", icon=":material/info:"):
                            st.json({
                                "Payment ID": p.id,
                                "Creator ID": p.creator_id,
                                "Campaign ID": p.campaign_id,
                                "Amount": p.amount,
                                "Due date": p.due_date,
                                "Notes": p.notes,
                            })

    with tab3:
        disputed = ps.filter_by_status("disputed")
        if not disputed:
            st.info("No disputed payments.", icon=":material/check_circle:")
        else:
            for p in disputed:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{_creator_name(p)}**")
                        st.caption(f"{_campaign_title(p)} · Due {p.due_date}")
                        if p.notes:
                            st.caption(p.notes)
                    with c2:
                        st.markdown(f"**₹{p.amount:,.0f}**", text_alignment="right")
                        st.badge(STATUS_LABELS["disputed"], icon=STATUS_ICONS["disputed"], color=STATUS_COLORS["disputed"])
                    st.caption("Resolve the dispute by moving the payment forward:")
                    with st.container(horizontal=True):
                        if st.button("Mark as paid", key=f"rpaid_{p.id}", type="primary", icon=":material/check:"):
                            ps.update_status(p.id, "paid")
                            st.toast("Dispute resolved — marked as paid")
                            st.rerun()
                        if st.button("Mark as processed", key=f"rproc_{p.id}", icon=":material/done_all:"):
                            ps.update_status(p.id, "processed")
                            st.toast("Dispute resolved — marked as processed")
                            st.rerun()

    with tab4:
        creator_totals = {}
        for p in payments:
            name = _creator_name(p)
            totals = creator_totals.setdefault(name, {"count": 0, "total": 0.0, "paid": 0.0, "pending": 0.0})
            totals["count"] += 1
            totals["total"] += p.amount
            if p.status == "paid":
                totals["paid"] += p.amount
            elif p.status == "pending":
                totals["pending"] += p.amount

        if not creator_totals:
            st.info("No payment data available.", icon=":material/info:")
        else:
            summary_rows = [{
                "Creator": name,
                "Payments": vals["count"],
                "Total": vals["total"],
                "Paid": vals["paid"],
                "Pending": vals["pending"],
            } for name, vals in sorted(creator_totals.items(), key=lambda x: -x[1]["total"])]
            summary_df = pd.DataFrame(summary_rows)

            chart = alt.Chart(summary_df.nlargest(10, "Total")).mark_bar().encode(
                x=alt.X("Total:Q", title="Total payout (₹)"),
                y=alt.Y("Creator:N", sort="-x", title=None),
                color=alt.value("#1E88E5"),
            ).properties(height=240)
            st.altair_chart(chart)

            st.markdown("#### Payout summary")
            st.dataframe(summary_df, hide_index=True, column_config={
                "Payments": st.column_config.NumberColumn(width="small"),
                "Total": st.column_config.NumberColumn("Total", format="₹%,.0f"),
                "Paid": st.column_config.NumberColumn("Paid", format="₹%,.0f"),
                "Pending": st.column_config.NumberColumn("Pending", format="₹%,.0f"),
            })

            st.markdown("#### Payout detail")
            selected = st.selectbox("Select creator", options=list(creator_totals))
            detail_rows = [{
                "Campaign": _campaign_title(p),
                "Amount": p.amount,
                "Status": STATUS_LABELS.get(p.status, p.status),
                "Due date": p.due_date,
            } for p in payments if _creator_name(p) == selected]
            st.dataframe(pd.DataFrame(detail_rows), hide_index=True, column_config={
                "Amount": st.column_config.NumberColumn("Amount", format="₹%,.0f"),
            })

    if st.session_state.get("add_payment_open"):
        add_payment_dialog()
    if st.session_state.get("import_payments_open"):
        import_payments_dialog()
    if st.session_state.get("edit_payment_id"):
        edit_payment_dialog(st.session_state["edit_payment_id"])
    if st.session_state.get("delete_payment_id"):
        delete_payment_dialog(st.session_state["delete_payment_id"])

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in payments")
