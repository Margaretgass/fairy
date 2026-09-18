from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from fairy.models import Category, Task


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        category=Category(row["category"]),
        done=bool(row["done"]),
        created_at=datetime.fromisoformat(row["created_at"]).replace(tzinfo=UTC),
        completed_at=datetime.fromisoformat(row["completed_at"]).replace(tzinfo=UTC)
        if row["completed_at"]
        else None,
    )


def add_task(
    conn: sqlite3.Connection,
    title: str,
    category: Category = Category.OPTIONAL,
    now: datetime | None = None,
) -> Task:
    """Add a task to the database and return it."""
    now = now or datetime.now(UTC)
    cur = conn.execute(
        "INSERT INTO tasks (title, category, done, created_at) VALUES (?, ?, 0, ?)",
        (title.strip(), category.value, now.isoformat()),
    )
    return get_task(conn, cur.lastrowid)


def get_task(conn: sqlite3.Connection, task_id: int) -> Task:
    """Fetch one task. Raises KeyError if it doesn't exist."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise KeyError(f"no task with id {task_id}")
    return _row_to_task(row)


def list_tasks(conn: sqlite3.Connection, *, include_done: bool = False) -> list[Task]:
    """return a list of tasks, hide completed tasks unless asked"""
    sql = "SELECT * FROM tasks"
    if not include_done:
        sql += " WHERE done = 0"
    sql += " ORDER BY id"
    return [_row_to_task(row) for row in conn.execute(sql)]


def complete_task(conn: sqlite3.Connection, task_id: int, *, now: datetime | None = None) -> Task:
    """Mark a task as completed and return it."""
    now = now or datetime.now(UTC)
    get_task(conn, task_id)  # raises if not found
    conn.execute(
        "UPDATE tasks SET done = 1, completed_at = ? WHERE id = ?",
        (now.isoformat(), task_id),
    )
    return get_task(conn, task_id)
