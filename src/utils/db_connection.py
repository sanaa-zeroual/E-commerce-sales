import sqlite3

from src.config import DATABASE_PATH, ensure_project_dirs


def get_connection():
    """Return a SQLite connection with foreign keys enabled."""
    ensure_project_dirs()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection