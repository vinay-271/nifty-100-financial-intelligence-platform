from pathlib import Path
import sqlite3


DB_PATH = Path("db/nifty100.db")


def get_db():
    """Provide a SQLite connection for an API request."""

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()
