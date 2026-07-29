import streamlit as st

from creo.agents.query_agent import QueryAgent
from creo.utils.helpers import load_faqs

if "query_agent" not in st.session_state:
    st.session_state.query_agent = QueryAgent()
agent = st.session_state.query_agent

faqs = load_faqs()

st.title("Creator queries")
st.caption("AI-powered FAQ assistant with knowledge base search")

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("FAQ categories")
    categories = sorted(set(f.category for f in faqs))
    selected_cat = st.segmented_control("Filter by category", ["All"] + categories, label_visibility="collapsed")

    filtered = faqs if selected_cat == "All" or not selected_cat else [f for f in faqs if f.category == selected_cat]
    st.caption(f"{len(filtered)} articles available")

    for faq in filtered:
        with st.expander(faq.question, icon=":material/help:"):
            st.write(faq.answer)
            st.caption(f"Category: {faq.category}")

with col1:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources", icon=":material/article:"):
                    for s in msg["sources"]:
                        st.caption(f":material/description: {s.get('question', 'Unknown')} ({s.get('category', 'General')})")

    if prompt := st.chat_input("Ask about onboarding, payments, campaigns..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                cat = selected_cat if selected_cat and selected_cat != "All" else None
                result = agent.answer(prompt, category=cat)

            st.markdown(result["answer"])

            sources = result.get("sources", [])
            if sources:
                with st.expander("Sources", icon=":material/article:"):
                    for s in sources:
                        st.caption(f":material/description: {s.get('question', 'Unknown')} ({s.get('category', 'General')})")

            confidence = result.get("confidence", "low")
            if confidence == "high":
                st.caption(":material/check_circle: High confidence answer")
            elif confidence == "medium":
                st.caption(":material/timeline: Medium confidence — please verify")
            else:
                st.caption(":material/error: Low confidence — contact Creator Success team")

            st.session_state.chat_messages.append({
                "role": "assistant", "content": result["answer"], "sources": sources,
            })
