import streamlit as st
import pandas as pd

from src.core.services.creator_service import CreatorService
from src.core.agents.categorization_agent import CategorizationAgent

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
cs = st.session_state.cs

categorizer = CategorizationAgent()

st.title("Categorization")
st.caption("AI-powered niche and language tagging for creators")

creators_pool = [c for c in cs.creators if c.status.value != "rejected"]

selected = st.selectbox(
    "Select a creator",
    options=[(c.id, f"{c.name} ({c.primary_niche})") for c in creators_pool],
    format_func=lambda x: x[1],
)

if selected:
    creator = cs.get_by_id(selected[0])
    if creator and st.button("Run AI categorization", type="primary", icon=":material/label:"):
        with st.spinner("Analyzing creator profile..."):
            result = categorizer.categorize(creator)
            st.session_state.cat_result = result

    result = st.session_state.get("cat_result")
    if result:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Niche analysis")
            if "niche_scores" in result:
                ndf = pd.DataFrame(list(result["niche_scores"].items()), columns=["Niche", "Score"])
                st.bar_chart(ndf, x="Niche", y="Score", horizontal=True)
            st.markdown(f"**Primary niche:** {result.get('primary_niche', 'N/A')}")
            if result.get("suggested_tags"):
                st.markdown("**Suggested tags:** " + ", ".join(f"`{t}`" for t in result["suggested_tags"]))

        with col2:
            st.subheader("Language analysis")
            if "language_scores" in result:
                ldf = pd.DataFrame(list(result["language_scores"].items()), columns=["Language", "Score"])
                st.bar_chart(ldf, x="Language", y="Score", horizontal=True)
            st.markdown(f"**Primary language:** {result.get('primary_language', 'N/A')}")
            st.markdown(f"**Tier:** {result.get('tier', 'N/A')}")
