"""render 模块单元测试。"""

from __future__ import annotations

import unittest
from datetime import date
from typing import List

from weeklyplan.model import Task, WeeklyplanError
from weeklyplan.render import day_row_height_mm, render_html


def make_tasks() -> List[Task]:
    return [
        Task(day=1, text="背单词"),
        Task(day=1, text="做习题"),
        Task(day=7, text="整理笔记"),
    ]


class RenderHtmlTest(unittest.TestCase):
    def test_basic_document(self) -> None:
        page = render_html(make_tasks())
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("A4 portrait", page)
        self.assertIn("周计划", page)

    def test_day_headers(self) -> None:
        page = render_html([])
        for name in ("周一", "周二", "周三", "周四", "周五", "周六", "周日"):
            self.assertIn(">%s" % name, page)

    def test_blank_grid(self) -> None:
        page = render_html([], rows=8)
        self.assertEqual(page.count("<td"), 56)

    def test_task_text_and_boxes(self) -> None:
        page = render_html(make_tasks())
        self.assertIn("背单词", page)
        self.assertIn("整理笔记", page)
        self.assertEqual(page.count('class="box"'), 3)

    def test_weekend_headers(self) -> None:
        page = render_html([])
        self.assertEqual(page.count('<th class="weekend">'), 2)

    def test_dates_shown(self) -> None:
        page = render_html([], start=date(2026, 11, 23))
        self.assertIn("11/23", page)
        self.assertIn("11/29", page)
        self.assertIn("2026 年 11 月 23 日", page)

    def test_no_dates(self) -> None:
        page = render_html([])
        self.assertIn("一周安排", page)
        self.assertNotIn('class="date"', page)

    def test_footer_count(self) -> None:
        page = render_html(make_tasks())
        self.assertIn("本周共 3 项任务", page)

    def test_title_escaped(self) -> None:
        page = render_html([], title="<周计划>")
        self.assertIn("&lt;周计划&gt;", page)

    def test_info_fields(self) -> None:
        page = render_html([])
        for label in ("姓名", "班级", "本周目标"):
            self.assertIn("<b>%s</b>" % label, page)

    def test_capacity_error(self) -> None:
        tasks = [Task(day=1, text="任务%d" % index) for index in range(9)]
        with self.assertRaises(WeeklyplanError):
            render_html(tasks, rows=8)

    def test_non_list(self) -> None:
        with self.assertRaises(WeeklyplanError):
            render_html("tasks")  # type: ignore[arg-type]

    def test_non_task(self) -> None:
        with self.assertRaises(WeeklyplanError):
            render_html(["任务"])  # type: ignore[list-item]

    def test_empty_title(self) -> None:
        with self.assertRaises(WeeklyplanError):
            render_html([], title=" ")

    def test_bad_rows(self) -> None:
        with self.assertRaises(WeeklyplanError):
            render_html([], rows=4)

    def test_bad_start(self) -> None:
        with self.assertRaises(WeeklyplanError):
            render_html([], start="2026-11-23")  # type: ignore[arg-type]

    def test_row_height(self) -> None:
        self.assertEqual(day_row_height_mm(5), 30.0)
        self.assertAlmostEqual(day_row_height_mm(8), 25.625)
        with self.assertRaises(WeeklyplanError):
            day_row_height_mm(4)


if __name__ == "__main__":
    unittest.main()
