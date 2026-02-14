from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select, func

from app.db import SessionLocal
from app.models import Transaction

st.set_page_config(page_title="Commbank Finance Tracker", layout="wide")
st.title("Finance Tracker")


@st.cache_data
def load_summary():
    with SessionLocal() as session:
        income = session.scalar(
            select(func.sum(Transaction.amount)).where(Transaction.amount > 0)
        ) or 0.0

        expenses = session.scalar(
            select(func.sum(Transaction.amount)).where(Transaction.amount < 0)
        ) or 0.0

        net = income + expenses
        return float(income), float(expenses), float(net)


@st.cache_data
def load_monthly():
    with SessionLocal() as session:
        stmt = (
            select(
                func.strftime("%Y-%m", Transaction.date).label("month"),
                func.sum(Transaction.amount).label("total"),
            )
            .group_by("month")
            .order_by("month")
        )
        rows = session.execute(stmt).all()

    df = pd.DataFrame(rows, columns=["month", "total"])
    return df


@st.cache_data
def load_recent(limit: int = 25):
    with SessionLocal() as session:
        stmt = (
            select(
                Transaction.date,
                Transaction.amount,
                Transaction.description_raw,
                Transaction.cumulative_balance,
            )
            .order_by(Transaction.date.desc())
            .limit(limit)
        )
        rows = session.execute(stmt).all()

    return pd.DataFrame(
        rows, columns=["date", "amount", "description", "cumulative_balance"]
    )


income, expenses, net = load_summary()

c1, c2, c3 = st.columns(3)
c1.metric("Total income", f"${income:,.2f}")
c2.metric("Total expenses", f"${abs(expenses):,.2f}")
c3.metric("Net change", f"${net:,.2f}")

st.divider()

monthly_df = load_monthly()
st.subheader("Monthly net total")
st.line_chart(monthly_df.set_index("month")["total"])

st.divider()

st.subheader("Recent transactions")
st.dataframe(load_recent(50), use_container_width=True)