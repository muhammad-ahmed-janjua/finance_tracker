from __future__ import annotations

from datetime import date
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import core, queries

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Finance Tracker",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

CATEGORIZATION_VERSION = "v2-transfer-reason"

# ---------------------------------------------------------------------------
# CSS — hide chrome, style metric cards, tighten spacing
# ---------------------------------------------------------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}

/* Metric cards */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px 20px 12px;
}
[data-testid="stMetricLabel"]  > div { font-size: 0.78rem; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.06em; }
[data-testid="stMetricValue"]  > div { font-size: 1.7rem;  font-weight: 700; }
[data-testid="stMetricDelta"]  > div { font-size: 0.78rem; }

/* Tighter tab strip */
[data-testid="stTabs"] { margin-top: 4px; }

/* Section typography helpers */
.sh { font-size: 1rem; font-weight: 600; margin: 0 0 2px; }
.sc { font-size: 0.78rem; opacity: 0.55; margin: 0 0 12px; }

/* Sidebar helper text */
[data-testid="stSidebar"] .helper { font-size: 0.74rem; opacity: 0.5; margin-top: -6px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached data loaders  (logic unchanged)
# ---------------------------------------------------------------------------
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
    return core.add_categories(queries.get_transactions(start, end))

@st.cache_data
def get_date_bounds() -> tuple[date | None, date | None]:
    return queries.get_date_bounds()


# ---------------------------------------------------------------------------
# Guard: need data before anything else
# ---------------------------------------------------------------------------
min_d, max_d = get_date_bounds()
if min_d is None or max_d is None:
    st.warning("No transactions found in the database yet.")
    st.stop()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Finance Tracker")
    st.caption("Personal spend analytics")
    st.divider()

    st.markdown("**Date range**")
    raw_range = st.date_input(
        "date_range",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
        label_visibility="collapsed",
    )
    if isinstance(raw_range, (list, tuple)):
        start_date = raw_range[0]
        end_date   = raw_range[1] if len(raw_range) > 1 else raw_range[0]
    else:
        start_date = end_date = raw_range

    st.markdown("")
    st.markdown("**Spending mode**")
    exclude_transfers = st.checkbox("Exclude transfers (True Spend)")
    st.markdown(
        "<div class='helper'>Removes inter-account transfers so charts reflect real spending.</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    days = (end_date - start_date).days + 1
    st.caption(f"{days} days · {start_date:%b %d %Y} → {end_date:%b %d %Y}")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
prev_start, prev_end = core.previous_window(start_date, end_date)

income,      expenses,      net      = load_summary(start_date, end_date)
prev_income, prev_expenses, prev_net = load_summary(prev_start,  prev_end)

monthly_df  = load_monthly(start_date, end_date)
all_df      = load_all(start_date, end_date, CATEGORIZATION_VERSION)
prev_all_df = load_all(prev_start,  prev_end,  CATEGORIZATION_VERSION)
recent_df   = core.add_categories(load_recent(start_date, end_date, limit=50))


def _filter_transfers(df: pd.DataFrame) -> pd.DataFrame:
    if exclude_transfers and not df.empty and "category" in df.columns:
        return df[df["category"] != "Transfer"].reset_index(drop=True)
    return df

insight_df      = _filter_transfers(all_df)
prev_insight_df = _filter_transfers(prev_all_df)

has_prev = (prev_income + abs(prev_expenses)) > 0


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
h_left, h_right = st.columns([6, 1])
with h_left:
    mode_badge = " · transfers excluded" if exclude_transfers else ""
    st.markdown("## Finance Tracker")
    st.caption(f"{start_date:%b %d, %Y} – {end_date:%b %d, %Y}{mode_badge}")
with h_right:
    st.markdown(
        "<div style='text-align:right;padding-top:14px'>"
        "<span style='background:rgba(92,124,250,0.18);color:#8b9cf4;"
        "padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:600'>"
        "DEMO</span></div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
k1, k2, k3 = st.columns(3)

income_delta   = round(income        - prev_income,          2) if has_prev else None
expenses_delta = round(abs(expenses) - abs(prev_expenses),   2) if has_prev else None
net_delta      = round(net           - prev_net,             2) if has_prev else None

k1.metric("Total Income",    f"${income:,.2f}",        delta=income_delta,   delta_color="normal")
k2.metric("Total Expenses",  f"${abs(expenses):,.2f}", delta=expenses_delta, delta_color="inverse")
k3.metric("Net Change",      f"${net:,.2f}",           delta=net_delta,      delta_color="normal")

st.markdown("")


# ---------------------------------------------------------------------------
# Plotly theme helpers
# ---------------------------------------------------------------------------
_PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(color="#b0b8cc", size=12),
    margin=dict(l=0, r=0, t=8, b=0),
    hoverlabel=dict(bgcolor="#1a1f2e", font_color="#e0e4ef", font_size=12),
)
_GRID  = dict(showgrid=True,  gridcolor="rgba(255,255,255,0.06)", zeroline=False)
_NOGRD = dict(showgrid=False, zeroline=False)


def _currency_axis(d: dict) -> dict:
    return {**d, "tickprefix": "$", "tickformat": ",.0f"}


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_insights, tab_debug = st.tabs(["Overview", "Insights", "Debug"])


# ── OVERVIEW ──────────────────────────────────────────────────────────────
with tab_overview:

    # Monthly net chart
    st.markdown('<p class="sh">Monthly net</p>', unsafe_allow_html=True)
    st.markdown('<p class="sc">Net cash flow by calendar month</p>', unsafe_allow_html=True)

    if monthly_df.empty:
        st.info("No monthly data available for the selected range.")
    else:
        bar_colors = ["#ef5350" if v < 0 else "#26a69a" for v in monthly_df["total"]]
        fig_monthly = go.Figure(go.Bar(
            x=monthly_df["month"],
            y=monthly_df["total"],
            marker_color=bar_colors,
            hovertemplate="<b>%{x}</b><br>Net: $%{y:,.2f}<extra></extra>",
        ))
        fig_monthly.add_hline(y=0, line_color="rgba(255,255,255,0.15)", line_width=1)
        fig_monthly.update_layout(
            **_PLOTLY_BASE,
            height=300,
            xaxis={**_NOGRD, "tickangle": -30},
            yaxis=_currency_axis(_GRID),
            bargap=0.35,
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    st.markdown("")

    # Spending by category
    mode_note = " · transfers excluded" if exclude_transfers else ""
    st.markdown('<p class="sh">Spending by category</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sc">Expenses only{mode_note}</p>', unsafe_allow_html=True)

    spending_df = core.spending_by_category(insight_df)
    if spending_df.empty:
        st.info("No expense data to display. Try adjusting the date range or spending mode.")
    else:
        fig_spend = go.Figure(go.Bar(
            x=spending_df["total"],
            y=spending_df["category"],
            orientation="h",
            marker_color="#5c7cfa",
            marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>",
        ))
        fig_spend.update_layout(
            **_PLOTLY_BASE,
            height=max(260, len(spending_df) * 34 + 40),
            xaxis=_currency_axis(_GRID),
            yaxis={**_NOGRD, "autorange": "reversed"},
        )
        st.plotly_chart(fig_spend, use_container_width=True)


# ── INSIGHTS ───────────────────────────────────────────────────────────────
with tab_insights:

    # Period comparison
    st.markdown('<p class="sh">What changed vs previous period</p>', unsafe_allow_html=True)
    st.caption(
        f"Current: {start_date:%b %d, %Y} – {end_date:%b %d, %Y}  ·  "
        f"Previous: {prev_start:%b %d, %Y} – {prev_end:%b %d, %Y}"
    )

    deltas_df = core.category_deltas(insight_df, prev_insight_df)
    increases = deltas_df[deltas_df["delta"] > 0].head(5).copy()
    decreases = deltas_df[deltas_df["delta"] < 0].tail(5).copy()
    increases["change"] = increases["delta"].apply(lambda x: f"+${x:,.2f}")
    decreases["change"] = decreases["delta"].apply(lambda x: f"-${abs(x):,.2f}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top increases**")
        if increases.empty:
            st.caption("No spending increases detected in this period.")
        else:
            st.dataframe(
                increases[["category", "change"]].reset_index(drop=True),
                use_container_width=True, hide_index=True,
            )
    with col2:
        st.markdown("**Top decreases**")
        if decreases.empty:
            st.caption("No spending decreases detected in this period.")
        else:
            st.dataframe(
                decreases[["category", "change"]].reset_index(drop=True),
                use_container_width=True, hide_index=True,
            )

    st.markdown("")
    st.divider()

    # Recurring commitments
    st.markdown('<p class="sh">Recurring commitments</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sc">Merchants with a consistent weekly or monthly cadence · min. 3 occurrences</p>',
        unsafe_allow_html=True,
    )

    commitments_df = core.detect_recurring_commitments(insight_df)
    if commitments_df.empty:
        st.info("No recurring commitments detected. Try a wider date range (3+ months recommended).")
    else:
        display = commitments_df.copy()
        display["confidence"] = (commitments_df["confidence"] * 100).round(0).astype(int)
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "merchant":      st.column_config.TextColumn("Merchant",       width="medium"),
                "cadence":       st.column_config.TextColumn("Cadence",        width="small"),
                "median_amount": st.column_config.NumberColumn("Typical amount", format="$%.2f"),
                "last_seen":     st.column_config.DateColumn("Last seen",      format="MMM DD, YYYY"),
                "occurrences":   st.column_config.NumberColumn("Occurrences",  width="small"),
                "confidence":    st.column_config.NumberColumn("Confidence %", format="%d%%"),
            },
        )


# ── DEBUG ──────────────────────────────────────────────────────────────────
with tab_debug:
    st.caption("Raw data tables for inspection.")
    st.markdown("")

    st.markdown("**Recent transactions** (last 50)")
    st.dataframe(
        recent_df,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "date":                st.column_config.DatetimeColumn("Date",        format="MMM DD, YYYY"),
            "amount":              st.column_config.NumberColumn("Amount",         format="$%.2f"),
            "description":         st.column_config.TextColumn("Description",     width="large"),
            "cumulative_balance":  st.column_config.NumberColumn("Balance",        format="$%.2f"),
            "category":            st.column_config.TextColumn("Category"),
        },
    )

    st.markdown("")

    with st.expander("Debug: Transfer category breakdown"):
        if insight_df.empty or "category" not in insight_df.columns:
            st.caption("No insight data available.")
        else:
            tdf = insight_df[insight_df["category"] == "Transfer"].copy()
            if tdf.empty:
                st.success("No rows currently categorized as Transfer in insight_df.")
            else:
                bd = (
                    tdf.groupby("description")["amount"]
                    .agg(total="sum", count="size")
                    .reset_index()
                    .assign(total=lambda d: d["total"].abs())
                    .sort_values("total", ascending=False)
                    .head(30)
                )
                st.caption(f"{len(tdf)} rows in Transfer category")
                st.dataframe(bd, use_container_width=True, hide_index=True)

    with st.expander("Debug: Other / uncategorized breakdown"):
        if insight_df.empty or "category" not in insight_df.columns:
            st.caption("No insight data available.")
        else:
            odf = insight_df[insight_df["category"] == "Other"].copy()
            if odf.empty:
                st.success("No uncategorized rows.")
            else:
                bd = (
                    odf.groupby("description")["amount"]
                    .agg(total="sum", count="size")
                    .reset_index()
                    .assign(total=lambda d: d["total"].abs())
                    .sort_values("total", ascending=False)
                    .head(30)
                )
                st.caption(f"{len(odf)} rows categorized as Other")
                st.dataframe(bd, use_container_width=True, hide_index=True)

    with st.expander("Debug: Rows containing 'Rent'"):
        if "description" in all_df.columns and "category" in all_df.columns:
            rent_df = all_df[
                all_df["description"].str.contains("Rent", case=False, na=False)
            ][["date", "amount", "description", "category"]].head(50)
            if rent_df.empty:
                st.caption("No rows containing 'Rent' found.")
            else:
                st.dataframe(rent_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Missing expected columns on all_df.")
