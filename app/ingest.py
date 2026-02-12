from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import re

import pandas as pd

from app.models import Transaction

# Generate unique transaction id for each row
def generate_transaction_id(date: datetime, amount: float, description: str, cumulative_balance: float) -> str:
    # normalise white space
    whitespace = re.compile(r"\s+")
    desc = whitespace.sub(" ", description.strip())
    raw = f"{date.date().isoformat()}|{amount:.2f}|{desc}|{cumulative_balance:.2f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_commbank_csv(path: str | Path) -> list[Transaction]:
    path = Path(path)

    df = pd.read_csv(
            path, 
            header=None,
            names=["date","amount","description","cumulative_balance"],
            encoding="utf-8-sig",
            )

    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="raise")
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    df["description"] = df["description"].astype(str).fillna("").str.strip()
    df["cumulative_balance"] = pd.to_numeric(df["cumulative_balance"], errors="raise")

    print(df.head())
    print(df.shape)

    transactions: list[Transaction] = []
    for row in df.itertuples(index=False):
        date = row.date.to_pydatetime()
        amount = float(row.amount)
        desc = row.description
        bal = float(row.cumulative_balance)

        tx_id = generate_transaction_id(date, amount, desc, bal)

        transactions.append(
            Transaction(
                transaction_id = tx_id,
                date=date,
                amount=amount,
                description_raw = desc,
                cumulative_balance = bal
            )
        )

    return transactions
