from app import queries


def print_summary():
    income, expenses, net = queries.get_all_summary()

    print("\n==== Summary ====")
    print(f"Total income:    ${income:.2f}")
    print(f"Total expenses:  ${expenses:.2f}")
    print(f"Net change:      ${net:.2f}")


def print_monthly_summary():
    results = queries.get_all_monthly_totals()

    print("\n==== Monthly Summary ====")
    for month, total in results:
        print(f"{month}: ${total:.2f}")


def print_all_transaction():
    results = queries.get_all_transactions()

    print("\n==== All Transactions ====")
    for tx in results:
        print(
            f"{tx.date.date()} | "
            f"{tx.amount:>10.2f} | "
            f"{tx.description_raw[:40]:<40} | "
            f"{tx.cumulative_balance:>10.2f}"
        )
