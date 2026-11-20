"""weeklyplan：A4 可打印学生周计划表。"""

from __future__ import annotations

from .model import (
    DAY_ALIASES,
    DAY_NAMES,
    DEFAULT_ROWS,
    MAX_ROWS,
    MAX_TASK,
    MIN_ROWS,
    Task,
    WeeklyplanError,
    check_capacity,
    check_rows,
    format_tasks,
    group_tasks,
    load_tasks,
    parse_day,
    parse_start,
    parse_tasks,
    week_dates,
)
from .render import day_row_height_mm, render_html

__version__ = "0.1.0"

__all__ = [
    "DAY_ALIASES",
    "DAY_NAMES",
    "DEFAULT_ROWS",
    "MAX_ROWS",
    "MAX_TASK",
    "MIN_ROWS",
    "Task",
    "WeeklyplanError",
    "check_capacity",
    "check_rows",
    "day_row_height_mm",
    "format_tasks",
    "group_tasks",
    "load_tasks",
    "parse_day",
    "parse_start",
    "parse_tasks",
    "render_html",
    "week_dates",
    "__version__",
]
