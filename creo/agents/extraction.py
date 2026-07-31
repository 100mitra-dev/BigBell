import json
import logging
import re

from creo.agents.base import BaseAgent
from creo.config import get_all_languages, get_all_niches

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?[\d][\d\s\-().]{6,25}[\d]")
HANDLE_RE = re.compile(r"@([A-Za-z0-9][A-Za-z0-9_.]{1,29})")
FOLLOWER_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})*|\d+(?:\.\d+)?)\s*([kKmM]?)\s*(?:followers|follower|subs|subscribers|views)")
CAP_NAME = r"[A-Z][A-Za-z']+(?:\s+[A-Z][A-Za-z']+){0,2}"
NAME_RE = re.compile(rf"\b(?i:my name is|name[:：]|name is|i am|i'm|i’m|this is|call me)\s+({CAP_NAME})")

_NAME_STOP = {
    "i", "im", "am", "is", "a", "an", "the", "my", "me", "and", "from",
    "of", "in", "on", "with", "to", "for", "at", "by", "this", "hi", "hello",
    "email", "phone", "contact", "mobile", "handle", "niche", "language",
    "youtube", "instagram", "twitter", "address", "followers", "subscriber",
    "name", "based", "located",
}

PLATFORM_ALIASES = {
    "youtube": ("youtube", "youtu", "channel", "subscribe", "subscriber"),
    "instagram": ("instagram", "insta", "ig"),
    "twitter": ("twitter", "tweet", "x.com"),
    "tiktok": ("tiktok",),
    "linkedin": ("linkedin", "linked in"),
    "facebook": ("facebook", "fb"),
    "twitch": ("twitch",),
    "snapchat": ("snapchat", "snap"),
    "threads": ("threads",),
    "pinterest": ("pinterest", "pin"),
}

REQUIRED_FIELD_LABELS = {
    "name": "Name",
    "email": "Email",
    "primary_niche": "Primary niche",
    "primary_language": "Primary language",
}


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF file."""
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def missing_required_fields(parsed: dict) -> list[str]:
    missing = []
    if not parsed.get("name"):
        missing.append("name")
    if not parsed.get("email") or "@" not in str(parsed.get("email")):
        missing.append("email")
    if not parsed.get("primary_niche"):
        missing.append("primary_niche")
    if not parsed.get("primary_language"):
        missing.append("primary_language")
    return missing


def _first_match(pattern, text) -> str | None:
    m = pattern.search(text)
    if not m:
        return None
    return m.group(1) if m.lastindex else m.group(0)


def _clean_name(name: str) -> str:
    parts = []
    for word in name.split():
        token = word.lower().replace("'", "").replace("’", "")
        if token not in _NAME_STOP:
            parts.append(word)
    return " ".join(parts) or None


def _significant_terms(term: str) -> list[str]:
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", term) if len(w) > 3]
    return words or [term.lower()]


def _ordered_term_matches(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    hits = []
    for term in terms:
        sig = _significant_terms(term)
        if all(word in lower for word in sig):
            pos = min(lower.find(word) for word in sig)
            hits.append((pos, term))
    hits.sort(key=lambda x: x[0])
    return [term for _, term in hits]


def _normalize_phone(raw: str) -> str:
    return re.sub(r"[^\d+]", "", raw)


def _platform_for_context(context: str) -> str | None:
    best, best_score = None, 0
    for platform, aliases in PLATFORM_ALIASES.items():
        score = sum(1 for alias in aliases if re.search(rf"\b{re.escape(alias)}\b", context))
        if score > best_score:
            best, best_score = platform, score
    return best


class CreatorExtractionAgent(BaseAgent):
    """Extracts a creator profile from raw text (notes, WhatsApp messages, PDFs)."""

    def parse_text(self, raw_text: str) -> dict:
        if self.use_mock:
            return self._mock_parse_text(raw_text)
        logger.debug("AI parsing creator details from text")
        return self._ai_parse_text(raw_text)

    def _mock_parse_text(self, raw_text: str) -> dict:
        text = raw_text.strip()
        niches = _ordered_term_matches(text, get_all_niches())
        languages = _ordered_term_matches(text, get_all_languages())
        return {
            "name": self._extract_name(text),
            "email": _first_match(EMAIL_RE, text),
            "phone": self._extract_phone(text),
            "primary_niche": niches[0] if niches else "",
            "secondary_niches": niches[1:4],
            "primary_language": languages[0] if languages else "",
            "secondary_languages": languages[1:3],
            "platforms": self._extract_platforms(text),
            "notes": text or None,
        }

    def _ai_parse_text(self, raw_text: str) -> dict:
        prompt = f"""You are a data extraction agent for a creator management platform.

