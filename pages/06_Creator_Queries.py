import streamlit as st

st.set_page_config(page_title="Creator Queries", page_icon="💬", layout="wide")

from src.core.agents.query_agent import QueryAgent
from src.utils.display import section_header
from src.utils.helpers import load_faqs


if "query_agent" not in st.session_state:
    st.session_state.query_agent = QueryAgent()

agent = st.session_state.query_agent
faqs = load_faqs()

section_header("Creator Query Assistant", "AI-powered FAQ answering with RAG")

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("FAQ Categories")
    categories = list(set(f.category for f in faqs))
    selected_category = st.selectbox("Filter by category", ["All"] + sorted(categories))

    if selected_category != "All":
        category_faqs = [f for f in faqs if f.category == selected_category]
    else:
        category_faqs = faqs

    st.subheader(f"Quick Questions ({len(category_faqs)})")
    for faq in category_faqs:
        with st.expander(faq.question):
            st.write(faq.answer)
            st.caption(f"Category: {faq.category}")

with col1:
    st.subheader("Ask a Question")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for s in msg["sources"]:
                        st.caption(f"📄 {s['question']} ({s['category']})")

    if prompt := st.chat_input("Ask a question about onboarding, payments, campaigns..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                cat_for_search = selected_category if selected_category != "All" else None
                result = agent.answer(prompt, category=cat_for_search)

            st.markdown(result["answer"])

            sources = result.get("sources", [])
            if sources:
                with st.expander("Sources"):
                    for s in sources:
                        st.caption(f"📄 {s.get('question', 'Unknown')} ({s.get('category', 'General')})")

            confidence = result.get("confidence", "medium")
            if confidence == "high":
                st.caption("✅ High confidence answer")
            elif confidence == "medium":
                st.caption("⚠️ Medium confidence — please verify")
            else:
                st.caption("❌ Low confidence — please contact Creator Success team for accurate information")

            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": sources,
            })
