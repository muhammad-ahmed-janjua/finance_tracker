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
