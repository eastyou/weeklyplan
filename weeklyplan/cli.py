"""命令行入口：生成可打印的学生周计划表。"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence

from .model import (
    DEFAULT_ROWS,
    MAX_ROWS,
    MIN_ROWS,
    Task,
    WeeklyplanError,
    load_tasks,
    parse_start,
)
from .render import render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weeklyplan",
        description="学生周计划表：任务 CSV 一键生成 A4 可打印周计划",
    )
    parser.add_argument("--version", action="version", version="weeklyplan 0.1.0")
    parser.add_argument(
        "-i",
        "--input",
        default=None,
        help="任务 CSV（星期,任务）；不传则生成空白周计划",
    )
    parser.add_argument(
        "-o", "--output", default="周计划.html", help="输出 HTML 路径"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="每天行数 %d~%d，默认 %d" % (MIN_ROWS, MAX_ROWS, DEFAULT_ROWS),
    )
    parser.add_argument(
        "--start", default=None, help="本周周一日期 YYYY-MM-DD，显示每一天的日期"
    )
    parser.add_argument("--title", default="周计划", help="页面标题")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        tasks: List[Task] = load_tasks(args.input) if args.input else []
        start: Optional[date] = parse_start(args.start) if args.start else None
        page = render_html(tasks, title=args.title, rows=args.rows, start=start)
    except WeeklyplanError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取任务失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    print(
        "已生成 %s：%d 项任务，每天 %d 行%s"
        % (
            args.output,
            len(tasks),
            args.rows,
            "，本周从 %s 开始" % start.isoformat() if start else "",
        )
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
