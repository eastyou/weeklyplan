"""命令行入口单元测试。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List

from weeklyplan.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.tasks = self.root / "tasks.csv"
        self.tasks.write_text("星期,任务\n周一,背单词\n周三,做习题\n", encoding="utf-8")
        self.target = self.root / "plan.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> int:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return main(argv)

    def test_blank_plan(self) -> None:
        code = self.run_cli(["-o", str(self.target)])
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("周计划", page)
        self.assertNotIn('class="box"', page)

    def test_with_tasks(self) -> None:
        code = self.run_cli(["-i", str(self.tasks), "-o", str(self.target)])
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("背单词", page)
        self.assertEqual(page.count('class="box"'), 2)

    def test_start_date(self) -> None:
        code = self.run_cli(
            ["-o", str(self.target), "--start", "2026-11-23"]
        )
        self.assertEqual(code, 0)
        self.assertIn("11/23", self.target.read_text(encoding="utf-8"))

    def test_custom_rows(self) -> None:
        code = self.run_cli(["-o", str(self.target), "--rows", "5"])
        self.assertEqual(code, 0)
        self.assertIn("每天 5 行", self.target.read_text(encoding="utf-8"))

    def test_invalid_rows(self) -> None:
        code = self.run_cli(["-o", str(self.target), "--rows", "4"])
        self.assertEqual(code, 2)
        self.assertFalse(self.target.exists())

    def test_invalid_start(self) -> None:
        code = self.run_cli(["-o", str(self.target), "--start", "2026-11-21"])
        self.assertEqual(code, 2)

    def test_capacity_error(self) -> None:
        many = self.root / "many.csv"
        rows = ["周一,任务%d" % index for index in range(13)]
        many.write_text("\n".join(rows) + "\n", encoding="utf-8")
        code = self.run_cli(["-i", str(many), "-o", str(self.target), "--rows", "12"])
        self.assertEqual(code, 2)

    def test_missing_file(self) -> None:
        code = self.run_cli(
            ["-i", str(self.root / "missing.csv"), "-o", str(self.target)]
        )
        self.assertEqual(code, 1)

    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
