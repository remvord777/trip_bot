import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


# ======================================================
# СОЕДИНЕНИЕ С БД
# ======================================================
def get_connection():
    return sqlite3.connect(DB_PATH)


# ======================================================
# ИНИЦИАЛИЗАЦИЯ БД (ТОЛЬКО CREATE TABLE)
# ======================================================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            place TEXT,
            date_from TEXT,
            date_to TEXT,
            purpose TEXT,
            telegram_user_id INTEGER
        )
        """
    )

    conn.commit()
    conn.close()


# ======================================================
# ПОЛУЧИТЬ КОМАНДИРОВКИ ПОЛЬЗОВАТЕЛЯ
# ======================================================
def get_all_trips(telegram_user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, city, place, date_from, date_to, purpose
        FROM trips
        WHERE telegram_user_id = ?
        ORDER BY id DESC
        """,
        (telegram_user_id,),
    )

    rows = cursor.fetchall()
    conn.close()
    return rows
