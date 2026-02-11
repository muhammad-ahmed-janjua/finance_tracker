from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "db" / "finance.db"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DB_PATH = "data/db/finance.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, future=True, echo=False)

SessionLocal = sessionmaker(bind=engine, 
                            autoflush=False,
                            autocommit=False,
                            future=True)

class Base(DeclarativeBase):
    pass

def init_db() -> None:
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)