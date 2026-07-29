import streamlit as st
import uuid

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.services.payment_service import PaymentService
from creo.ui.components.cards import creator_avatar
from creo.models import Creator, PlatformInfo, CreatorStatus
from creo.config import NICHES, LANGUAGES
from creo.storage.csv_handler import export_creators_to_csv, import_creators_from_csv

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

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("Filters")
    status_f = st.selectbox("Status", ["All", "active", "onboarding", "pending", "inactive", "rejected"])
    niche_f = st.selectbox("Niche", ["All"] + sorted(cs.get_niche_distribution().keys()))
    lang_f = st.selectbox("Language", ["All"] + sorted(cs.get_language_distribution().keys()))

with col2:
    q = st.text_input("Search creators", placeholder="Name, email, niche, or language...", label_visibility="collapsed")

with col3:
    st.write("")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.toggle("Add", key="show_add_creator_toggle", help="Show add creator form")
    with c2:
        csv_data = export_creators_to_csv(cs.creators)
        st.download_button("Export CSV", data=csv_data, file_name="creators.csv", mime="text/csv", icon=":material/download:", use_container_width=True)

uploaded = st.file_uploader("Import creators from CSV", type="csv", label_visibility="collapsed")
if uploaded:
    content = uploaded.getvalue().decode("utf-8")
    imported = import_creators_from_csv(content)
    for creator in imported:
        cs.add(creator)
    st.success(f"Imported {len(imported)} creators")
    st.rerun()

if st.session_state.get("show_add_creator_toggle"):
    with st.container(border=True):
        st.markdown("**Add creator**")
        with st.form("add_creator_form"):
            col_name, col_email = st.columns(2)
            with col_name:
                name = st.text_input("Name", placeholder="Creator name")
            with col_email:
                email = st.text_input("Email", placeholder="creator@example.com")
            col_phone, col_niche, col_lang = st.columns(3)
            with col_phone:
                phone = st.text_input("Phone", placeholder="+91...")
            with col_niche:
                primary_niche = st.selectbox("Primary niche", NICHES, index=0)
            with col_lang:
                primary_language = st.selectbox("Primary language", LANGUAGES, index=0)
            notes = st.text_area("Notes", placeholder="Optional notes about this creator")
            submitted = st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True)
            if submitted and name and email:
                creator = Creator(
                    id=str(uuid.uuid4()),
                    name=name,
                    email=email,
                    phone=phone or None,
                    primary_niche=primary_niche,
                    primary_language=primary_language,
                    notes=notes or None,
                    status=CreatorStatus.PENDING,
                )
                cs.add(creator)
                st.session_state.show_add_creator_toggle = False
                st.rerun()

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

            c1, c2, c3, c4, c5 = st.columns(5)
            if creator.status.value != "active":
                with c1:
                    if st.button("Activate", key=f"act_{creator.id}", icon=":material/check_circle:", use_container_width=True):
                        cs.update_status(creator.id, CreatorStatus.ACTIVE)
                        st.rerun()
            if creator.status.value != "inactive":
                with c2:
                    if st.button("Deactivate", key=f"deact_{creator.id}", icon=":material/pause_circle:", use_container_width=True):
                        cs.update_status(creator.id, CreatorStatus.INACTIVE)
                        st.rerun()
            if creator.status.value != "pending":
                with c3:
                    if st.button("Mark pending", key=f"pend_{creator.id}", icon=":material/schedule:", use_container_width=True):
                        cs.update_status(creator.id, CreatorStatus.PENDING)
                        st.rerun()
            with c4:
                if st.button("Edit", key=f"edit_{creator.id}", icon=":material/edit:", use_container_width=True):
                    st.session_state[f"editing_{creator.id}"] = not st.session_state.get(f"editing_{creator.id}", False)
                    st.rerun()
            with c5:
                if st.button("Delete", key=f"del_{creator.id}", icon=":material/delete:", use_container_width=True):
                    cs.delete(creator.id)
                    st.rerun()

        if st.session_state.get(f"editing_{creator.id}"):
            with st.container(border=True):
                st.markdown("**Edit creator**")
                with st.form(f"edit_form_{creator.id}"):
                    e_name = st.text_input("Name", value=creator.name)
                    e_email = st.text_input("Email", value=creator.email)
                    e_phone = st.text_input("Phone", value=creator.phone or "")
                    e_niche = st.selectbox("Primary niche", NICHES, index=NICHES.index(creator.primary_niche) if creator.primary_niche in NICHES else 0)
                    e_lang = st.selectbox("Primary language", LANGUAGES, index=LANGUAGES.index(creator.primary_language) if creator.primary_language in LANGUAGES else 0)
                    e_notes = st.text_area("Notes", value=creator.notes or "")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        saved = st.form_submit_button("Save", type="primary", icon=":material/save:", use_container_width=True)
                    with col_cancel:
                        cancelled = st.form_submit_button("Cancel", use_container_width=True)
                    if saved:
                        creator.name = e_name
                        creator.email = e_email
                        creator.phone = e_phone or None
                        creator.primary_niche = e_niche
                        creator.primary_language = e_lang
                        creator.notes = e_notes or None
                        cs.repo.save_all(cs.creators)
                        st.session_state[f"editing_{creator.id}"] = False
                        st.rerun()
                    if cancelled:
                        st.session_state[f"editing_{creator.id}"] = False
                        st.rerun()
