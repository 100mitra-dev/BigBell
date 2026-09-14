import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from creo.config import DATA_DIR

DB_PATH = DATA_DIR / "creo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"


def _configure_sqlite(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=5000")
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


engine = sa.create_engine(
    DATABASE_URL, echo=False, connect_args={"check_same_thread": False, "timeout": 30},
)
event.listen(engine, "connect", _configure_sqlite)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


def drop_all():
    Base.metadata.drop_all(engine)
