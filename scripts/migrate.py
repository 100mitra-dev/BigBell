"""Thin CLI wrapper so `python scripts/migrate.py` works (delegates to creo.storage.db.migrate)."""
from creo.storage.db.migrate import migrate

if __name__ == "__main__":
    migrate()
