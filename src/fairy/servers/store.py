"""SQLite storage. One file shared by every fairy part"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path.home() / ".fairy" / "fairy.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    category     TEXT    NOT NULL DEFAULT 'Optional',
    done         INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL,
    completed_at TEXT
);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open database, create file and schema if they don't exist."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # rows can be indexed by col name
    conn.execute("PRAGMA journal_mode = WAL")  # 2 processes can read at once
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session(db_path: Path | None = None) -> Generator[sqlite3.Connection]:
    """Open a connection, commit on success, and always close it."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
