import json
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample_data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
CUSTOM_NICHES_FILE = SAMPLE_DATA_DIR / "custom_niches.json"
CUSTOM_LANGUAGES_FILE = SAMPLE_DATA_DIR / "custom_languages.json"

AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

MATCH_TOP_K = int(os.getenv("MATCH_TOP_K", "10"))
MATCH_RERANK_TOP_K = int(os.getenv("MATCH_RERANK_TOP_K", "5"))

REVIEW_NICHE_WEIGHT = 0.35
REVIEW_QUALITY_WEIGHT = 0.25
REVIEW_ENGAGEMENT_WEIGHT = 0.20
REVIEW_COMPLETENESS_WEIGHT = 0.10
REVIEW_LANGUAGE_WEIGHT = 0.10

MATCH_NICHE_WEIGHT = 0.30
MATCH_LANGUAGE_WEIGHT = 0.15
MATCH_REACH_WEIGHT = 0.10
MATCH_ENGAGEMENT_WEIGHT = 0.15
MATCH_QUALITY_WEIGHT = 0.15
MATCH_COMPLETENESS_WEIGHT = 0.05
MATCH_BUDGET_WEIGHT = 0.10

VERIFY_MIN_SCORE = 60
VERIFY_MIN_COMPLETENESS = 80

NICHES = [
    "Beauty & Makeup", "Fitness & Wellness", "Gaming", "Technology",
    "Food & Cooking", "Travel", "Parenting", "Business & Finance",
    "Fashion", "Music & Entertainment", "Education & Learning",
    "Automotive", "Skincare & Wellness", "Photography", "Home Decor",
    "Book Reviews & Literature", "Comedy & Entertainment", "Dance & Choreography",
    "Health & Wellness", "Lifestyle", "Spirituality & Yoga",
]

LANGUAGES = [
    "English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi",
    "Gujarati", "Kannada", "Malayalam", "Punjabi", "Urdu",
    "Bhojpuri", "Haryanvi", "Rajasthani", "Sanskrit", "Arabic",
    "French",
]


def _load_list(path: Path) -> list[str]:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def _save_list(path: Path, items: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(items, f, indent=2)


def load_custom_niches() -> list[str]:
    return _load_list(CUSTOM_NICHES_FILE)


def save_custom_niches(niches: list[str]):
    _save_list(CUSTOM_NICHES_FILE, niches)


def add_custom_niche(niche: str):
    niches = load_custom_niches()
    if niche and niche not in NICHES and niche not in niches:
        niches.append(niche)
        save_custom_niches(niches)


def remove_custom_niche(niche: str):
    niches = load_custom_niches()
    if niche in niches:
        niches.remove(niche)
        save_custom_niches(niches)


def get_all_niches() -> list[str]:
    return NICHES + load_custom_niches()


def load_custom_languages() -> list[str]:
    return _load_list(CUSTOM_LANGUAGES_FILE)


def save_custom_languages(langs: list[str]):
    _save_list(CUSTOM_LANGUAGES_FILE, langs)


def get_all_languages() -> list[str]:
    return LANGUAGES + load_custom_languages()
