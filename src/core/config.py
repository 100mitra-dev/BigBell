import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample_data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

MATCH_TOP_K = int(os.getenv("MATCH_TOP_K", "10"))
MATCH_RERANK_TOP_K = int(os.getenv("MATCH_RERANK_TOP_K", "5"))

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
