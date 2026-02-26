from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select, func
from datetime import datetime, time, timedelta, date

from app.db import SessionLocal
from app.models import Transaction
from app import queries

st.set_page_config(page_title="Commbank Finance Tracker", layout="wide")
st.title("Finance Tracker")

@st.cache_data
def load_summary(start: date, end: date):
    return queries.get_summary(start, end)


@st.cache_data
def load_monthly(start: date, end: date):
    return queries.get_monthly_totals(start, end)


@st.cache_data
def load_recent(start: date, end: date, limit: int = 50):
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

    return pd.DataFrame(
        rows, columns=["date", "amount", "description", "cumulative_balance"]
    )

@st.cache_data
def get_date_bounds() -> tuple[date | None, date | None]:
    return queries.get_date_bounds()


min_d, max_d = get_date_bounds()

if min_d is None or max_d is None:
    st.warning("No transactions found in the database yet.")
    st.stop()

st.sidebar.header("Filters")
start_date, end_date = st.sidebar.date_input(
    "Date range",
    value=(min_d, max_d),
    min_value=min_d,
    max_value=max_d,
)

if isinstance(start_date, date) and not isinstance(end_date, date):
    end_date = start_date

income, expenses, net = load_summary(start_date, end_date)
monthly_df = load_monthly(start_date, end_date)
recent_df = load_recent(start_date, end_date, limit=50)


c1, c2, c3 = st.columns(3)
c1.metric("Total income", f"${income:,.2f}")
c2.metric("Total expenses", f"${abs(expenses):,.2f}")
c3.metric("Net change", f"${net:,.2f}")

st.divider()

st.subheader("Monthly net total")
st.line_chart(monthly_df.set_index("month")["total"])

st.divider()

st.subheader("Recent transactions")
st.dataframe(recent_df, use_container_width=True)
