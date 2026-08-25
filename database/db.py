import sqlite3
from datetime import date
from pathlib import Path

from werkzeug.security import generate_password_hash


DATABASE_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_db()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_user(name, email, password):
    connection = get_db()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            ON CONFLICT(email) DO NOTHING
            """,
            (name, email, generate_password_hash(password)),
        )
        connection.commit()
        return cursor.rowcount == 1
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def seed_db():
    connection = get_db()

    try:
        existing_user = connection.execute(
            "SELECT 1 FROM users LIMIT 1"
        ).fetchone()
        if existing_user:
            return

        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                "Demo User",
                "demo@spendly.com",
                generate_password_hash("demo123"),
            ),
        )

        demo_user_id = cursor.lastrowid
        current_date = date.today()
        expense_dates = [
            date(current_date.year, current_date.month, day).isoformat()
            for day in (1, 4, 7, 10, 13, 16, 19, 22)
        ]
        expenses = [
            (demo_user_id, 12.50, "Food", expense_dates[0], "Lunch"),
            (demo_user_id, 3.25, "Transport", expense_dates[1], "Bus fare"),
            (demo_user_id, 89.99, "Bills", expense_dates[2], "Internet bill"),
            (demo_user_id, 24.00, "Health", expense_dates[3], "Pharmacy"),
            (
                demo_user_id,
                15.00,
                "Entertainment",
                expense_dates[4],
                "Movie ticket",
            ),
            (demo_user_id, 42.75, "Shopping", expense_dates[5], "Household items"),
            (demo_user_id, 8.50, "Other", expense_dates[6], "Parking"),
            (demo_user_id, 18.25, "Food", expense_dates[7], "Groceries"),
        ]
        connection.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            expenses,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
