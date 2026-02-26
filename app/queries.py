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


def get_monthly_totals(start: date, end: date) -> "pd.DataFrame":
    """Return DataFrame[month: str, total: float] grouped by YYYY-MM, ordered ascending."""
    import pandas as pd

    start_dt = datetime.combine(start, time.min)
    end_dt_excl = datetime.combine(end + timedelta(days=1), time.min)

    with SessionLocal() as session:
        stmt = (
            select(
                func.strftime("%Y-%m", Transaction.date).label("month"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.date >= start_dt, Transaction.date < end_dt_excl)
            .group_by("month")
            .order_by("month")
        )
        rows = session.execute(stmt).all()

    return pd.DataFrame(rows, columns=["month", "total"])


def get_transactions(start: date, end: date, limit: int | None = None) -> "pd.DataFrame":
    """Return transactions in [start, end], newest first.
    Columns: date, amount, description, cumulative_balance."""
    import pandas as pd

    start_dt = datetime.combine(start, time.min)
    end_dt_excl = datetime.combine(end + timedelta(days=1), time.min)

    with SessionLocal() as session:
        stmt = (
            select(
                Transaction.date,
                Transaction.amount,
                Transaction.description_raw,
                Transaction.cumulative_balance,
            )
            .where(Transaction.date >= start_dt, Transaction.date < end_dt_excl)
            .order_by(Transaction.date.desc())
            .limit(limit)
        )
        rows = session.execute(stmt).all()

    return pd.DataFrame(rows, columns=["date", "amount", "description", "cumulative_balance"])


def get_all_summary() -> tuple[float, float, float]:
    """Return (income, expenses, net) across all transactions."""
    with SessionLocal() as session:
        income = session.scalar(
            select(func.sum(Transaction.amount)).where(Transaction.amount > 0)
        ) or 0.0

        expenses = session.scalar(
            select(func.sum(Transaction.amount)).where(Transaction.amount < 0)
        ) or 0.0

        net = income + expenses
        return float(income), float(expenses), float(net)


def get_all_monthly_totals() -> list:
    """Return list of (month, total) rows across all transactions, ordered ascending."""
    with SessionLocal() as session:
        stmt = (
            select(
                func.strftime("%Y-%m", Transaction.date).label("month"),
                func.sum(Transaction.amount).label("total"),
            )
            .group_by("month")
            .order_by("month")
        )
        return session.execute(stmt).all()


def get_all_transactions() -> list:
    """Return all transactions ordered by date ascending.
    Each row has: date, amount, description_raw, cumulative_balance."""
    with SessionLocal() as session:
        stmt = (
            select(
                Transaction.date,
                Transaction.amount,
                Transaction.description_raw,
                Transaction.cumulative_balance,
            )
            .order_by(Transaction.date)
        )
        return session.execute(stmt).all()
