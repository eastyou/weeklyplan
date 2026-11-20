"""model 模块单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import List

from weeklyplan.model import (
    MAX_TASK,
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


class ParseDayTest(unittest.TestCase):
    def test_aliases(self) -> None:
        self.assertEqual(parse_day("周一"), 1)
        self.assertEqual(parse_day("星期三"), 3)
        self.assertEqual(parse_day("礼拜五"), 5)
        self.assertEqual(parse_day("周日"), 7)
        self.assertEqual(parse_day("周天"), 7)
        self.assertEqual(parse_day("1"), 1)
        self.assertEqual(parse_day("7"), 7)
        self.assertEqual(parse_day(" 三 "), 3)

    def test_invalid(self) -> None:
        for value in ("星期八", "", "monday", "8"):
            with self.assertRaises(WeeklyplanError):
                parse_day(value)

    def test_non_text(self) -> None:
        with self.assertRaises(WeeklyplanError):
            parse_day(1)  # type: ignore[arg-type]


class ParseTasksTest(unittest.TestCase):
    def test_without_header(self) -> None:
        tasks = parse_tasks("周一,背单词\n周三,做习题\n")
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].day, 1)
        self.assertEqual(tasks[0].text, "背单词")

    def test_headers(self) -> None:
        for header in ("星期,任务", "日期,内容", "周,计划"):
            tasks = parse_tasks(header + "\n周一,背单词\n")
            self.assertEqual(len(tasks), 1, header)

    def test_extra_column(self) -> None:
        with self.assertRaises(WeeklyplanError) as ctx:
            parse_tasks("周一,背单词,备注\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_missing_task(self) -> None:
        with self.assertRaises(WeeklyplanError) as ctx:
            parse_tasks("周一\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_missing_day(self) -> None:
        with self.assertRaises(WeeklyplanError) as ctx:
            parse_tasks("，背单词\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_bad_day(self) -> None:
        with self.assertRaises(WeeklyplanError) as ctx:
            parse_tasks("星期八,背单词\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_empty(self) -> None:
        with self.assertRaises(WeeklyplanError):
            parse_tasks("\n\n")

    def test_non_text(self) -> None:
        with self.assertRaises(WeeklyplanError):
            parse_tasks(123)  # type: ignore[arg-type]

    def test_task_too_long(self) -> None:
        with self.assertRaises(WeeklyplanError):
            parse_tasks("周一,%s\n" % ("字" * (MAX_TASK + 1)))

    def test_bom(self) -> None:
        tasks = parse_tasks("\ufeff周一,背单词\n")
        self.assertEqual(tasks[0].text, "背单词")

    def test_load_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.csv"
            path.write_text("周一,背单词\n", encoding="utf-8")
            self.assertEqual(load_tasks(path)[0].day, 1)

    def test_load_gbk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.csv"
            path.write_bytes("周一,背单词\n".encode("gbk"))
            self.assertEqual(load_tasks(path)[0].text, "背单词")

    def test_unknown_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.csv"
            path.write_bytes(b"\xff\xff\xff")
            with self.assertRaises(WeeklyplanError):
                load_tasks(path)

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_tasks("/tmp/definitely-missing-weeklyplan.csv")


class TaskTest(unittest.TestCase):
    def test_day_name(self) -> None:
        self.assertEqual(Task(day=3, text="做习题").day_name, "周三")

    def test_bad_day(self) -> None:
        for value in (0, 8, True, "1"):
            with self.assertRaises(WeeklyplanError):
                Task(day=value, text="任务")  # type: ignore[arg-type]

    def test_empty_text(self) -> None:
        with self.assertRaises(WeeklyplanError):
            Task(day=1, text="  ")

    def test_non_text(self) -> None:
        with self.assertRaises(WeeklyplanError):
            Task(day=1, text=1)  # type: ignore[arg-type]

    def test_trim(self) -> None:
        self.assertEqual(Task(day=1, text=" 背单词 ").text, "背单词")


class StartTest(unittest.TestCase):
    def test_valid_monday(self) -> None:
        self.assertEqual(parse_start("2026-11-23"), date(2026, 11, 23))

    def test_bad_format(self) -> None:
        for value in ("2026/11/23", "2026-1-1", "abc"):
            with self.assertRaises(WeeklyplanError):
                parse_start(value)

    def test_not_monday(self) -> None:
        with self.assertRaises(WeeklyplanError) as ctx:
            parse_start("2026-11-21")
        self.assertIn("周一", str(ctx.exception))

    def test_bad_date(self) -> None:
        with self.assertRaises(WeeklyplanError):
            parse_start("2026-02-30")

    def test_non_text(self) -> None:
        with self.assertRaises(WeeklyplanError):
            parse_start(20261123)  # type: ignore[arg-type]

    def test_week_dates(self) -> None:
        days = week_dates(date(2026, 11, 23))
        self.assertEqual(days[0], date(2026, 11, 23))
        self.assertEqual(days[-1], date(2026, 11, 29))

    def test_week_dates_none(self) -> None:
        self.assertEqual(week_dates(None), [None] * 7)

    def test_week_dates_bad(self) -> None:
        with self.assertRaises(WeeklyplanError):
            week_dates("2026-11-23")  # type: ignore[arg-type]


class GroupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tasks: List[Task] = [
            Task(day=1, text="背单词"),
            Task(day=1, text="做习题"),
            Task(day=7, text="整理笔记"),
        ]

    def test_group(self) -> None:
        grouped = group_tasks(self.tasks)
        self.assertEqual(len(grouped[1]), 2)
        self.assertEqual(len(grouped[7]), 1)
        self.assertEqual(grouped[3], [])

    def test_empty(self) -> None:
        grouped = group_tasks([])
        self.assertEqual(set(grouped.keys()), set(range(1, 8)))

    def test_non_list(self) -> None:
        with self.assertRaises(WeeklyplanError):
            group_tasks("tasks")  # type: ignore[arg-type]

    def test_non_task(self) -> None:
        with self.assertRaises(WeeklyplanError):
            group_tasks(["任务"])  # type: ignore[list-item]

    def test_capacity(self) -> None:
        self.assertEqual(check_capacity(self.tasks, 8), 2)

    def test_capacity_exceeded(self) -> None:
        tasks = [Task(day=1, text="任务%d" % index) for index in range(9)]
        with self.assertRaises(WeeklyplanError) as ctx:
            check_capacity(tasks, 8)
        self.assertIn("周一", str(ctx.exception))

    def test_capacity_empty(self) -> None:
        self.assertEqual(check_capacity([], 8), 0)

    def test_capacity_bad_rows(self) -> None:
        with self.assertRaises(WeeklyplanError):
            check_capacity(self.tasks, 4)

    def test_check_rows(self) -> None:
        self.assertEqual(check_rows(5), 5)
        self.assertEqual(check_rows(12), 12)
        with self.assertRaises(WeeklyplanError):
            check_rows(4)
        with self.assertRaises(WeeklyplanError):
            check_rows(True)  # type: ignore[arg-type]

    def test_format_roundtrip(self) -> None:
        text = format_tasks(self.tasks)
        again = parse_tasks(text)
        self.assertEqual([task.text for task in again], [task.text for task in self.tasks])

    def test_format_empty(self) -> None:
        with self.assertRaises(WeeklyplanError):
            format_tasks([])

    def test_format_non_task(self) -> None:
        with self.assertRaises(WeeklyplanError):
            format_tasks(["任务"])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
