from __future__ import annotations

from datetime import date
import re
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
    "mex fresh":    "Dining",
    "mad mex":      "Dining",
    "oporto":       "Dining",

    # Transport
    "opal":         "Transport",
    "uber":         "Transport",
    "taxi":         "Transport",
    "transportfornsw": "Transport",
    "transport for nsw": "Transport",
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
    "amznprime":    "Subscriptions",
    "chatgpt":      "Subscriptions",
    "openai":       "Subscriptions",

    # Health
    "chemist":      "Health",
    "pharmacy":     "Health",
    "medicare":     "Health",
    "hospital":     "Health",
    "gym":          "Health",
    "fitness":      "Health",
    "anytime fitness": "Health",
    "barber":       "Health",

    # Shopping
    "amazon":       "Shopping",
    "ebay":         "Shopping",
    "kmart":        "Shopping",
    "target":       "Shopping",
    "big w":        "Shopping",
    "myer":         "Shopping",
    "david jones":  "Shopping",
    "afterpay":     "Shopping",
    "jb hi fi":     "Shopping",
    "jb hifi":      "Shopping",

    # ATM / Cash
    "atm":          "Cash",

    # Transfers (category label only — filtering uses is_transfer())
    "transfer":     "Transfer",

    # Insurance
    "insurance":    "Insurance",

    # Education
    "university":   "Education",
    "tafe":         "Education",
    "rent": "Utilities",        # or "Housing"
    "groceries": "Groceries",
    "nails": "Health",
    "savings": "Transfer",    
}

# ---------------------------------------------------------------------------
# Transfer detection (HIGH PRECISION)
# Only match the whole word "transfer".
# ---------------------------------------------------------------------------
_TRANSFER_WORD = re.compile(r"\btransfer\b", re.IGNORECASE)

def is_transfer(description: str) -> bool:
    """Return True only if description contains the whole word 'transfer'."""
    if not isinstance(description, str):
        return False
    return bool(_TRANSFER_WORD.search(description))


# ---------------------------------------------------------------------------
# Transfer description breakdown
# Extract the meaningful tail/reason (e.g., "rent") from transfer descriptions.
# ---------------------------------------------------------------------------
_TRANSFER_NOISE = {
    "transfer", "to", "from", "commbank", "app",
    "internet", "banking", "bank", "online", "mobile"
}

_RE_MASKED = re.compile(r"\bxx\d+\b", re.IGNORECASE)   # e.g. xx6405
_RE_LONGNUM = re.compile(r"\b\d{4,}\b")                # long ids, refs
_RE_NONALPHA = re.compile(r"[^a-z\s]")                 # keep letters/spaces
_RE_SPACES = re.compile(r"\s+")

def transfer_reason(description: str, tail_words: int = 3) -> str:
    """
    Extract a short "reason" phrase from a transfer description.

    Example:
      "Transfer to xx6405 CommBank app Rent" -> "rent"

    Steps:
      - lowercase + trim
      - remove masked accounts (xx####) and long numbers (>=4 digits)
      - remove punctuation
      - drop noise tokens (transfer/to/from/commbank/app/...)
      - return last N remaining words (tail-focused)
    """
    if not isinstance(description, str):
        return ""

    s = description.lower().strip()
    s = _RE_MASKED.sub(" ", s)
    s = _RE_LONGNUM.sub(" ", s)
    s = _RE_NONALPHA.sub(" ", s)
    s = _RE_SPACES.sub(" ", s).strip()

    words = [w for w in s.split() if w and w not in _TRANSFER_NOISE]
    if not words:
        return ""

    return " ".join(words[-tail_words:])


# ---------------------------------------------------------------------------
# Categorization helpers
# ---------------------------------------------------------------------------
_PAYMENT_PREFIX = re.compile(
    r"^(direct debit|bpay|visa purchase|eftpos|dbs\*)\s+",
    re.IGNORECASE,
)

_NOISE_TOKEN = re.compile(
    r"\b(\d[\d\-\.]*|pty|ltd|au|nz|us|ca|gb|sg|hk|nsw|vic|qld|sa|wa|tas|nt|act|card|value|date)\b",
    re.IGNORECASE,
)

def categorization_key(description: str, tail_words: int = 5) -> str:
    """
    Produce a cleaned key for rule matching (non-transfer).

    - lowercase/trim
    - strip common leading prefixes (eftpos/visa purchase/direct debit/dbs*)
    - remove digits + common noise tokens (nsw/aus/pty/etc.)
    - collapse whitespace
    - keep last N words (tail-focused but not destructive)
    """
    if not isinstance(description, str):
        return ""

    s = description.lower().strip()
    s = _PAYMENT_PREFIX.sub("", s)
    s = _RE_MASKED.sub(" ", s)
    s = _NOISE_TOKEN.sub(" ", s)
    s = _RE_NONALPHA.sub(" ", s)
    s = _RE_SPACES.sub(" ", s).strip()

    if not s:
        return ""
    parts = s.split()
    return " ".join(parts[-tail_words:]) if len(parts) > tail_words else s


