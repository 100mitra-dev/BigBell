import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.core.services.payment_service import PaymentService
from src.utils.display import metric_card, section_header


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    if "campaign_service" not in st.session_state:
        st.session_state.campaign_service = CampaignService()
    if "payment_service" not in st.session_state:
        st.session_state.payment_service = PaymentService()
    return (
        st.session_state.creator_service,
        st.session_state.campaign_service,
        st.session_state.payment_service,
    )


cs, cams, ps = load_data()

section_header("Executive Dashboard", "Real-time overview of creator operations")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    metric_card("Total Creators", str(len(cs.creators)), f"{cs.get_active_count()} active")
with col2:
    metric_card("Active Campaigns", str(cams.get_active_count()), f"₹{cams.get_total_budget():,.0f} total budget")
with col3:
    metric_card("Pending Reviews", str(len(cs.filter_by_status("pending")) + len(cs.filter_by_status("onboarding"))), "Needs attention")
with col4:
    metric_card("Pending Payments", str(ps.get_pending_count()), f"₹{ps.get_total_pending_amount():,.0f}")
with col5:
    hours_saved = len(cs.creators) * 2
    metric_card("Hours Saved (est.)", str(hours_saved), "This week via AI")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Creator Niche Distribution")
    niche_dist = cs.get_niche_distribution()
    fig = px.pie(
        values=list(niche_dist.values()),
        names=list(niche_dist.keys()),
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Creator Status Breakdown")
    status_data = pd.DataFrame({
        "Status": ["Active", "Onboarding", "Pending", "Inactive", "Rejected"],
        "Count": [
            cs.get_active_count(),
            cs.get_onboarding_count(),
            cs.get_pending_count(),
            cs.get_inactive_count(),
            len(cs.filter_by_status("rejected")),
        ],
    })
    fig = px.bar(
        status_data,
        x="Status",
        y="Count",
        color="Status",
        color_discrete_map={
            "Active": "#2ECC71",
            "Onboarding": "#3498DB",
            "Pending": "#F39C12",
            "Inactive": "#95A5A6",
            "Rejected": "#E74C3C",
        },
    )
    fig.update_layout(showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Language Distribution")
    lang_dist = cs.get_language_distribution()
    if lang_dist:
        lang_df = pd.DataFrame(list(lang_dist.items()), columns=["Language", "Count"])
        fig = px.bar(
            lang_df, x="Language", y="Count",
            color="Count", color_continuous_scale="Blues",
        )
        fig.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Payment Status Overview")
    payment_status = pd.DataFrame({
        "Status": ["Paid", "Processed", "Pending", "Disputed"],
        "Count": [ps.get_paid_count(), ps.get_processed_count(), ps.get_pending_count(), ps.get_disputed_count()],
    })
    fig = px.pie(
        payment_status, names="Status", values="Count",
        color="Status",
        color_discrete_map={
            "Paid": "#2ECC71",
            "Processed": "#3498DB",
            "Pending": "#F39C12",
            "Disputed": "#E74C3C",
        },
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Recent Creators")
recent = cs.creators[:5]
for creator in recent:
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        col1.write(f"**{creator.name}**")
        col2.write(creator.primary_niche)
        col3.write(f"{creator.primary_language} | {creator.tier}")
        col4.write(creator.status.value.title())
