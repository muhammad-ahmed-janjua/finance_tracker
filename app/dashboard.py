from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from app import core, queries

st.set_page_config(page_title="Commbank Finance Tracker", layout="wide")
st.title("Finance Tracker")

# Bump this whenever you change categorization logic in core.py.
# This forces Streamlit cache invalidation for cached dataframes that depend on core.add_categories().
CATEGORIZATION_VERSION = "v2-transfer-reason"


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
def load_all(start: date, end: date, version: str) -> pd.DataFrame:
    # version exists only to bust cache when categorization rules change
    df = queries.get_transactions(start, end)
    return core.add_categories(df)


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

exclude_transfers = st.sidebar.checkbox("Exclude transfers (True Spend)")

# Raw totals (always unfiltered)
income, expenses, net = load_summary(start_date, end_date)
monthly_df = load_monthly(start_date, end_date)

# Categorized dataframes (cache-busted by version key)
all_df = load_all(start_date, end_date, CATEGORIZATION_VERSION)
recent_df = core.add_categories(load_recent(start_date, end_date, limit=50))

# Insight dataframe used for: category spend, deltas, recurring commitments.
# IMPORTANT: when excluding transfers, filter by category, not by core.is_transfer(),
# so "Transfer ... Rent" can be categorized as Utilities and INCLUDED in true spend.
if exclude_transfers and not all_df.empty and "category" in all_df.columns:
    insight_df = all_df[all_df["category"] != "Transfer"].reset_index(drop=True)
else:
    insight_df = all_df

# --- Summary metrics ---
c1, c2, c3 = st.columns(3)
c1.metric("Total income", f"${income:,.2f}")
c2.metric("Total expenses", f"${abs(expenses):,.2f}")
c3.metric("Net change", f"${net:,.2f}")

st.divider()

# --- Monthly trend ---
st.subheader("Monthly net total")
st.line_chart(monthly_df.set_index("month")["total"])

st.divider()

# --- Spending by category ---
st.subheader("Spending by category")
spending_df = core.spending_by_category(insight_df)
st.bar_chart(spending_df.set_index("category")["total"])

st.divider()

# --- What changed vs previous period ---
prev_start, prev_end = core.previous_window(start_date, end_date)
prev_all_df = load_all(prev_start, prev_end, CATEGORIZATION_VERSION)

if exclude_transfers and not prev_all_df.empty and "category" in prev_all_df.columns:
    prev_insight_df = prev_all_df[prev_all_df["category"] != "Transfer"].reset_index(drop=True)
else:
    prev_insight_df = prev_all_df

deltas_df = core.category_deltas(insight_df, prev_insight_df)

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

# --- Recurring commitments ---
st.subheader("Recurring commitments")
commitments_df = core.detect_recurring_commitments(insight_df)

if commitments_df.empty:
    st.caption("No recurring commitments detected. Try a wider date range (3+ months recommended).")
else:
    display = commitments_df.copy()
    display["median_amount"] = display["median_amount"].apply(lambda x: f"${x:,.2f}")
    display["confidence"] = display["confidence"].apply(lambda x: f"{int(x * 100)}%")
    st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()

# --- Recent transactions ---
st.subheader("Recent transactions")
st.dataframe(recent_df, use_container_width=True)

# --- Debug: Transfer bucket breakdown ---
with st.expander("Debug: Transfer transactions (by description)"):
    if insight_df is None or insight_df.empty or "category" not in insight_df.columns:
        st.caption("No insight data available.")
    else:
        transfers_df = insight_df[(insight_df["category"] == "Transfer")].copy()
        if transfers_df.empty:
            st.success("No rows currently categorized as Transfer in the insight dataframe.")
        else:
            breakdown = (
                transfers_df.groupby("description")["amount"]
                .agg(total="sum", count="size")
                .reset_index()
            )
            breakdown["total"] = breakdown["total"].abs()
            st.caption(f"Rows in Transfer category (insight_df): {len(transfers_df)}")
            st.dataframe(
                breakdown.sort_values("total", ascending=False).head(30),
                use_container_width=True,
                hide_index=True,
            )

# --- Debug: Transfer bucket breakdown ---
with st.expander("Debug: Transfer transactions (by description)"):
    if insight_df is None or insight_df.empty or "category" not in insight_df.columns:
        st.caption("No insight data available.")
    else:
        transfers_df = insight_df[(insight_df["category"] == "Other")].copy()
        if transfers_df.empty:
            st.success("No rows currently categorized as Transfer in the insight dataframe.")
        else:
            breakdown = (
                transfers_df.groupby("description")["amount"]
                .agg(total="sum", count="size")
                .reset_index()
            )
            breakdown["total"] = breakdown["total"].abs()
            st.caption(f"Rows in Transfer category (insight_df): {len(transfers_df)}")
            st.dataframe(
                breakdown.sort_values("total", ascending=False).head(30),
                use_container_width=True,
                hide_index=True,
            )

# --- Debug: rent rows ---
with st.expander("Debug: rows containing 'Rent'"):
    if "description" in all_df.columns and "category" in all_df.columns:
        st.dataframe(
            all_df[all_df["description"].str.contains("Rent", case=False, na=False)][
                ["date", "amount", "description", "category"]
            ].head(50),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Missing expected columns on all_df.")