def categorize(description: str) -> str:
    """
    Return the first matching category for a raw transaction description.

    Strategy:
    - If it's a transfer: match against transfer_reason() first (tail), then fallback to full.
    - Otherwise: match against categorization_key() first (cleaned/tail), then fallback to full.
    - Default: 'Other'
    """
    if not isinstance(description, str) or not description:
        return "Other"

    lowered = description.lower()

    # Transfers: focus on extracted reason at the end
    if is_transfer(description):
        reason = transfer_reason(description)

        if reason:
            # Try matching reason first
            for keyword, category in CATEGORY_RULES.items():
                if keyword in reason:
                    return category

        # If reason didn't match anything meaningful,
        # classify as pure Transfer
        return "Transfer"

    # Non-transfers: use cleaned key first
    key = categorization_key(description)
    if key:
        for keyword, category in CATEGORY_RULES.items():
            if keyword in key:
                return category

    # fallback to raw lowered
    for keyword, category in CATEGORY_RULES.items():
        if keyword in lowered:
            return category

    return "Other"


def add_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with a new 'category' column derived from the 'description' column."""
    df = df.copy()
    if "description" not in df.columns:
        df["category"] = "Other"
        return df
    df["category"] = df["description"].apply(categorize)
    return df


# ---------------------------------------------------------------------------
# Spending breakdown
# ---------------------------------------------------------------------------
def spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Filter expense rows (amount < 0), group by category, and return
    DataFrame[category, total] sorted by total spend descending (absolute value)."""
    _EMPTY = pd.DataFrame(columns=["category", "total"])
    if df is None or df.empty or "amount" not in df.columns or "category" not in df.columns:
        return _EMPTY
    expenses = df[df["amount"] < 0]
    if expenses.empty:
        return _EMPTY
    return (
        expenses.groupby("category")["amount"]
        .sum()
        .abs()
        .reset_index()
        .rename(columns={"amount": "total"})
        .sort_values("total", ascending=False)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Period-over-period comparison
# ---------------------------------------------------------------------------
def previous_window(start: date, end: date) -> tuple[date, date]:
    """Return the immediately preceding equal-length window."""
    from datetime import timedelta
    window_length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window_length - 1)
    return prev_start, prev_end


def category_deltas(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> pd.DataFrame:
    """Compare category spending between two equal-length windows."""
    _EMPTY = pd.DataFrame(columns=["category", "current", "previous", "delta"])
    current = spending_by_category(current_df).rename(columns={"total": "current"})
    previous = spending_by_category(previous_df).rename(columns={"total": "previous"})
    if current.empty and previous.empty:
        return _EMPTY
    merged = current.merge(previous, on="category", how="outer").fillna(0.0)
    merged["delta"] = merged["current"] - merged["previous"]
    return merged.sort_values("delta", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Recurring commitments detection
# ---------------------------------------------------------------------------
# Strip common leading payment method prefixes before extracting merchant name
_PAYMENT_PREFIX_RECUR = re.compile(
    r"^(direct debit|bpay|visa purchase|eftpos|dbs\*)\s+",
    re.IGNORECASE,
)

# Remove standalone digit sequences (ref numbers, phone numbers) and common noise tokens
_NOISE_TOKEN_RECUR = re.compile(
    r"\b(\d[\d\-\.]*|pty|ltd|au|nz|us|ca|gb|sg|hk|nsw|vic|qld|sa|wa|tas|nt|act|card|value|date)\b",
    re.IGNORECASE,
)

_EXTRA_SPACE = re.compile(r"\s+")

def _normalize_merchant(description: str) -> str:
    """Derive a stable merchant name from a raw transaction description."""
    s = _PAYMENT_PREFIX_RECUR.sub("", (description or "").strip())
    s = _RE_MASKED.sub(" ", s)
    s = _NOISE_TOKEN_RECUR.sub(" ", s)
    s = _RE_NONALPHA.sub(" ", s)
    s = _EXTRA_SPACE.sub(" ", s).strip()
    # Use first two words as stable label
    words = s.split()
    return " ".join(words[:2]).title() if words else "Unknown"


def detect_recurring_commitments(df: pd.DataFrame) -> pd.DataFrame:
    """Detect recurring expense commitments using deterministic cadence rules."""
    cols = ["merchant", "cadence", "median_amount", "last_seen", "occurrences", "confidence"]
    if df is None or df.empty or "amount" not in df.columns or "description" not in df.columns or "date" not in df.columns:
        return pd.DataFrame(columns=cols)

    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return pd.DataFrame(columns=cols)

    expenses["merchant"] = expenses["description"].apply(_normalize_merchant)
    expenses["date"] = pd.to_datetime(expenses["date"], errors="coerce")
    expenses = expenses.dropna(subset=["date"])
    if expenses.empty:
        return pd.DataFrame(columns=cols)

    records: list[dict] = []

    for merchant, group in expenses.groupby("merchant"):
        if len(group) < 3:
            continue

        sorted_dates = group["date"].sort_values().tolist()
        gaps = [(sorted_dates[i + 1] - sorted_dates[i]).days for i in range(len(sorted_dates) - 1)]
        if not gaps:
            continue

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
            "merchant": merchant,
            "cadence": cadence,
            "median_amount": round(float(group["amount"].abs().median()), 2),
            "last_seen": group["date"].max().date(),
            "occurrences": int(len(group)),
            "confidence": round(in_range / len(gaps), 2),
        })

    if not records:
        return pd.DataFrame(columns=cols)

    return (
        pd.DataFrame(records)
        .sort_values(["cadence", "confidence"], ascending=[True, False])
        .reset_index(drop=True)
    )