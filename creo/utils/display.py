import streamlit as st


def metric_card(label: str, value: str, delta: str = None, help_text: str = None):
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="padding: 0.5rem;">
                <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.25rem;">{label}</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #1A1A2E;">{value}</div>
                {f'<div style="font-size: 0.8rem; color: {"#2ECC71" if delta and not delta.startswith("-") else "#E74C3C"}; margin-top: 0.25rem;">{delta}</div>' if delta else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if help_text:
            st.caption(help_text)


def creator_card(creator, compact: bool = False):
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            initial = creator.name.split()[0][0].upper()
            st.markdown(
                f"""
                <div style="width:60px;height:60px;border-radius:50%;background:#1E88E5;display:flex;align-items:center;justify-content:center;
                font-size:1.5rem;font-weight:700;color:white;">
                    {initial}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(f"**{creator.name}**  ")
            st.caption(f"{creator.primary_niche} | {creator.primary_language}")
            if not compact:
                cols = st.columns(4)
                cols[0].metric("Followers", f"{creator.total_followers:,}")
                cols[1].metric("Engagement", f"{creator.avg_engagement_rate}%")
                cols[2].metric("Quality", f"{creator.content_quality_score}/10")
                cols[3].metric("Completeness", f"{creator.profile_completeness}%")


def status_badge(status: str):
    colors = {
        "active": "#2ECC71",
        "inactive": "#95A5A6",
        "pending": "#F39C12",
        "onboarding": "#3498DB",
        "rejected": "#E74C3C",
        "accepted": "#2ECC71",
        "reviewed": "#3498DB",
        "shortlisted": "#F39C12",
        "paid": "#2ECC71",
        "processed": "#3498DB",
        "disputed": "#E74C3C",
    }
    color = colors.get(status.lower(), "#95A5A6")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;">{status}</span>'


def section_header(title: str, subtitle: str = None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()


def info_row(label: str, value: str):
    st.markdown(f"**{label}:** {value}")
