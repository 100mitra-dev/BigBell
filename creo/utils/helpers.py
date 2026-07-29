import json
from pathlib import Path
from datetime import datetime, date
from typing import Any

from creo.models import Creator, Campaign, Application, FAQ, Payment
from creo.config import SAMPLE_DATA_DIR


def load_json(filename: str) -> list[dict]:
    path = SAMPLE_DATA_DIR / filename
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_creators() -> list[Creator]:
    data = load_json("creators.json")
    return [Creator(**d) for d in data]


def load_campaigns() -> list[Campaign]:
    data = load_json("campaigns.json")
    return [Campaign(**d) for d in data]


def load_applications() -> list[Application]:
    data = load_json("applications.json")
    return [Application(**d) for d in data]


def load_faqs() -> list[FAQ]:
    data = load_json("faq.json")
    return [FAQ(**d) for d in data]


def load_payments() -> list[Payment]:
    data = load_json("payments.json")
    return [Payment(**d) for d in data]


def save_json(filename: str, data: list[dict]):
    path = SAMPLE_DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def save_creators(creators: list[Creator]):
    save_json("creators.json", [c.model_dump() for c in creators])


def save_applications(applications: list[Application]):
    save_json("applications.json", [a.model_dump() for a in applications])


def save_payments(payments: list[Payment]):
    save_json("payments.json", [p.model_dump() for p in payments])


def today_str() -> str:
    return date.today().isoformat()


def days_until(target_date: str) -> int:
    if not target_date:
        return 0
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    delta = target - date.today()
    return delta.days


def filter_by_status(items: list[Any], status: str) -> list[Any]:
    return [i for i in items if i.status == status]


def search_creators(creators: list[Creator], query: str) -> list[Creator]:
    q = query.lower()
    return [c for c in creators if q in c.name.lower() or q in c.primary_niche.lower() or q in c.primary_language.lower() or q in c.email.lower()]


def search_campaigns(campaigns: list[Campaign], query: str) -> list[Campaign]:
    q = query.lower()
    return [c for c in campaigns if q in c.title.lower() or q in c.brand.lower() or q in c.description.lower()]
