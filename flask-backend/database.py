"""Database helpers for the Flask backend (SQLite)."""

import sqlite3
from config import DB_PATH


def get_connection():
    """Create a new SQLite connection for the configured DB file."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create required tables if they do not already exist."""
    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                user_id INTEGER,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                platform TEXT NOT NULL,
                participants TEXT NOT NULL,
                reminder_time TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                phone_numbers TEXT,
                emails TEXT,
                synced_at TEXT
            )
        """)
