import streamlit as st

from creo.services.creator_service import CreatorService
from creo.agents.verification_agent import VerificationAgent
from creo.ui.components.cards import creator_card

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
cs = st.session_state.cs

verifier = VerificationAgent()

st.title("Verification")
st.caption("Automated profile and social media verification")

tab1, tab2 = st.tabs(["Pending verification", "All profiles"])

with tab1:
    pending = cs.filter_by_status("pending") + cs.filter_by_status("onboarding")
    if not pending:
        st.info("No creators pending verification.", icon=":material/verified:")
    else:
        for creator in pending[:10]:
            with st.container(border=True):
                creator_card(creator, compact=True)

                result_key = f"verify_result_{creator.id}"
                if st.button("Run verification", key=f"verify_{creator.id}", icon=":material/verified:"):
                    with st.spinner(f"Verifying {creator.name}..."):
                        st.session_state[result_key] = verifier.verify(creator)
                    st.rerun()

                result = st.session_state.get(result_key)
                if result:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Verification score", f'{result.get("overall_score", 0)}/100')
                        if result.get("verified"):
                            st.success(":material/check_circle: Verified")
                        else:
                            st.error(":material/cancel: Not verified")
                    with c2:
                        for issue in result.get("issues", []):
                            st.warning(issue, icon=":material/warning:")

                    cq = result.get("content_quality")
                    if cq:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Quality", f'{cq.get("score", 0)}/10')
                        c2.metric("Consistency", f'{cq.get("consistency", 0)}/10')
                        c3.metric("Originality", f'{cq.get("originality", 0)}/10')

                    with st.expander("Platform details", icon=":material/language:"):
                        for platform, pdata in result.get("platforms", {}).items():
                            st.write(f"**{platform.title()}**")
                            st.json(pdata)

                    if result.get("verified"):
                        if st.button(f"Approve {creator.name}", key=f"approve_{creator.id}", icon=":material/check:"):
                            cs.update_status(creator.id, "active")
                            st.success(f"{creator.name} approved and moved to active!")
                            st.rerun()

with tab2:
    q = st.text_input("Search creators", placeholder="Name, niche, or language...", label_visibility="collapsed")
    creators = cs.search(q) if q else cs.creators

    for creator in creators:
        with st.container(border=True):
            creator_card(creator)
            st.badge(creator.status.value, icon=":material/info:")
            if creator.platforms:
                with st.expander("Platform details", icon=":material/language:"):
                    for name, info in creator.platforms.items():
                        v = ":material/check_circle:" if info.verified else ":material/cancel:"
                        st.write(f"**{name.title()}**: {info.handle} | {info.followers:,} followers | {v}")
