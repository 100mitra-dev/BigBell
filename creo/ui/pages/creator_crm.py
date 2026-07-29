import streamlit as st
import uuid

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.services.payment_service import PaymentService
from creo.models import Creator, CreatorStatus
from creo.config import get_all_niches, LANGUAGES
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

PLATFORM_META = {
    "youtube": {"icon": ":material/smart_display:", "url": "https://youtube.com/@{handle}"},
    "instagram": {"icon": ":material/photo_camera:", "url": "https://instagram.com/{handle}"},
    "twitter": {"icon": ":material/tag:", "url": "https://x.com/{handle}"},
    "x": {"icon": ":material/tag:", "url": "https://x.com/{handle}"},
    "twitch": {"icon": ":material/videogame_asset:", "url": "https://twitch.tv/{handle}"},
    "tiktok": {"icon": ":material/music_video:", "url": "https://tiktok.com/@{handle}"},
    "linkedin": {"icon": ":material/business:", "url": "https://linkedin.com/in/{handle}"},
    "facebook": {"icon": ":material/thumb_up:", "url": "https://facebook.com/{handle}"},
}

st.title("Creator management")
st.caption("Manage and maintain creator records")

toolbar = st.columns([2, 1, 1, 1], vertical_alignment="bottom")
with toolbar[0]:
    q = st.text_input("Search", placeholder="Search by name, email, or niche...", label_visibility="collapsed")
with toolbar[1]:
    status_f = st.selectbox("Status", ["All", "active", "onboarding", "pending", "inactive", "rejected"], label_visibility="collapsed")
with toolbar[2]:
    all_niches = ["All"] + sorted(cs.get_niche_distribution().keys())
    niche_f = st.selectbox("Niche", all_niches, label_visibility="collapsed")
with toolbar[3]:
    l_all = ["All"] + sorted(cs.get_language_distribution().keys())
    lang_f = st.selectbox("Language", l_all, label_visibility="collapsed")

act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
with act_col1:
    add_btn = st.button("Add creator", use_container_width=True, icon=":material/add:")
with act_col2:
    import_btn = st.button("Import CSV", use_container_width=True, icon=":material/file_upload:")
with act_col3:
    csv_data = export_creators_to_csv(cs.creators)
    st.download_button("Export CSV", data=csv_data, file_name="creators.csv", mime="text/csv", use_container_width=True, icon=":material/file_download:")

if import_btn:
    st.session_state.show_import = not st.session_state.get("show_import", False)

if st.session_state.get("show_import"):
    imp = st.file_uploader("Import CSV", type="csv", key="csv_import")
    if imp:
        imported = import_creators_from_csv(imp.getvalue().decode("utf-8"))
        for c in imported:
            cs.add(c)
        st.session_state.show_import = False
        st.success(f"Imported {len(imported)} creators")
        st.rerun()

if add_btn:
    st.session_state.show_add_form = True
