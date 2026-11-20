"""把周计划渲染成可打印的 A4 表格。"""

from __future__ import annotations

import html
from datetime import date
from typing import Dict, List, Optional, Sequence

from .model import (
    DAY_NAMES,
    DEFAULT_ROWS,
    Task,
    WeeklyplanError,
    check_capacity,
    check_rows,
    group_tasks,
    week_dates,
)

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0


def _num(value: float) -> str:
    text = "%.1f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


def day_row_height_mm(rows: int) -> float:
    """按每日行数计算表格行高。"""
    size = check_rows(rows)
    return min(30.0, 205.0 / size)


def _info_markup() -> str:
    return (
        '<div class="info">'
        "<span><b>姓名</b><i></i></span>"
        "<span><b>班级</b><i></i></span>"
        "<span class=\"goal\"><b>本周目标</b><i></i></span>"
        "</div>"
    )


def _head_markup(dates: Sequence[Optional[date]]) -> str:
    cells: List[str] = []
    for index, name in enumerate(DAY_NAMES):
        css = ' class="weekend"' if index >= 5 else ""
        extra = ""
        if index < len(dates) and dates[index] is not None:
            day = dates[index]
            extra = '<span class="date">%d/%d</span>' % (day.month, day.day)
        cells.append("<th%s>%s%s</th>" % (css, name, extra))
    return "<thead><tr>%s</tr></thead>" % "".join(cells)


def _tbody(tasks: Dict[int, List[Task]], rows: int) -> str:
    body: List[str] = []
    for offset in range(rows):
        cells: List[str] = []
        for day in range(1, 8):
            css = ' class="weekend"' if day >= 6 else ""
            items = tasks.get(day, [])
            if offset < len(items):
                task = items[offset]
                content = (
                    '<div class="task"><span class="box"></span>'
                    "<span>%s</span></div>" % html.escape(task.text)
                )
            else:
                content = ""
            cells.append("<td%s>%s</td>" % (css, content))
        body.append("<tr>%s</tr>" % "".join(cells))
    return "<tbody>%s</tbody>" % "".join(body)


def render_html(
    tasks: Sequence[Task],
    title: str = "周计划",
    rows: int = DEFAULT_ROWS,
    start: Optional[date] = None,
) -> str:
    """生成完整 HTML：一周七列，每项任务带勾选框。"""
    if not isinstance(tasks, (list, tuple)):
        raise WeeklyplanError("tasks 必须是任务列表")
    for task in tasks:
        if not isinstance(task, Task):
            raise WeeklyplanError("任务列表里出现了非 Task 对象")
    if not isinstance(title, str) or not title.strip():
        raise WeeklyplanError("标题不能为空")
    size = check_rows(rows)
    check_capacity(tasks, size)
    dates = week_dates(start)
    grouped = group_tasks(tasks)

    height = day_row_height_mm(size)
    count = len(tasks)
    head = (
        '<header class="head"><h1>%s</h1>'
        '<p class="sub">%s</p>%s</header>'
        % (
            html.escape(title.strip()),
            html.escape(_range_label(dates)),
            _info_markup(),
        )
    )
    table = (
        '<table class="week"><colgroup>%s</colgroup>%s%s</table>'
        % ("".join('<col style="width:14.28%">' for _ in range(7)), _head_markup(dates), _tbody(grouped, size))
    )
    foot = (
        '<footer class="foot"><span>本周共 %d 项任务 · 完成一项在方框里打勾</span>'
        "<span>weeklyplan · A4 纵向</span></footer>" % count
    )
    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>%s · 每天 %d 行 · 共 %d 项任务</span></div>"
        % (html.escape(title.strip()), html.escape(_range_label(dates)), size, count)
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n"
        '%s\n<section class="sheet">%s%s%s</section>\n</body>\n</html>\n'
        % (
            html.escape(title.strip()),
            _style(height),
            toolbar,
            head,
            table,
            foot,
        )
    )


def _range_label(dates: Sequence[Optional[date]]) -> str:
    first = dates[0] if dates else None
    last = dates[-1] if dates else None
    if first is None or last is None:
        return "一周安排"
    return "%d 年 %d 月 %d 日 ~ %d 月 %d 日" % (
        first.year,
        first.month,
        first.day,
        last.month,
        last.day,
    )


def _style(height: float) -> str:
    template = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 8mm 0 12mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 210mm;
    margin: 0 auto 6mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 210mm;
    height: 297mm;
    margin: 0 auto 8mm;
    padding: 13mm 15mm 9mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
    page-break-after: always;
    break-after: page;
    overflow: hidden;
  }
  .head { text-align: center; }
  .head h1 {
    margin: 0;
    font-size: 21pt;
    font-weight: 600;
    letter-spacing: 5pt;
  }
  .head .sub { margin: 1.5mm 0 0; font-size: 10pt; color: #64748b; }
  .info {
    display: flex;
    gap: 5mm;
    margin: 4mm 0 3.5mm;
    font-size: 10pt;
    color: #334155;
  }
  .info span { flex: 1; display: flex; align-items: flex-end; gap: 1.5mm; }
  .info span.goal { flex: 2; }
  .info b { font-weight: 400; white-space: nowrap; }
  .info i { flex: 1; height: 4.5mm; border-bottom: 0.3mm solid #94a3b8; }
  table.week { width: 100%; border-collapse: collapse; table-layout: fixed; }
  table.week th,
  table.week td {
    border: 0.25mm solid #94a3b8;
    vertical-align: top;
    padding: 1mm 1.2mm;
  }
  table.week th {
    height: 10mm;
    background: #f1f5f9;
    font-size: 9pt;
    font-weight: 600;
    text-align: center;
    vertical-align: middle;
  }
  table.week th.weekend { background: #fef2f2; color: #b91c1c; }
  table.week th .date {
    display: block;
    margin-top: 0.6mm;
    font-size: 7pt;
    font-weight: 400;
    color: #94a3b8;
  }
  table.week td { height: __ROW_HEIGHT__mm; }
  table.week td.weekend { background: #fffafa; }
  .task {
    display: flex;
    align-items: flex-start;
    gap: 1.2mm;
    font-size: 8.5pt;
    line-height: 1.4;
    margin-bottom: 1.2mm;
    overflow-wrap: anywhere;
  }
  .task .box {
    flex: 0 0 2.8mm;
    width: 2.8mm;
    height: 2.8mm;
    margin-top: 0.5mm;
    border: 0.25mm solid #64748b;
  }
  .foot {
    margin-top: auto;
    padding-top: 2mm;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #64748b;
    border-top: 0.2mm solid #e2e8f0;
  }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""
    return template.replace("__ROW_HEIGHT__", _num(height))
