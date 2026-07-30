import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

from creo.config import DATA_DIR

DB_PATH = DATA_DIR / "creo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = sa.create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


def drop_all():
    Base.metadata.drop_all(engine)
