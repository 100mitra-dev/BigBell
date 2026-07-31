import streamlit as st

from creo.config import get_all_niches, LANGUAGES
from creo.rag.faq_kb import (
    FAQKnowledgeBase,
    generate_faq_pdf_bytes,
    parse_faq_pdf,
)
from creo.services.helpdesk_service import (
    HelpdeskService,
    DEMO_QUESTIONS,
    CHANNELS,
)
from creo.utils.json_io import load_faqs, load_json
from creo.services.creator_service import CreatorService
import logging

logger = logging.getLogger(__name__)

CHANNEL_META = {
    "whatsapp": (":material/call:", "WhatsApp"),
    "email": (":material/mail:", "Email"),
    "in_app": (":material/chat:", "In-app"),
}
CONFIDENCE_META = {
    "high": (":material/check_circle:", "High confidence"),
    "medium": (":material/timeline:", "Medium confidence"),
    "low": (":material/error:", "Low confidence"),
}

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "helpdesk" not in st.session_state:
    st.session_state.helpdesk = HelpdeskService()
cs = st.session_state.cs
svc = st.session_state.helpdesk


def creator_label(creator_id: str) -> str:
    creator = cs.get_by_id(creator_id)
    if not creator:
        return creator_id
    return f"{creator.name} \u00b7 {creator.primary_niche}"


def channel_tag(channel: str) -> str:
    icon, label = CHANNEL_META.get(channel, (":material/chat:", channel.title()))
    return f"{icon} {label}"


def message_caption(msg) -> str:
    icon, label = CHANNEL_META.get(msg.channel, (":material/chat:", msg.channel.title()))
    return f"{icon} {label} \u00b7 {msg.created_at[11:16]}"


def get_suggestions(pending_msg) -> list[str]:
    cache = st.session_state.setdefault("suggestions_cache", {})
    key = pending_msg.id
    if key not in cache:
        with st.spinner("Drafting AI reply suggestions..."):
            cache[key] = svc.suggest_replies(pending_msg.content, count=3)
    return cache[key]


def current_thread_id() -> str | None:
    selected = st.session_state.get("selected_thread")
    if selected and cs.get_by_id(selected):
        return selected
    thread_ids = svc.creator_ids()
    if thread_ids:
        return thread_ids[0]
    creators = cs.creators
    return creators[0].id if creators else None


st.title("Creator Helpdesk")
st.caption("Talk with creators over WhatsApp, email & in-app \u2014 auto-answers from the FAQ knowledge base")

stats = svc.stats()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Conversations", stats["threads"])
m2.metric("Unanswered", stats["pending"])
m3.metric("Auto-answered", stats["auto"])
m4.metric("FAQ articles", stats["faqs"])

inbox_tab, kb_tab = st.tabs([":material/inbox: Inbox", ":material/menu_book: Knowledge base"])

