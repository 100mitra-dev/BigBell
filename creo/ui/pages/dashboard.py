import streamlit as st
import pandas as pd

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.services.payment_service import PaymentService

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
if "ps" not in st.session_state:
    st.session_state.ps = PaymentService()

cs = st.session_state.cs
cams = st.session_state.cams
ps = st.session_state.ps

st.title("Dashboard")
st.caption("Real-time overview of creator operations")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total creators", len(cs.creators), f"{cs.get_active_count()} active")
col2.metric("Active campaigns", cams.get_active_count(), f"₹{cams.get_total_budget():,.0f} total budget")
col3.metric("Pending reviews", len(cs.filter_by_status("pending")) + len(cs.filter_by_status("onboarding")))
col4.metric("Pending payments", ps.get_pending_count(), f"₹{ps.get_total_pending_amount():,.0f}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Niche distribution")
    niche_dist = cs.get_niche_distribution()
    if niche_dist:
        niche_df = pd.DataFrame(list(niche_dist.items()), columns=["Niche", "Count"])
        st.bar_chart(niche_df, x="Niche", y="Count", horizontal=True)

with col2:
    st.subheader("Status breakdown")
    status_df = pd.DataFrame({
        "Status": ["Active", "Onboarding", "Pending", "Inactive", "Rejected"],
        "Count": [
            cs.get_active_count(), cs.get_onboarding_count(),
            cs.get_pending_count(), cs.get_inactive_count(),
            len(cs.filter_by_status("rejected")),
        ],
    })
    st.bar_chart(status_df, x="Status", y="Count")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Language distribution")
    lang_dist = cs.get_language_distribution()
    if lang_dist:
        lang_df = pd.DataFrame(list(lang_dist.items()), columns=["Language", "Count"])
        st.bar_chart(lang_df, x="Language", y="Count")

with col2:
    st.subheader("Payment status")
    payment_df = pd.DataFrame({
        "Status": ["Paid", "Processed", "Pending", "Disputed"],
        "Count": [ps.get_paid_count(), ps.get_processed_count(), ps.get_pending_count(), ps.get_disputed_count()],
    })
    st.bar_chart(payment_df, x="Status", y="Count")

st.subheader("Recent creators")
for creator in cs.creators[:5]:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.markdown(f"**{creator.name}**")
        c2.write(creator.primary_niche)
        c3.write(f"{creator.primary_language} | {creator.tier}")
        c4.badge(creator.status.value.title(), icon=f":material/{'check_circle' if creator.status.value == 'active' else 'schedule'}:")
