import streamlit as st
import pandas as pd

st.set_page_config(page_title="Creator CRM", page_icon="👥", layout="wide")

from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.core.services.payment_service import PaymentService
from src.utils.display import section_header, status_badge, creator_card


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    if "campaign_service" not in st.session_state:
        st.session_state.campaign_service = CampaignService()
    if "payment_service" not in st.session_state:
        st.session_state.payment_service = PaymentService()
    return st.session_state.creator_service, st.session_state.campaign_service, st.session_state.payment_service


cs, cams, ps = load_data()

section_header("Creator CRM", "Manage creator records and activity")

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Filters")
    status_filter = st.selectbox("Status", ["All", "active", "onboarding", "pending", "inactive", "rejected"])
    niche_filter = st.selectbox("Niche", ["All"] + sorted(cs.get_niche_distribution().keys()))
    lang_filter = st.selectbox("Language", ["All"] + sorted(cs.get_language_distribution().keys()))

with col2:
    search_query = st.text_input("Search creators...", placeholder="Name, email, niche, or language...")

creators = cs.creators
if search_query:
    creators = cs.search(search_query)
if status_filter != "All":
    creators = [c for c in creators if c.status.value == status_filter]
if niche_filter != "All":
    creators = [c for c in creators if c.primary_niche == niche_filter or niche_filter in c.secondary_niches]
if lang_filter != "All":
    creators = [c for c in creators if c.primary_language == lang_filter or lang_filter in c.secondary_languages]

st.write(f"Showing **{len(creators)}** creators")

for creator in creators:
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])

        with col1:
            initial = creator.name.split()[0][0].upper()
            st.markdown(
                f"""
                <div style="width:70px;height:70px;border-radius:50%;background:#1E88E5;display:flex;align-items:center;justify-content:center;
                font-size:2rem;font-weight:700;color:white;margin-bottom:0.5rem;">
                    {initial}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(status_badge(creator.status.value), unsafe_allow_html=True)

        with col2:
            st.markdown(f"### {creator.name}")
            st.caption(f"{creator.email} | {creator.phone or 'No phone'}")
            st.markdown(f"**{creator.primary_niche}** | {creator.primary_language}")

            cols = st.columns(5)
            cols[0].metric("Total Followers", f"{creator.total_followers:,}")
            cols[1].metric("Engagement", f"{creator.avg_engagement_rate}%")
            cols[2].metric("Quality", f"{creator.content_quality_score}/10")
            cols[3].metric("Completeness", f"{creator.profile_completeness}%")
            cols[4].metric("Campaigns", str(creator.total_campaigns_completed))

            with st.expander("Platform Details"):
                for platform, info in creator.platforms.items():
                    st.markdown(f"- **{platform.title()}**: {info.handle} ({info.followers:,} followers) {'✅' if info.verified else '❌'}")

            with st.expander("Campaign History"):
                creator_campaigns = [c for c in cams.campaigns if creator.id in c.assigned_creators]
                if creator_campaigns:
                    for c in creator_campaigns:
                        st.markdown(f"- **{c.title}** ({c.brand}) — {c.status}")
                else:
                    st.write("No campaign history yet.")

            with st.expander("Payment History"):
                creator_payments = ps.get_for_creator(creator.id)
                if creator_payments:
                    for p in creator_payments:
                        st.markdown(f"- ₹{p.amount:,.0f} — {p.status} — Due: {p.due_date}")
                else:
                    st.write("No payment history yet.")

            if creator.notes:
                st.caption(f"📝 {creator.notes}")

            col1, col2, col3, col4 = st.columns(4)
            if creator.status.value != "active":
                if col1.button(f"Activate", key=f"act_{creator.id}"):
                    cs.update_status(creator.id, "active")
                    st.rerun()
            if creator.status.value != "inactive":
                if col2.button(f"Deactivate", key=f"deact_{creator.id}"):
                    cs.update_status(creator.id, "inactive")
                    st.rerun()
            if creator.status.value != "pending":
                if col3.button(f"Mark Pending", key=f"pend_{creator.id}"):
                    cs.update_status(creator.id, "pending")
                    st.rerun()

    st.divider()
