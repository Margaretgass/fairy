"""Pure geometry rules for the desktop Fairy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


def clamp_position(position: Point, window: Rect, available: Rect) -> Point:
    """Return a top-left position that keeps the window in the available area."""
    max_x = max(available.x, available.x + available.width - window.width)
    max_y = max(available.y, available.y + available.height - window.height)
    return Point(
        x=min(max(position.x, available.x), max_x),
        y=min(max(position.y, available.y), max_y),
    )


def snap_to_nearest_side(position: Point, window: Rect, available: Rect) -> Point:
    """Clamp a position, then move it to the nearer horizontal screen edge."""
    clamped = clamp_position(position, window, available)
    left_x = available.x
    right_x = max(available.x, available.x + available.width - window.width)
    distance_to_left = abs(clamped.x - left_x)
    distance_to_right = abs(right_x - clamped.x)
    snapped_x = left_x if distance_to_left <= distance_to_right else right_x
    return Point(snapped_x, clamped.y)
