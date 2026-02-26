from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Keyword → category mapping.
# Keys are lowercased substrings; first match wins.
# ---------------------------------------------------------------------------
CATEGORY_RULES: dict[str, str] = {
    # Income
    "payroll":      "Income",
    "salary":       "Income",
    "wages":        "Income",
    # Groceries
    "woolworths":   "Groceries",
    "coles":        "Groceries",
    "aldi":         "Groceries",
    "iga":          "Groceries",
    "harris farm":  "Groceries",
    # Dining
    "mcdonald":     "Dining",
    "kfc":          "Dining",
    "subway":       "Dining",
    "domino":       "Dining",
    "hungry jack":  "Dining",
    "nandos":       "Dining",
    "uber eats":    "Dining",
    "menulog":      "Dining",
    "doordash":     "Dining",
    # Transport
    "opal":         "Transport",
    "uber":         "Transport",
    "taxi":         "Transport",
    "bp ":          "Transport",
    "shell":        "Transport",
    "caltex":       "Transport",
    "7-eleven":     "Transport",
    # Utilities
    "electricity":  "Utilities",
    "energy":       "Utilities",
    "water":        "Utilities",
    "telstra":      "Utilities",
    "optus":        "Utilities",
    "vodafone":     "Utilities",
    "internet":     "Utilities",
    # Subscriptions
    "netflix":      "Subscriptions",
    "spotify":      "Subscriptions",
    "youtube":      "Subscriptions",
    "disney":       "Subscriptions",
    "apple.com":    "Subscriptions",
    "microsoft":    "Subscriptions",
    "amazon prime": "Subscriptions",
    # Health
    "chemist":      "Health",
    "pharmacy":     "Health",
    "medicare":     "Health",
    "hospital":     "Health",
    "gym":          "Health",
    "fitness":      "Health",
    # Shopping
    "amazon":       "Shopping",
    "ebay":         "Shopping",
    "kmart":        "Shopping",
    "target":       "Shopping",
    "big w":        "Shopping",
    "myer":         "Shopping",
    "david jones":  "Shopping",
    # ATM / Cash
    "atm":          "Cash",
    # Transfers
    "transfer":     "Transfer",
    "bpay":         "Transfer",
    # Insurance
    "insurance":    "Insurance",
    # Education
    "university":   "Education",
    "tafe":         "Education",
}


def categorize(description: str) -> str:
    """Return the first matching category for a raw transaction description.
    Falls back to 'Other' if no rule matches."""
    lowered = description.lower()
    for keyword, category in CATEGORY_RULES.items():
        if keyword in lowered:
            return category
    return "Other"


def add_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with a new 'category' column derived from the 'description' column."""
    df = df.copy()
    df["category"] = df["description"].apply(categorize)
    return df


def spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Filter expense rows (amount < 0), group by category, and return
    DataFrame[category, total] sorted by total spend descending (absolute value)."""
    expenses = df[df["amount"] < 0]
    return (
        expenses.groupby("category")["amount"]
        .sum()
        .abs()
        .reset_index()
        .rename(columns={"amount": "total"})
        .sort_values("total", ascending=False)
        .reset_index(drop=True)
    )


def previous_window(start: date, end: date) -> tuple[date, date]:
    """Return the immediately preceding equal-length window.

    Example: start=2024-02-01, end=2024-02-29 (29 days)
             → prev_start=2024-01-03, prev_end=2024-01-31
    """
    from datetime import timedelta
    window_length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window_length - 1)
    return prev_start, prev_end


def category_deltas(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> pd.DataFrame:
    """Compare category spending between two equal-length windows.

    Returns DataFrame[category, current, previous, delta] sorted by delta descending.
    delta > 0: spent more in current period.
    delta < 0: spent less in current period.
    """
    current = (
        spending_by_category(current_df)
        .rename(columns={"total": "current"})
    )
    previous = (
        spending_by_category(previous_df)
        .rename(columns={"total": "previous"})
    )
    merged = current.merge(previous, on="category", how="outer").fillna(0.0)
    merged["delta"] = merged["current"] - merged["previous"]
    return (
        merged
        .sort_values("delta", ascending=False)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Recurring commitments detection
# ---------------------------------------------------------------------------

import re as _re

# Strip common leading payment method prefixes before extracting merchant name
_PAYMENT_PREFIX = _re.compile(
    r"^(direct debit|bpay|visa purchase|eftpos)\s+",
    _re.IGNORECASE,
)

# Remove standalone digit sequences (ref numbers, phone numbers) and
# common noise tokens (state/country codes, legal suffixes)
_NOISE_TOKEN = _re.compile(
    r"\b(\d[\d\-\.]*|pty|ltd|au|nz|us|ca|gb|sg|hk|nsw|vic|qld|sa|wa|tas|nt|act)\b",
    _re.IGNORECASE,
)

_EXTRA_SPACE = _re.compile(r"\s+")


def _normalize_merchant(description: str) -> str:
    """Derive a stable merchant name from a raw transaction description.

    Steps:
      1. Strip leading payment-method prefix (BPAY, DIRECT DEBIT, etc.)
      2. Remove digit sequences and noise tokens (ref numbers, state codes)
      3. Take the first two meaningful words and title-case them
    """
    s = _PAYMENT_PREFIX.sub("", description.strip())
    s = _NOISE_TOKEN.sub(" ", s)
    s = _EXTRA_SPACE.sub(" ", s).strip()
    return " ".join(s.split()[:2]).title()


def detect_recurring_commitments(df: pd.DataFrame) -> pd.DataFrame:
    """Detect recurring expense commitments using deterministic cadence rules.

    Rules:
      - Expenses only (amount < 0)
      - >= 3 occurrences per normalized merchant
      - Median day gap 5–9  → weekly
      - Median day gap 25–35 → monthly

    Confidence = fraction of consecutive gaps that fall within the cadence range.

    Returns DataFrame[merchant, cadence, median_amount, last_seen, occurrences, confidence]
    sorted by cadence then confidence descending.
    """
    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return pd.DataFrame(columns=[
            "merchant", "cadence", "median_amount", "last_seen", "occurrences", "confidence",
        ])

    expenses["merchant"] = expenses["description"].apply(_normalize_merchant)
    expenses["date"] = pd.to_datetime(expenses["date"])

    records = []

    for merchant, group in expenses.groupby("merchant"):
        if len(group) < 3:
            continue

        sorted_dates = group["date"].sort_values().tolist()
        gaps = [(sorted_dates[i + 1] - sorted_dates[i]).days for i in range(len(sorted_dates) - 1)]

        # Use the middle value of sorted gaps as a robust median
        median_gap = sorted(gaps)[len(gaps) // 2]

        if 5 <= median_gap <= 9:
            cadence = "weekly"
            in_range = sum(1 for g in gaps if 5 <= g <= 9)
        elif 25 <= median_gap <= 35:
            cadence = "monthly"
            in_range = sum(1 for g in gaps if 25 <= g <= 35)
        else:
            continue

        records.append({
            "merchant":      merchant,
            "cadence":       cadence,
            "median_amount": round(float(group["amount"].abs().median()), 2),
            "last_seen":     group["date"].max().date(),
            "occurrences":   len(group),
            "confidence":    round(in_range / len(gaps), 2),
        })

    if not records:
        return pd.DataFrame(columns=[
            "merchant", "cadence", "median_amount", "last_seen", "occurrences", "confidence",
        ])

    return (
        pd.DataFrame(records)
        .sort_values(["cadence", "confidence"], ascending=[True, False])
        .reset_index(drop=True)
    )
