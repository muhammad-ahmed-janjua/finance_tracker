from __future__ import annotations

from datetime import date

from sqlalchemy import select, func

from app.db import SessionLocal
from app.models import Transaction


def get_date_bounds() -> tuple[date | None, date | None]:
    """Return (min_date, max_date) of all transactions in the DB."""
    with SessionLocal() as session:
        min_dt = session.scalar(select(func.min(Transaction.date)))
        max_dt = session.scalar(select(func.max(Transaction.date)))
    if min_dt is None or max_dt is None:
        return None, None
    return min_dt.date(), max_dt.date()
