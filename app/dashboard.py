from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import date

from app import queries, core

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
    return queries.get_transactions(start, end, limit=limit)


@st.cache_data
def load_all(start: date, end: date) -> pd.DataFrame:
    return core.add_categories(queries.get_transactions(start, end))


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
all_df = load_all(start_date, end_date)
recent_df = core.add_categories(load_recent(start_date, end_date, limit=50))

c1, c2, c3 = st.columns(3)
c1.metric("Total income", f"${income:,.2f}")
c2.metric("Total expenses", f"${abs(expenses):,.2f}")
c3.metric("Net change", f"${net:,.2f}")

st.divider()

st.subheader("Monthly net total")
st.line_chart(monthly_df.set_index("month")["total"])

st.divider()

st.subheader("Spending by category")
spending_df = core.spending_by_category(all_df)
st.bar_chart(spending_df.set_index("category")["total"])

st.divider()

# --- What changed vs previous period ---
prev_start, prev_end = core.previous_window(start_date, end_date)
prev_df = load_all(prev_start, prev_end)
deltas_df = core.category_deltas(all_df, prev_df)

st.subheader("What changed vs previous period")
st.caption(f"Comparing {start_date} – {end_date} against {prev_start} – {prev_end}")

increases = deltas_df[deltas_df["delta"] > 0].head(5).copy()
decreases = deltas_df[deltas_df["delta"] < 0].tail(5).copy()

increases["change"] = increases["delta"].apply(lambda x: f"+${x:,.2f}")
decreases["change"] = decreases["delta"].apply(lambda x: f"-${abs(x):,.2f}")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Top increases**")
    st.dataframe(
        increases[["category", "change"]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
with col2:
    st.markdown("**Top decreases**")
    st.dataframe(
        decreases[["category", "change"]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

st.subheader("Recent transactions")
st.dataframe(recent_df, use_container_width=True)
