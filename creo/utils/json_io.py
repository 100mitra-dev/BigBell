import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: no flock; rely on atomic rename only
    fcntl = None

from creo.models import Creator, Campaign, Application, FAQ, Payment
from creo.config import SAMPLE_DATA_DIR


def _path(filename: str) -> Path:
    return SAMPLE_DATA_DIR / filename


def _read_json_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


@contextmanager
def _locked(path: Path, mode: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode) as f:
        if fcntl is not None:
            op = fcntl.LOCK_EX if "w" in mode or "+" in mode else fcntl.LOCK_SH
            fcntl.flock(f.fileno(), op)
        try:
            yield f
        finally:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def load_json_list(filename: str) -> list[dict]:
    """Generic list loader (alias of load_json for repository use)."""
    return load_json(filename)


def save_json_list(filename: str, data: list[dict]):
    """Generic list saver (alias of save_json for repository use)."""
    save_json(filename, data)


def load_json(filename: str) -> list[dict]:
    path = _path(filename)
    if not path.exists():
        return []
    if fcntl is None:
        return _read_json_file(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with _locked(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json(filename: str, data: list[dict]):
    path = _path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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
