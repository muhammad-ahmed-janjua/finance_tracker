from sqlalchemy import select, func
from app.db import SessionLocal
from app.models import Transaction

def print_summary():
    with SessionLocal() as session:
        total_income = session.scalar(
            select(func.sum(Transaction.amount))
            .where(Transaction.amount > 0)
        ) or 0

        total_expenses = session.scalar(
            select(func.sum(Transaction.amount))
            .where(Transaction.amount < 0)
        ) or 0

        net = total_income + total_expenses

        print("\n==== Summary ====")
        print(f"Total income:    ${total_income:.2f}")
        print(f"Total expenses:  ${total_expenses:.2f}")
        print(f"Net change:      ${net:.2f}")


def print_monthly_summary():
    with SessionLocal() as session:
        stmt = (
            select(
                func.strftime('%Y-%m', Transaction.date).label("month"),
                func.sum(Transaction.amount).label("total")
            )
            .group_by("month")
            .order_by("month")
        )

        results = session.execute(stmt).all()

        print("\n==== Monthly Summary ====")
        for month, total in results:
            print(f"{month}: ${total:.2f}")

def print_all_transaction():
    with SessionLocal() as session:
        stmt = select(Transaction)
        results = session.execute(stmt).scalars().all()

        print("\n==== All Transactions ====")
        for tx in results:
            print(
                f"{tx.date.date()} | "
                f"{tx.amount:>10.2f} | "
                f"{tx.description_raw[:40]:<40} | "
                f"{tx.cumulative_balance:>10.2f}"
            )