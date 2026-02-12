from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description_raw: Mapped[str] = mapped_column(String, nullable=False)
    cumulative_balance: Mapped[float] = mapped_column(Float, nullable=False)

