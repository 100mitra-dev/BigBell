import streamlit as st

from src.core.services.creator_service import CreatorService
from src.core.services.campaign_service import CampaignService
from src.core.services.payment_service import PaymentService
from app.components.cards import creator_card, creator_avatar

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
if "ps" not in st.session_state:
    st.session_state.ps = PaymentService()
cs = st.session_state.cs
cams = st.session_state.cams
ps = st.session_state.ps

st.title("Creator CRM")
st.caption("Full creator record management")

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Filters")
    status_f = st.selectbox("Status", ["All", "active", "onboarding", "pending", "inactive", "rejected"])
    niche_f = st.selectbox("Niche", ["All"] + sorted(cs.get_niche_distribution().keys()))
    lang_f = st.selectbox("Language", ["All"] + sorted(cs.get_language_distribution().keys()))

with col2:
    q = st.text_input("Search creators", placeholder="Name, email, niche, or language...", label_visibility="collapsed")

creators = cs.creators
if q:
    creators = cs.search(q)
if status_f != "All":
    creators = [c for c in creators if c.status.value == status_f]
if niche_f != "All":
    creators = [c for c in creators if c.primary_niche == niche_f or niche_f in c.secondary_niches]
if lang_f != "All":
    creators = [c for c in creators if c.primary_language == lang_f or lang_f in c.secondary_languages]

st.caption(f"Showing **{len(creators)}** creators")

for creator in creators:
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])

        with c1:
            creator_avatar(creator.name, 64)
            st.badge(creator.status.value)

        with c2:
            st.markdown(f"### {creator.name}")
            st.caption(f"{creator.email} | {creator.phone or 'No phone'}")
            st.markdown(f"**{creator.primary_niche}** | {creator.primary_language}")

            m = st.columns(5)
            m[0].metric("Followers", f"{creator.total_followers:,}")
            m[1].metric("Engagement", f"{creator.avg_engagement_rate}%")
            m[2].metric("Quality", f"{creator.content_quality_score}/10")
            m[3].metric("Completeness", f"{creator.profile_completeness}%")
            m[4].metric("Campaigns", str(creator.total_campaigns_completed))

            with st.expander("Platform details", icon=":material/language:"):
                for platform, info in creator.platforms.items():
                    v = ":material/check_circle:" if info.verified else ":material/cancel:"
                    st.markdown(f"- **{platform.title()}**: {info.handle} ({info.followers:,} followers) {v}")

            with st.expander("Campaign history", icon=":material/campaign:"):
                cc = [c for c in cams.campaigns if creator.id in c.assigned_creators]
                if cc:
                    for c in cc:
                        st.markdown(f"- **{c.title}** ({c.brand}) — {c.status}")
                else:
                    st.write("No campaign history yet.")

            with st.expander("Payment history", icon=":material/payments:"):
                cp = ps.get_for_creator(creator.id)
                if cp:
                    for p in cp:
                        st.markdown(f"- ₹{p.amount:,.0f} — {p.status} — Due: {p.due_date}")
                else:
                    st.write("No payment history yet.")

            if creator.notes:
                st.caption(f":material/note: {creator.notes}")

            c1, c2, c3 = st.columns(3)
            if creator.status.value != "active":
                with c1:
                    if st.button("Activate", key=f"act_{creator.id}", icon=":material/check_circle:"):
                        cs.update_status(creator.id, "active")
                        st.rerun()
            if creator.status.value != "inactive":
                with c2:
                    if st.button("Deactivate", key=f"deact_{creator.id}", icon=":material/pause_circle:"):
                        cs.update_status(creator.id, "inactive")
                        st.rerun()
            if creator.status.value != "pending":
                with c3:
                    if st.button("Mark pending", key=f"pend_{creator.id}", icon=":material/schedule:"):
                        cs.update_status(creator.id, "pending")
                        st.rerun()
