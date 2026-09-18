"""MCP server shares fairy task list with any MCP client"""

from __future__ import annotations

from fastmcp import FastMCP

from fairy import store, tasks
from fairy.models import Category

mcp = FastMCP("fairy-tasks")


def main() -> None:
    """Start the Fairy tasks MCP server."""
    mcp.run()


@mcp.tool
def add_task(title: str, category: str = "Optional") -> dict:
    """Add a task to the database and return it.
    Args:
        title: what needs to be done, in user's words
        category: one Anchor, Quest, Maintenance, Optional.
            Anchor is a fixed, important commitment.
            Quest is part of a bigger project or goal
            Maintenance is a recurring task or routine such as working out
            Optional is everything else
    """
    with store.session() as conn:
        task = tasks.add_task(conn, title, Category(category))
        return task.model_dump(mode="json")


@mcp.tool
def list_tasks(include_done: bool = False) -> list[dict]:
    """return a list of tasks, by default only unfinished ones

    Args:
        include_done: set true to also return completed tasks
    """
    with store.session() as conn:
        found = tasks.list_tasks(conn, include_done=include_done)
        return [task.model_dump(mode="json") for task in found]


@mcp.tool
def complete_task(task_id: int) -> dict:
    """Mark a task as finished and return it.

    Args:
        task_id: the id of the task to complete
    """
    with store.session() as conn:
        task = tasks.complete_task(conn, task_id)
        return task.model_dump(mode="json")


if __name__ == "__main__":
    main()