with inbox_tab:
    thread_ids = svc.creator_ids()
    if not thread_ids:
        st.info(
            "No conversations yet. Use the demo tools below to create a mock creator "
            "and send a question as them to see auto-answering in action.",
            icon=":material/emoji_people:",
        )

    left_col, right_col = st.columns([1, 2.2])

    with left_col:
        with st.container(border=True):
            st.markdown("**Demo tools**")
            with st.expander("Add mock creator", icon=":material/person_add:"):
                with st.form("mock_creator_form"):
                    name = st.text_input("Name", placeholder="e.g. Ananya Sharma")
                    email = st.text_input("Email", placeholder="ananya@example.com")
                    phone = st.text_input("Phone", placeholder="+91 98765 43210")
                    niche = st.selectbox("Primary niche", get_all_niches())
                    language = st.selectbox("Primary language", LANGUAGES)
                    if st.form_submit_button("Create & open thread", type="primary", use_container_width=True) and name:
                        creator = svc.create_mock_creator(name, email, phone, niche, language)
                        st.session_state.selected_thread = creator.id
                        st.success(f"Created mock creator **{creator.name}**")
                        st.rerun()

            with st.expander("Simulate incoming question", icon=":material/forum:"):
                target = current_thread_id()
                if not target:
                    st.caption("Create a mock creator first.")
                else:
                    st.caption(f"Will arrive as: **{creator_label(target)}**")
                    demo_q = st.selectbox("Sample question", DEMO_QUESTIONS, key="demo_q")
                    custom_q = st.text_input("...or type your own question", key="demo_custom_q")
                    demo_channel = st.pills("Channel", CHANNELS, default="whatsapp", key="demo_channel")
                    if st.button("Send as creator", icon=":material/send:", type="primary", use_container_width=True, key="send_demo_btn"):
                        question = custom_q.strip() or demo_q
                        result = svc.receive_question(target, question, demo_channel)
                        if result["auto_answered"]:
                            st.success("Auto-answered from knowledge base")
                        else:
                            st.warning("No strong FAQ match \u2014 reply manually below")
                        st.rerun()

        with st.container(border=True):
            st.markdown("**Threads**")
            if thread_ids:
                labels = {creator_label(cid): cid for cid in thread_ids}
                default_label = None
                selected = st.session_state.get("selected_thread")
                if selected and selected in labels.values():
                    default_label = next(l for l, cid in labels.items() if cid == selected)
                chosen = st.selectbox(
                    "Select creator",
                    options=list(labels.keys()),
                    index=list(labels.keys()).index(default_label) if default_label else 0,
                    key="thread_picker",
                    label_visibility="collapsed",
                )
                selected_thread = labels[chosen]
                st.session_state.selected_thread = selected_thread
                st.caption(f"Unanswered: {svc.pending_count(selected_thread)} \u00b7 "
                           f"{len(svc.thread(selected_thread))} messages")
            elif cs.creators:
                st.caption("No conversations yet \u2014 send a question with the demo tool to start one.")
            else:
                st.caption("No threads yet")

    with right_col:
        cid = current_thread_id()
        if cid:
            creator = cs.get_by_id(cid)
            with st.container(border=True):
                if creator:
                    st.markdown(f"### {creator.name}")
                    st.caption(
                        f"{channel_tag('email')} {creator.email} \u00b7 "
                        f"{channel_tag('whatsapp')} {creator.phone or 'n/a'} \u00b7 "
                        f"{creator.primary_niche}"
                    )
                else:
                    st.markdown(f"### {cid}")

                for msg in svc.thread(cid):
                    if msg.role == "creator":
                        with st.chat_message("user"):
                            st.markdown(msg.content)
                            st.caption(message_caption(msg))
                    else:
                        with st.chat_message("assistant"):
                            st.markdown(msg.content)
                            if msg.kind == "auto":
                                icon, label = CONFIDENCE_META.get(msg.confidence, CONFIDENCE_META["medium"])
                                st.markdown(
                                    f":material/bolt: **Auto-answered** \u00b7 "
                                    f"`{msg.faq_id or 'FAQ'}` \u00b7 {icon} {label}",
                                    help="Answered automatically from the FAQ knowledge base via embedding similarity.",
                                )
                            else:
                                st.markdown(":material/edit: **Manual reply**")
                            st.caption(message_caption(msg))

                st.divider()
                pending = svc.unanswered_question(cid)
                if pending:
                    with st.container(border=True):
                        st.markdown(f"**:material/schedule: Needs your reply** \u2014 {channel_tag(pending.channel)}")
                        suggestions = get_suggestions(pending)
                        if suggestions:
                            chosen = st.radio(
                                "Suggested replies",
                                suggestions,
                                key=f"sug_{pending.id}",
                                label_visibility="collapsed",
                            )
                            if st.button("Send selected reply", icon=":material/send:", type="primary", use_container_width=True, key=f"send_sug_{pending.id}"):
                                svc.send_reply(cid, chosen, pending.channel, kind="manual")
                                st.rerun()
                        custom = st.text_area("Or write your own reply", key=f"custom_{pending.id}", height=90)
                        if st.button("Send custom reply", icon=":material/send:", use_container_width=True, key=f"send_custom_{pending.id}") and custom.strip():
                            svc.send_reply(cid, custom.strip(), pending.channel, kind="manual")
                            st.rerun()
                else:
                    reply_channel = st.pills("Reply via", CHANNELS, default="whatsapp", key="reply_channel")
                    if prompt := st.chat_input("Message this creator..."):
                        svc.send_reply(cid, prompt, reply_channel, kind="manual")
                        st.rerun()
        else:
            st.info("Select a thread on the left to view the conversation.", icon=":material/inbox:")


with kb_tab:
    st.caption(
        "This page auto-answers creator questions by matching them against a Chroma-embedded "
        "knowledge base. Upload a PDF of FAQ Q&A pairs to grow it \u2014 the contents stay "
        "hidden from creators and visitors."
    )

    k1, k2, k3 = st.columns(3)
    kb = FAQKnowledgeBase()
    try:
        faq_total = kb.count()
        k1.metric("Indexed articles", faq_total)
        categories = kb.categories()
        k2.metric("Categories", len(categories))
        uploaded_count = len(load_json("faq_uploaded.json"))
        k3.metric("From uploaded PDFs", uploaded_count)
    except Exception as e:
        k1.metric("Indexed articles", 0)
        k2.metric("Categories", 0)
        k3.metric("From uploaded PDFs", 0)
        st.warning(f"Knowledge base not ready yet: {e}")

    if categories:
        chips = " ".join(
            f'<span style="background:#7C3AED15;color:#7C3AED;padding:2px 12px;border-radius:12px;'
            f'font-size:0.8rem;margin:0 4px 4px 0">{c}</span>'
            for c in categories
        )
        st.markdown(chips, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Upload FAQ PDF**")
        st.caption("Each entry must follow a `Q1: Question?` / `A: Answer` format (see the sample PDF).")
        uploaded = st.file_uploader("Choose a PDF file", type=["pdf"], key="faq_pdf_upload")
        if uploaded:
            try:
                faqs = parse_faq_pdf(uploaded.getvalue())
            except Exception as e:
                st.error(f"Could not parse the PDF: {e}")
            else:
                st.success(f"Parsed **{len(faqs)}** Q&A entries from **{uploaded.name}**")
                if st.button("Ingest into knowledge base", type="primary", icon=":material/library_add:", key="ingest_pdf"):
                    added = kb.add_uploaded_faqs(faqs)
                    if added:
                        st.success(f"Ingested {added} new entries. The knowledge base is now live for auto-answers.")
                        st.rerun()
                    else:
                        st.info("No new entries \u2014 everything in the PDF is already known.")
                        st.rerun()

    with st.container(border=True):
        st.markdown("**Sample FAQ PDF**")
        st.caption("Download a demo FAQ PDF (created from the bundled knowledge base) and re-upload it to test ingestion.")
        sample_bytes = generate_faq_pdf_bytes(load_faqs())
        st.download_button(
            "Download sample FAQ PDF",
            data=sample_bytes,
            file_name="sample_faq.pdf",
            mime="application/pdf",
            icon=":material/file_download:",
            key="sample_pdf",
        )
        if st.button("Rebuild index", icon=":material/refresh:", key="reindex_kb"):
            with st.spinner("Rebuilding embedding index..."):
                kb.reindex()
            st.success("Index rebuilt")
            st.rerun()
