import uuid

import streamlit as st

from creo.config import get_all_niches, get_all_languages, CONTENT_TYPES, AUDIENCE_TYPES, SORT_OPTIONS, PLATFORM_OPTIONS
from creo.models import Creator, CreatorStatus, PlatformInfo
from creo.services.creator_service import CreatorService
from creo.services.meta_discovery import DiscoveryFilters, live_discover, mock_discover
from creo.utils.runtime_settings import get_meta_api_key, get_meta_api_token
import logging

logger = logging.getLogger(__name__)

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
cs: CreatorService = st.session_state.cs

st.title("Discover creators")
st.caption("Find new creators via Meta creator discovery, filter by attributes, save to local database")

try:
    meta_key = get_meta_api_key() or st.session_state.get("meta_api_key", "")
    meta_token = get_meta_api_token() or st.session_state.get("meta_api_token", "")
    if not meta_key and not meta_token:
        st.warning("No Meta API key configured — showing mock results. Add one in Settings → Meta API.")
    else:
        st.success("Meta API key configured — live discovery enabled (falls back to mock on error).")

    with st.container(border=True):
        st.subheader("Search query")
        search_query = st.text_input("Search by name/handle/niche", placeholder="e.g. gaming, travel...", key="discovery_query")

        st.subheader("Filter criteria")
        c1, c2, c3 = st.columns(3)
        with c1:
            niche = st.selectbox("Niche", ["All"] + sorted(get_all_niches()), key="discovery_niche")
            language = st.selectbox("Language", ["All"] + sorted(get_all_languages()), key="discovery_lang")
        with c2:
            region = st.text_input("Region", placeholder="e.g. IN-MH, US, UK, BR", key="discovery_region")
            platform = st.selectbox("Platform", PLATFORM_OPTIONS, key="discovery_platform")
        with c3:
            min_f = st.number_input("Min followers", min_value=0, value=0, step=1000, key="discovery_minf")
            max_f = st.number_input("Max followers (0 = no limit)", min_value=0, value=0, step=1000, key="discovery_maxf")

        st.subheader("Advanced filters")
        c4, c5, c6 = st.columns(3)
        with c4:
            content_type = st.selectbox("Content type", CONTENT_TYPES, key="discovery_ct")
        with c5:
            audience_type = st.selectbox("Audience type", AUDIENCE_TYPES, key="discovery_at")
        with c6:
            sort_by = st.selectbox("Sort by", SORT_OPTIONS, key="discovery_sort")

        limit = st.slider("Max results", 5, 50, 20, key="discovery_limit")
        search = st.button("Discover", type="primary", icon=":material/travel_explore:", use_container_width=True)

        filters = DiscoveryFilters(
            niche="" if niche == "All" else niche,
            language="" if language == "All" else language,
            region=region.strip(),
            min_followers=int(min_f),
            max_followers=int(max_f),
            platform=platform,
            limit=int(limit),
            search_query=search_query.strip(),
            content_type=content_type,
            audience_type=audience_type,
            sort_by=sort_by,
        )

        if search or "discovery_results" not in st.session_state:
            try:
                if meta_key or meta_token:
                    st.session_state.discovery_results = live_discover(filters, meta_key, meta_token)
                    st.session_state.discovery_source = "live"
                else:
                    raise ValueError("no key")
            except Exception as e:
                logger.warning("Live discovery failed, using mock: %s", e)
                st.session_state.discovery_results = mock_discover(filters)
                st.session_state.discovery_source = "mock"

    results = st.session_state.get("discovery_results", [])
    st.caption(f"**{len(results)}** creator(s) found ({st.session_state.get('discovery_source', 'mock')} results)")

    existing_emails = {c.email.lower() for c in cs.creators}
    for i, d in enumerate(results):
        with st.container(border=True):
            top = st.columns([3, 1, 1])
            with top[0]:
                st.markdown(f"**{d.name}** ({d.handle}) {'✅' if d.verified else ''}")
                st.caption(f"{d.niche} · {d.language} · {d.region or 'any region'} · {d.platform}")
            with top[1]:
                st.metric("Followers", f"{d.followers:,}")
            with top[2]:
                st.metric("Engagement", f"{d.engagement_rate:.1f}%")
            if d.profile_url:
                st.link_button("Profile", d.profile_url)
            if d.handle.strip("@ ").lower().replace(".", "") + "@example.com" in existing_emails:
                st.info("Already in local database")
            else:
                if st.button("Save to database", key=f"save_disc_{i}", icon=":material/add:"):
                    email = f"{d.handle.strip('@ ').replace('.', '').lower()}@example.com"
                    cs.add(Creator(
                        id=str(uuid.uuid4()),
                        name=d.name,
                        email=email,
                        primary_niche=d.niche,
                        primary_language=d.language,
                        platforms={d.platform: PlatformInfo(handle=d.handle, followers=d.followers, verified=d.verified)},
                        avg_engagement_rate=d.engagement_rate,
                        status=CreatorStatus.PENDING,
                        region=d.region or None,
                        notes=f"Discovered via Meta ({d.region or 'any region'}). Profile: {d.profile_url}",
                    ))
                    st.success(f"Saved {d.name} to local database")
                    st.rerun()
except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in discovery")
