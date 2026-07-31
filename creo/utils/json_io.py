import json

from creo.models import Creator, Campaign, Application, FAQ, Payment
from creo.config import SAMPLE_DATA_DIR


def load_json(filename: str) -> list[dict]:
    path = SAMPLE_DATA_DIR / filename
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def save_json(filename: str, data: list[dict]):
    path = SAMPLE_DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_creators() -> list[Creator]:
    data = load_json("creators.json")
    return [Creator(**d) for d in data]


def save_creators(creators: list[Creator]):
    save_json("creators.json", [c.model_dump() for c in creators])


def load_campaigns() -> list[Campaign]:
    data = load_json("campaigns.json")
    return [Campaign(**d) for d in data]


def load_applications() -> list[Application]:
    data = load_json("applications.json")
    return [Application(**d) for d in data]


def save_applications(applications: list[Application]):
    save_json("applications.json", [a.model_dump() for a in applications])


def load_faqs() -> list[FAQ]:
    data = load_json("faq.json")
    return [FAQ(**d) for d in data]


def load_payments() -> list[Payment]:
    data = load_json("payments.json")
    return [Payment(**d) for d in data]
