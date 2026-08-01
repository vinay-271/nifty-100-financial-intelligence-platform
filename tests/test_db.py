import sqlite3
from pathlib import Path

DB_PATH = Path("db") / "nifty100.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "stock_prices",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "sectors",
    ]

    print("\n" + "=" * 45)
    print("N100 DATABASE VERIFICATION")
    print("=" * 45)

    print("\nTable Row Counts")
    print("-" * 45)

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:<20} : {count}")

    print("\nForeign Key Check")
    print("-" * 45)

    cursor.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()

    if not violations:
        print("✓ No foreign key violations found.")
    else:
        print(f"✗ {len(violations)} foreign key violation(s):")
        for violation in violations:
            print(violation)

    conn.close()


if __name__ == "__main__":
    main()
