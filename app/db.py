from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import IntegrityError

from typing import Iterable, TYPE_CHECKING
if TYPE_CHECKING:
    from app.models import Transaction

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "finance.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, 
                            autoflush=False,
                            autocommit=False,
                            future=True)

class Base(DeclarativeBase):
    pass

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

# inserts row into DB
# if a transaction already exists, skip

def save_transactions(transactions: Iterable[Transaction]) -> tuple[int, int]:
    inserted, skipped = 0, 0

    with SessionLocal() as session:
        for tx in transactions:
            session.add(tx)
            try:
                session.commit()
                inserted += 1
            except IntegrityError:
                session.rollback()
                skipped += 1
    
    return inserted, skipped