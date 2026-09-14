import streamlit as st
import random

from creo.models import Creator, CreatorStatus, PlatformInfo
from creo.config import get_all_niches, LANGUAGES
from creo.storage.api.meta_marketplace import MetaMarketplaceRepository
from creo.storage.api.modash import ModashCreatorRepository
from creo.storage.api.instagram_creators import InstagramCreatorRepository
from creo.storage.api.composite_creators import CompositeCreatorRepository
from creo.storage.json.creator_repo import JsonCreatorRepository
from creo.services.creator_service import CreatorService
from creo.ui.components.platforms import platform_icon, handle_display
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Discover Creators", page_icon=":material/search:")

st.title("Discover Creators")
st.caption("Find creators across Meta Marketplace, Modash.io, and Instagram. Results are deduplicated and merged into your unified creator database.")

try:

    # --- Strategy selectors ---
    strategy = st.segmented_control(
        "Discovery strategy",
        options=["Meta Marketplace", "Modash.io", "Instagram", "All sources (composite)"],
        default="All sources (composite)",
        label_visibility="collapsed",
        key="discover_strategy",
    )

    # --- Filters ---
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 1])
    with f_col1:
        niche_f = st.selectbox("Niche", ["All"] + get_all_niches(), index=0, label_visibility="collapsed")
    with f_col2:
        lang_f = st.selectbox("Language", ["All"] + LANGUAGES, index=0, label_visibility="collapsed")
    with f_col3:
        region_f = st.text_input("Region", placeholder="e.g. Mumbai, Delhi, Bangalore...", label_visibility="collapsed")
    with f_col4:
        min_followers = st.number_input("Min followers", min_value=0, value=0, step=1000, label_visibility="collapsed")

    # --- Discovery ---
    discover_btn = st.button("Run discovery", type="primary", icon=":material/search:")

    if discover_btn or st.session_state.get("discover_results") is not None:
        with st.spinner("Discovering creators..."):
            meta_repo = MetaMarketplaceRepository()
            modash_repo = ModashCreatorRepository()
            ig_repo = InstagramCreatorRepository()
            json_repo = JsonCreatorRepository()

            if strategy == "Meta Marketplace":
                repo = meta_repo
            elif strategy == "Modash.io":
                repo = modash_repo
            elif strategy == "Instagram":
                repo = ig_repo
            else:
                repo = CompositeCreatorRepository([json_repo, meta_repo, modash_repo, ig_repo])

            all_creators: list[Creator] = repo.list_all()

        # Apply filters
        if niche_f != "All":
            all_creators = [c for c in all_creators if c.primary_niche == niche_f or niche_f in c.secondary_niches]
            with b2:
                st.metric("From Meta Marketplace", len(meta_repo.list_all()))
            with b3:
                st.metric("From Modash.io", len(modash_repo.list_all()))
            st.caption(f"Instagram profile scans: {len(ig_repo.list_all())} | After deduplication: {len(all_creators)} total")

        st.session_state.discover_results = all_creators

        st.success(f"Found **{len(all_creators)}** creator(s)")

        # --- Source breakdown ---
        if strategy == "All sources (composite)":
            st.markdown("### Source breakdown")
            b1, b2, b3 = st.columns(3)
            with b1:
                local_count = len(json_repo.list_all())
                st.metric("Local database", local_count)
            with b2:
                st.metric("From Meta Marketplace", len(meta_repo.list_all()))
            with c3:
                pass
            with b3:
                st.metric("From Modash.io", len(modash_repo.list_all()))
            c4 = st.columns(1)[0]
            # Instagram count shown via Modash card or separate metric
            st.caption(f"Instagram profile scans: {len(ig_repo.list_all())} | After deduplication: {len(all_creators)} total")

        # --- Results grid ---
        st.markdown("### Results")
        if not all_creators:
            st.info("No creators found matching your filters. Try adjusting the search criteria.", icon=":material/info:")
        else:
            for creator in all_creators:
                with st.container(border=True):
                    cols = st.columns([1, 6, 2, 2])
                    with cols[0]:
                        avatar_seed = creator.name.replace(" ", "").lower()
                        st.image(f"https://api.dicebear.com/7.x/initials/svg?seed={avatar_seed}", width=60)
                    with cols[1]:
                        st.markdown(f"**{creator.name}**")
                        st.caption(f"{creator.primary_niche} \u00b7 {creator.primary_language}")
                        if creator.region:
                            st.caption(f":material/public: {creator.region}")
                        # Platform badges
                        badge_html = ""
                        for plat, info in creator.platforms.items():
                            icon = platform_icon(plat)
                            badge_html += f'<span style="display:inline-flex;align-items:center;background:#F3F4F6;border-radius:8px;padding:2px 8px;margin-right:6px;font-size:0.75rem">{icon} {handle_display(info.handle)} \u00b7 {info.followers:,}</span> '
                        st.markdown(badge_html, unsafe_allow_html=True)
                    with cols[2]:
                        tier = creator.tier
                        tier_colors = {
                            "Elite": "#7C3AED", "Pro": "#0284C7",
                            "Growth": "#10B981", "Rising": "#F59E0B",
                        }
                        color = tier_colors.get(tier, "#6B7280")
                        st.markdown(
                            f'<div style="text-align:center">'
                            f'<span style="background:{color}15;color:{color};padding:4px 14px;border-radius:12px;font-weight:700;font-size:0.85rem">{tier}</span>'
                            f'<div style="font-size:0.7rem;color:#6B7280;margin-top:4px">{creator.total_followers:,} followers</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with cols[3]:
                        eng = creator.avg_engagement_rate
                        eng_color = "green" if eng >= 5 else "orange" if eng >= 3 else "red"
                        st.markdown(
                            f'<div style="text-align:right">'
                            f'<span style="font-size:1.1rem;font-weight:700;color:{eng_color}">{eng}%</span>'
                            f'<div style="font-size:0.7rem;color:#6B7280">engagement</div>'
                            f'{f"<span style=\"font-size:0.7rem;color:#6B7280\">Q{creator.content_quality_score}/10</span>" if creator.content_quality_score else ""}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    # Expandable details
                    with st.expander("View details", icon=":material/info:"):
                        detail_cols = st.columns(4)
                        with detail_cols[0]:
                            st.metric("Engagement", f"{creator.avg_engagement_rate}%")
                        with detail_cols[1]:
                            st.metric("Quality score", f"{creator.content_quality_score}/10")
                        with detail_cols[2]:
                            st.metric("Profile complete", f"{creator.profile_completeness}%")
                        with detail_cols[3]:
                            st.metric("Campaigns done", creator.total_campaigns_completed)
                        if creator.total_earnings > 0:
                            st.metric("Total earnings", f"\u20B9{creator.total_earnings:,.0f}")
                        if creator.email:
                            st.markdown(f":material/mail: {creator.email}")
                        if creator.phone:
                            st.markdown(f":material/call: {creator.phone}")
                        if creator.notes:
                            st.markdown(f"**Notes:** {creator.notes}")
                        if creator.suggested_tags:
                            tag_html = " ".join(
                                f'<span style="background:#F1F5F9;color:#475569;padding:2px 10px;border-radius:8px;font-size:0.75rem;margin-right:4px">{t}</span>'
                                for t in creator.suggested_tags
                            )
                            st.markdown(f"**Tags:** {tag_html}", unsafe_allow_html=True)

                        # Action: import into local store
                        if strategy != "Meta Marketplace" and st.button(f"Import {creator.name}", key=f"import_{creator.id}"):
                            cs = CreatorService()
                            try:
                                cs.add(creator)
                                st.success(f"Imported **{creator.name}** into your creator database")
                                cs.refresh()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to import: {e}")

    # --- Import section ---
    if st.session_state.get("discover_results"):
        st.divider()
        st.markdown("### Bulk import")
        st.caption("Import all discovered creators into your local database. Existing creators are deduplicated automatically.")
        if st.button("Import all discovered creators", icon=":material/upload:", type="primary", use_container_width=True):
            cs = CreatorService()
            imported = 0
            for c in st.session_state.discover_results:
                if cs.get_by_id(c.id) is None:
                    cs.add(c)
                    imported += 1
            cs.refresh()
            st.success(f"Imported {imported} new creator(s) into the database")
            st.rerun()

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in discover_creators")
