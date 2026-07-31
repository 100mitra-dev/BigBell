import logging
import uuid

import streamlit as st

from creo.agents.extraction import (
    CreatorExtractionAgent,
    REQUIRED_FIELD_LABELS,
    extract_pdf_text,
    missing_required_fields,
)
from creo.config import get_all_languages, get_all_niches
from creo.models import Creator, CreatorStatus, PlatformInfo
from creo.services.creator_service import CreatorService
from creo.ui.components.platforms import handle_display, platform_follower_label, platform_icon

logger = logging.getLogger(__name__)

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "extractor" not in st.session_state:
    st.session_state.extractor = CreatorExtractionAgent()
cs = st.session_state.cs
extractor = st.session_state.extractor

AI_WIDGET_KEYS = [
    "ai_name", "ai_email", "ai_phone", "ai_niche", "ai_lang",
    "ai_sec_niches", "ai_sec_langs", "ai_notes",
]


def _clear_ai_widgets():
    for key in AI_WIDGET_KEYS:
        st.session_state.pop(key, None)


def _clear_missing_dialog():
    st.session_state.pop("ai_missing_open", None)


@st.dialog("Missing details", width="small", on_dismiss=_clear_missing_dialog)
def missing_details_dialog():
    missing = st.session_state.get("ai_missing", [])
    st.write("These required details could not be extracted. Fill them in below before creating the creator.")
    for field in missing:
        st.warning(REQUIRED_FIELD_LABELS.get(field, field))
    if st.button("I'll fill them in", type="primary", icon=":material/manual_edit:", width="stretch", key="ai_missing_ok"):
        st.session_state.pop("ai_missing_open", None)
        st.rerun()


def _render_preview(parsed: dict):
    missing = missing_required_fields(parsed)
    if missing:
        st.info("A few details are missing — fill them in before creating the creator.")

    st.markdown("**Extracted details**")
    with st.container(border=True):
        niches = get_all_niches()
        languages = get_all_languages()
        primary_niche = parsed.get("primary_niche") or ""
        primary_language = parsed.get("primary_language") or ""
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name", value=parsed.get("name") or "", key="ai_name")
            email = st.text_input("Email", value=parsed.get("email") or "", key="ai_email")
            phone = st.text_input("Phone", value=parsed.get("phone") or "", key="ai_phone")
        with c2:
            niche = st.selectbox(
                "Primary niche",
                niches,
                index=niches.index(primary_niche) if primary_niche in niches else 0,
                key="ai_niche",
            )
            language = st.selectbox(
                "Primary language",
                languages,
                index=languages.index(primary_language) if primary_language in languages else 0,
                key="ai_lang",
            )
            sec_niches = st.multiselect(
                "Secondary niches",
                niches,
                default=[n for n in parsed.get("secondary_niches", []) if n in niches],
                key="ai_sec_niches",
            )
            sec_languages = st.multiselect(
                "Secondary languages",
                languages,
                default=[l for l in parsed.get("secondary_languages", []) if l in languages],
                key="ai_sec_langs",
            )
        notes = st.text_area("Notes", value=parsed.get("notes") or "", key="ai_notes")

    platforms = parsed.get("platforms") or {}
    if platforms:
        st.markdown("**Platforms**")
        with st.container(border=True):
            for platform, info in platforms.items():
                info = info if isinstance(info, dict) else getattr(info, "handle", None)
                if not isinstance(info, dict):
                    continue
                handle = info.get("handle", "")
                followers = int(info.get("followers") or 0)
                st.caption(
                    f"{platform_icon(platform)} **{platform.title()}**: {handle_display(handle)} — "
                    f"{followers:,} {platform_follower_label(platform)}"
                )

    if st.button("Create creator", type="primary", icon=":material/person_add:", width="stretch", key="ai_create_btn"):
        errors = []
        if not name.strip():
            errors.append("Name is required")
        if not email.strip() or "@" not in email:
            errors.append("A valid email is required")
        if not niche:
            errors.append("Primary niche is required")
        if not language:
            errors.append("Primary language is required")
        if errors:
            for error in errors:
                st.warning(error)
            return
        creator = Creator(
            id=str(uuid.uuid4()),
            name=name.strip(),
            email=email.strip(),
            phone=phone.strip() or None,
            primary_niche=niche,
            secondary_niches=sec_niches,
            primary_language=language,
            secondary_languages=sec_languages,
            platforms={
                platform: PlatformInfo(**info)
                for platform, info in platforms.items()
                if isinstance(info, dict) and info.get("handle")
            },
            notes=notes.strip() or None,
            status=CreatorStatus.PENDING,
        )
        cs.add(creator)
        st.session_state.pop("ai_parsed", None)
        st.session_state.pop("ai_missing", None)
        _clear_ai_widgets()
        st.toast(f"Creator {creator.name} added")
        st.rerun()


st.title("Add creator with AI")
st.caption("Paste a raw note, a WhatsApp message, or a PDF — Creo extracts the profile details and creates the creator record.")

try:
    mode = st.segmented_control(
        "Source",
        options=["Text", "PDF"],
        default="Text",
        key="ai_add_mode",
    )

    with st.container(border=True):
        st.markdown("**Profile source**")
        text_input = ""
        pdf_bytes = None
        if mode == "Text":
            text_input = st.text_area(
                "Profile text",
                placeholder=(
                    "Paste any raw text about the creator — a note, a WhatsApp message, a bio.\n\n"
                    "Example: Hi, I'm Priya Sharma from Mumbai. My Instagram @priyabeauty has 125k followers. "
                    "I create beauty & makeup content in Hindi and English. "
                    "Contact priya.sharma@email.com or +91 98765 43210."
                ),
                key="ai_add_text",
            )
        else:
            uploaded = st.file_uploader("Upload a PDF", type="pdf", key="ai_add_pdf")
            if uploaded:
                pdf_bytes = uploaded.getvalue()
        parse_btn = st.button("Parse and extract", type="primary", icon=":material/travel_explore:", width="stretch", key="ai_parse_btn")

    if parse_btn:
        text = ""
        if mode == "Text":
            text = (text_input or "").strip()
        else:
            if not pdf_bytes:
                st.warning("Please upload a PDF first.")
            else:
                try:
                    text = extract_pdf_text(pdf_bytes).strip()
                except Exception as e:
                    logger.exception("PDF text extraction failed")
                    st.error(f"Could not read the PDF: {e}")
        if text:
            with st.spinner("Extracting creator details..."):
                parsed = extractor.parse_text(text)
            _clear_ai_widgets()
            st.session_state.ai_parsed = parsed
            st.session_state.ai_missing = missing_required_fields(parsed)
            if st.session_state.ai_missing:
                st.session_state.ai_missing_open = True
            st.rerun()

    if st.session_state.get("ai_missing_open"):
        missing_details_dialog()

    if st.session_state.get("ai_parsed"):
        _render_preview(st.session_state.ai_parsed)

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in add creator")
