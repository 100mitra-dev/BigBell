import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Categorization", page_icon="🏷️", layout="wide")

from src.core.services.creator_service import CreatorService
from src.core.agents.categorization_agent import CategorizationAgent
from src.utils.display import section_header, status_badge


def load_data():
    if "creator_service" not in st.session_state:
        st.session_state.creator_service = CreatorService()
    return st.session_state.creator_service


cs = load_data()
categorizer = CategorizationAgent()

section_header("Creator Categorization", "AI-powered niche and language tagging")

tab1, tab2, tab3 = st.tabs(["Categorize Creators", "Niche Distribution", "Language Distribution"])

with tab1:
    creators_to_categorize = [c for c in cs.creators if c.status.value != "rejected"]

    selected = st.selectbox(
        "Select a creator to categorize",
        options=[(c.id, f"{c.name} ({c.primary_niche})") for c in creators_to_categorize],
        format_func=lambda x: x[1],
    )

    if selected:
        creator = cs.get_by_id(selected[0])
        if creator and st.button("Run AI Categorization", type="primary"):
            with st.spinner("Analyzing creator profile..."):
                result = categorizer.categorize(creator)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Niche Analysis")
                if "niche_scores" in result:
                    niche_df = pd.DataFrame(
                        list(result["niche_scores"].items()),
                        columns=["Niche", "Score"],
                    )
                    fig = px.bar(
                        niche_df, x="Score", y="Niche", orientation="h",
                        color="Score", color_continuous_scale="Blues",
                    )
                    fig.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown(f"**Primary Niche:** {result.get('primary_niche', 'N/A')}")
                if result.get("suggested_tags"):
                    st.markdown("**Suggested Tags:**")
                    tags = " ".join([f"`{t}`" for t in result["suggested_tags"]])
                    st.markdown(tags)

            with col2:
                st.subheader("Language Analysis")
                if "language_scores" in result:
                    lang_df = pd.DataFrame(
                        list(result["language_scores"].items()),
                        columns=["Language", "Score"],
                    )
                    fig = px.bar(
                        lang_df, x="Score", y="Language", orientation="h",
                        color="Score", color_continuous_scale="Greens",
                    )
                    fig.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown(f"**Primary Language:** {result.get('primary_language', 'N/A')}")
                st.markdown(f"**Tier:** {result.get('tier', 'N/A')}")

with tab2:
    dist = cs.get_niche_distribution()
    if dist:
        df = pd.DataFrame(list(dist.items()), columns=["Niche", "Count"])
        fig = px.bar(
            df, x="Count", y="Niche", orientation="h",
            color="Count", color_continuous_scale="Blues",
        )
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    lang_dist = cs.get_language_distribution()
    if lang_dist:
        df = pd.DataFrame(list(lang_dist.items()), columns=["Language", "Count"])
        fig = px.bar(
            df, x="Language", y="Count",
            color="Count", color_continuous_scale="Greens",
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