if st.session_state.get("show_add_form"):
    with st.container(border=True):
        st.markdown("**New creator**")
        with st.form("add_creator_form"):
            cols = st.columns(2)
            with cols[0]:
                n = st.text_input("Name", placeholder="e.g. Priya Sharma")
                e = st.text_input("Email", placeholder="priya@example.com")
                p = st.text_input("Phone", placeholder="+91 98765 43210", help="Include country code")
            with cols[1]:
                ni = st.selectbox("Primary niche", get_all_niches())
                la = st.selectbox("Primary language", LANGUAGES)
                no = st.text_area("Notes", placeholder="Additional notes about this creator")
            c1, c2 = st.columns(2)
            with c1:
                saved = st.form_submit_button("Save", type="primary", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
            if saved:
                if n and e:
                    creator = Creator(
                        id=str(uuid.uuid4()), name=n, email=e, phone=p or None,
                        primary_niche=ni, primary_language=la, notes=no or None,
                        status=CreatorStatus.PENDING,
                    )
                    cs.add(creator)
                    st.session_state.show_add_form = False
                    st.rerun()
            if cancelled:
                st.session_state.show_add_form = False
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

st.caption(f"**{len(creators)}** creator(s)")

for creator in creators:
    with st.container(border=True):
        row = st.columns([2, 1.5, 1, 1], vertical_alignment="center")
        with row[0]:
            st.markdown(f"**{creator.name}** :material/{'verified' if creator.verified else 'help'}: *{creator.tier}*")
            st.markdown(f":material/mail: {creator.email}  \n:material/label: {creator.primary_niche} · :material/translate: {creator.primary_language}")

        with row[1]:
            if creator.platforms:
                lines = []
                for plat, info in creator.platforms.items():
                    meta = PLATFORM_META.get(plat.lower())
                    if meta:
                        url = meta["url"].replace("{handle}", info.handle)
                        label = "subscribers" if plat.lower() == "youtube" else "followers"
                        lines.append(f"{meta['icon']} [{info.handle}]({url}) — {info.followers:,} {label}")
                    else:
                        lines.append(f":material/link: {info.handle} — {info.followers:,} followers")
                st.markdown("  \n".join(lines))
            else:
                st.caption("No social platforms")

        new_status = row[2].selectbox(
            "Status",
            ["active", "pending", "onboarding", "inactive", "rejected"],
            index=["active", "pending", "onboarding", "inactive", "rejected"].index(creator.status.value),
            key=f"st_{creator.id}",
            label_visibility="collapsed",
        )
        if new_status != creator.status.value:
            cs.update_status(creator.id, CreatorStatus(new_status))
            st.rerun()

        with row[3]:
            if st.button("Edit", key=f"e_{creator.id}", use_container_width=True):
                st.session_state[f"ed_{creator.id}"] = not st.session_state.get(f"ed_{creator.id}", False)
                st.rerun()
            if st.button("Del", key=f"d_{creator.id}", use_container_width=True):
                cs.delete(creator.id)
                st.rerun()

        st.markdown(
            f":material/people: {creator.total_followers:,} · "
            f":material/timeline: {creator.avg_engagement_rate}% · "
            f":material/star: {creator.content_quality_score}/10 · "
            f":material/checklist: {creator.profile_completeness}% complete · "
            f":material/campaign: {creator.total_campaigns_completed} campaigns"
        )

    if st.session_state.get(f"ed_{creator.id}"):
        with st.container(border=True):
            ec = st.columns(3)
            with ec[0]:
                en = st.text_input("Name", value=creator.name, key=f"en_{creator.id}")
                ee = st.text_input("Email", value=creator.email, key=f"ee_{creator.id}")
            with ec[1]:
                ep = st.text_input("Phone", value=creator.phone or "", key=f"ep_{creator.id}")
                eni = st.selectbox("Niche", get_all_niches(), index=get_all_niches().index(creator.primary_niche) if creator.primary_niche in get_all_niches() else 0, key=f"eni_{creator.id}")
            with ec[2]:
                ela = st.selectbox("Language", LANGUAGES, index=LANGUAGES.index(creator.primary_language) if creator.primary_language in LANGUAGES else 0, key=f"ela_{creator.id}")
                eno = st.text_area("Notes", value=creator.notes or "", key=f"eno_{creator.id}")
            csav, ccancel = st.columns(2)
            with csav:
                if st.button("Save", type="primary", use_container_width=True, key=f"es_{creator.id}"):
                    creator.name = en
                    creator.email = ee
                    creator.phone = ep or None
                    creator.primary_niche = eni
                    creator.primary_language = ela
                    creator.notes = eno or None
                    cs.repo.save_all(cs.creators)
                    st.session_state[f"ed_{creator.id}"] = False
                    st.rerun()
            with ccancel:
                if st.button("Cancel", use_container_width=True, key=f"ec_{creator.id}"):
                    st.session_state[f"ed_{creator.id}"] = False
                    st.rerun()

    with st.expander("Platforms, campaigns & payments", icon=":material/expand_more:"):
        cx = st.columns(3)
        with cx[0]:
            st.markdown("**Platforms**")
            if creator.platforms:
                for plat, info in creator.platforms.items():
                    v = ":material/check_circle:" if info.verified else ":material/cancel:"
                    meta = PLATFORM_META.get(plat.lower())
                    if meta:
                        url = meta["url"].replace("{handle}", info.handle)
                        st.markdown(f"- {meta['icon']} **{plat.title()}**: [{info.handle}]({url}) ({info.followers:,}) {v}")
                    else:
                        st.markdown(f"- :material/link: **{plat.title()}**: {info.handle} ({info.followers:,}) {v}")
            else:
                st.caption("No platforms linked")
        with cx[1]:
            st.markdown("**Campaigns**")
            cc = [c for c in cams.campaigns if creator.id in c.assigned_creators]
            if cc:
                for c in cc:
                    st.markdown(f"- **{c.title}** ({c.brand}) — {c.status}")
            else:
                st.caption("No campaign history")
        with cx[2]:
            st.markdown("**Payments**")
            cp = ps.get_for_creator(creator.id)
            if cp:
                for p in cp:
                    st.markdown(f"- ₹{p.amount:,.0f} — {p.status} — Due: {p.due_date}")
            else:
                st.caption("No payment history")
        if creator.notes:
            st.caption(f":material/note: {creator.notes}")
