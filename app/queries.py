from __future__ import annotations

from datetime import date, datetime, time, timedelta

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


def get_summary(start: date, end: date) -> tuple[float, float, float]:
    """Return (income, expenses, net) for [start, end] inclusive."""
    start_dt = datetime.combine(start, time.min)
    end_dt_excl = datetime.combine(end + timedelta(days=1), time.min)

    with SessionLocal() as session:
        income = session.scalar(
            select(func.sum(Transaction.amount))
            .where(Transaction.amount > 0)
            .where(Transaction.date >= start_dt, Transaction.date < end_dt_excl)
        ) or 0.0

        expenses = session.scalar(
            select(func.sum(Transaction.amount))
            .where(Transaction.amount < 0)
            .where(Transaction.date >= start_dt, Transaction.date < end_dt_excl)
        ) or 0.0

        net = income + expenses
        return float(income), float(expenses), float(net)
