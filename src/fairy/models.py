"""Typed objects shared by every part of Fairy."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    """how a task fits into the day, from og design docs"""

    ANCHOR = "Anchor"
    QUEST = "Quest"
    MAINTENANCE = "Maintenance"
    OPTIONAL = "Optional"


class Task(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=200)
    category: Category = Category.OPTIONAL
    done: bool = False
    created_at: datetime
    completed_at: datetime | None = None
