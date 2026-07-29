import streamlit as st


def creator_avatar(name: str, size: int = 56):
    initial = name.split()[0][0].upper() if name else "?"
    st.html(
        f"""<div style="
            width:{size}px;height:{size}px;border-radius:50%;
            background:linear-gradient(135deg,#1E88E5,#1565C0);
            display:flex;align-items:center;justify-content:center;
            font-size:{size//2}px;font-weight:700;color:white;
            flex-shrink:0;
        ">{initial}</div>"""
    )


def creator_card(creator, compact: bool = False):
    with st.container(border=True):
        col1, col2 = st.columns([1, 4])
        with col1:
            creator_avatar(creator.name)
        with col2:
            st.markdown(f"**{creator.name}**")
            st.caption(f"{creator.primary_niche} | {creator.primary_language}")
            if not compact:
                m = st.columns(4)
                m[0].metric("Followers", f"{creator.total_followers:,}")
                m[1].metric("Engagement", f"{creator.avg_engagement_rate}%")
                m[2].metric("Quality", f"{creator.content_quality_score}/10")
                m[3].metric("Completeness", f"{creator.profile_completeness}%")


def empty_state(message: str):
    st.info(message, icon=":material/info:")
