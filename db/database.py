import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        place TEXT,
        date_from TEXT,
        date_to TEXT,
        purpose TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_all_trips():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, city, place, date_from, date_to, purpose
        FROM trips
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_cities(limit: int = 4) -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT city
        FROM trips
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]