Extract the creator profile details from the raw text below. The text may be a note,
a WhatsApp message, a social media bio, or a resume. Use null for any detail that is not present.

Available niches: {', '.join(get_all_niches())}
Available languages: {', '.join(get_all_languages())}
Allowed platform keys: youtube, instagram, twitter, twitch, tiktok, linkedin, facebook, github, snapchat, threads, pinterest

Rules:
- Normalize primary_niche and primary_language to the closest value from the available lists (null if nothing matches).
- secondary_niches and secondary_languages are lists from the available lists (may be empty).
- platforms maps a platform key to {{"handle": "@...", "followers": int or 0, "verified": bool}}.
- notes keeps the raw text as-is.

Raw text:
\"\"\"
{raw_text}
\"\"\"

Return ONLY valid JSON with exactly this structure (no markdown, no commentary):
{{
  "name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "primary_niche": "string or null",
  "secondary_niches": ["string"],
  "primary_language": "string or null",
  "secondary_languages": ["string"],
  "platforms": {{"platform": {{"handle": "string", "followers": 0, "verified": false}}}},
  "notes": "string"
}}"""
        result = self._run_llm_chain(prompt)
        if result is None:
            return self._mock_parse_text(raw_text)
        try:
            data = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
            platforms = {}
            for key, value in (data.get("platforms") or {}).items():
                if isinstance(value, dict) and value.get("handle"):
                    try:
                        followers = int(value.get("followers") or 0)
                    except (TypeError, ValueError):
                        followers = 0
                    platforms[str(key)] = {
                        "handle": str(value["handle"]),
                        "followers": followers,
                        "verified": bool(value.get("verified")),
                    }
            return {
                "name": data.get("name") or None,
                "email": data.get("email") or None,
                "phone": data.get("phone") or None,
                "primary_niche": data.get("primary_niche") or "",
                "secondary_niches": list(data.get("secondary_niches") or []),
                "primary_language": data.get("primary_language") or "",
                "secondary_languages": list(data.get("secondary_languages") or []),
                "platforms": platforms,
                "notes": data.get("notes") or raw_text.strip() or None,
            }
        except Exception as e:
            logger.error("AI extraction failed, falling back to mock: %s", e)
            return self._mock_parse_text(raw_text)

    def _extract_name(self, text: str) -> str | None:
        m = NAME_RE.search(text)
        if m:
            return _clean_name(m.group(1))
        email = _first_match(EMAIL_RE, text)
        if email:
            local = email.split("@")[0]
            if "." in local and not re.search(r"\d", local):
                parts = [part.capitalize() for part in local.split(".") if part]
                if len(parts) >= 2:
                    return " ".join(parts[:2])
        return None

    def _extract_phone(self, text: str) -> str | None:
        m = PHONE_RE.search(text)
        if not m:
            return None
        phone = _normalize_phone(m.group(0))
        if sum(c.isdigit() for c in phone) < 10:
            return None
        return phone

    def _extract_platforms(self, text: str) -> dict:
        platforms = {}
        lower = text.lower()
        for m in HANDLE_RE.finditer(text):
            if m.start() > 0 and (text[m.start() - 1].isalnum() or text[m.start() - 1] in "._+-"):
                continue
            handle = "@" + m.group(1).rstrip(".")
            start = max(0, m.start() - 70)
            end = min(len(text), m.end() + 60)
            context = lower[start:end]
            platform = _platform_for_context(context)
            if not platform or platform in platforms:
                continue
            info = {
                "handle": handle,
                "followers": 0,
                "verified": bool(re.search(r"\b(?:verified|blue tick)\b", context)),
            }
            fm = FOLLOWER_RE.search(context)
            if fm:
                value = float(fm.group(1).replace(",", ""))
                suffix = fm.group(2).lower()
                if suffix == "k":
                    value *= 1_000
                elif suffix == "m":
                    value *= 1_000_000
                info["followers"] = int(value)
            platforms[platform] = info
        return platforms
