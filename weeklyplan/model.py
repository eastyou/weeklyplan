"""周计划数据模型：任务解析、星期归一化与日期计算。"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

MIN_ROWS = 5
MAX_ROWS = 12
DEFAULT_ROWS = 8
MAX_TASK = 40

DAY_NAMES: Tuple[str, ...] = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
DAY_ALIASES: Dict[str, int] = {
    "周一": 1, "星期一": 1, "礼拜一": 1, "一": 1, "1": 1,
    "周二": 2, "星期二": 2, "礼拜二": 2, "二": 2, "2": 2,
    "周三": 3, "星期三": 3, "礼拜三": 3, "三": 3, "3": 3,
    "周四": 4, "星期四": 4, "礼拜四": 4, "四": 4, "4": 4,
    "周五": 5, "星期五": 5, "礼拜五": 5, "五": 5, "5": 5,
    "周六": 6, "星期六": 6, "礼拜六": 6, "六": 6, "6": 6,
    "周日": 7, "周天": 7, "星期日": 7, "星期天": 7, "礼拜天": 7, "日": 7, "天": 7, "7": 7,
}
TASK_HEADERS = {"任务", "内容", "计划", "事项"}
DAY_HEADERS = {"星期", "日期", "周"}
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class WeeklyplanError(ValueError):
    """任务、星期或参数不合法。"""


@dataclass(frozen=True)
class Task:
    """一项周计划任务：星期几与任务内容。"""

    day: int
    text: str

    def __post_init__(self) -> None:
        if isinstance(self.day, bool) or not isinstance(self.day, int):
            raise WeeklyplanError("星期必须是 1~7 的整数")
        if not 1 <= self.day <= 7:
            raise WeeklyplanError("星期必须在 1~7 之间，当前是 %d" % self.day)
        if not isinstance(self.text, str):
            raise WeeklyplanError("任务内容必须是文本，当前是 %r" % (self.text,))
        text = self.text.strip()
        if not text:
            raise WeeklyplanError("任务内容不能为空")
        if len(text) > MAX_TASK:
            raise WeeklyplanError(
                "任务内容最多 %d 个字符，当前 %d 个" % (MAX_TASK, len(text))
            )
        object.__setattr__(self, "text", text)

    @property
    def day_name(self) -> str:
        """任务的星期名称，例如「周三」。"""
        return DAY_NAMES[self.day - 1]


def _decode(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise WeeklyplanError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            continue
    raise WeeklyplanError("无法识别文件编码，请另存为 UTF-8 或 GBK 后重试")


def parse_day(value: str) -> int:
    """把「周三」「星期三」「3」等写法统一成 1~7。"""
    if not isinstance(value, str):
        raise WeeklyplanError("星期必须是文本")
    text = value.strip()
    if text not in DAY_ALIASES:
        raise WeeklyplanError(
            "无法识别的星期：%s（可用周一~周日或 1~7）" % text
        )
    return DAY_ALIASES[text]


def _is_header(cells: Sequence[str]) -> bool:
    if len(cells) < 2:
        return False
    return cells[0] in DAY_HEADERS and cells[1] in TASK_HEADERS


def parse_tasks(text: str, source: str = "输入内容") -> List[Task]:
    """解析任务 CSV：星期,任务；表头可选。"""
    if not isinstance(text, str):
        raise WeeklyplanError("任务内容必须是文本")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    tasks: List[Task] = []
    header_checked = False
    for line_no, row in enumerate(reader, start=1):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        if not header_checked:
            header_checked = True
            if _is_header(cells):
                continue
        if len(cells) > 2:
            raise WeeklyplanError(
                "%s 第 %d 行有 %d 列，最多 2 列（星期,任务）"
                % (source, line_no, len(cells))
            )
        if len(cells) < 2 or not cells[1]:
            raise WeeklyplanError("%s 第 %d 行缺少任务内容" % (source, line_no))
        day_text, content = cells[0], cells[1]
        if not day_text:
            raise WeeklyplanError("%s 第 %d 行缺少星期" % (source, line_no))
        try:
            tasks.append(Task(day=parse_day(day_text), text=content))
        except WeeklyplanError as exc:
            raise WeeklyplanError("%s 第 %d 行：%s" % (source, line_no, exc)) from exc
    if not tasks:
        raise WeeklyplanError("%s 中没有有效的任务" % source)
    return tasks


def load_tasks(path: Union[str, Path]) -> List[Task]:
    """读取任务文件并解析。"""
    target = Path(path)
    return parse_tasks(_decode(target.read_bytes()), source=str(target))


def check_rows(rows: int) -> int:
    """校验每周行数（每天最多几项任务）。"""
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise WeeklyplanError("行数必须是整数")
    if not MIN_ROWS <= rows <= MAX_ROWS:
        raise WeeklyplanError(
            "行数必须在 %d~%d 之间，当前是 %d" % (MIN_ROWS, MAX_ROWS, rows)
        )
    return rows


def parse_start(value: str) -> date:
    """严格解析 YYYY-MM-DD 的起始日期。"""
    if not isinstance(value, str):
        raise WeeklyplanError("起始日期必须是文本")
    text = value.strip()
    if not _DATE_PATTERN.match(text):
        raise WeeklyplanError("起始日期格式必须是 YYYY-MM-DD，例如 2026-11-23")
    try:
        day = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise WeeklyplanError("日期不存在：%s" % text) from exc
    if not 1900 <= day.year <= 2100:
        raise WeeklyplanError("年份必须在 1900~2100 之间")
    if day.weekday() != 0:
        raise WeeklyplanError(
            "起始日期必须是周一，%s 是%s" % (text, DAY_NAMES[day.weekday()])
        )
    return day


def week_dates(start: Optional[date]) -> List[Optional[date]]:
    """返回一周七天的日期；未指定起始日期时全为 None。"""
    if start is None:
        return [None] * 7
    if not isinstance(start, date):
        raise WeeklyplanError("起始日期必须是 date 对象或 None")
    return [date.fromordinal(start.toordinal() + offset) for offset in range(7)]


def group_tasks(tasks: Sequence[Task]) -> Dict[int, List[Task]]:
    """按星期分组，缺少任务的星期返回空列表。"""
    grouped: Dict[int, List[Task]] = {day: [] for day in range(1, 8)}
    if not isinstance(tasks, (list, tuple)):
        raise WeeklyplanError("任务列表必须是列表")
    for task in tasks:
        if not isinstance(task, Task):
            raise WeeklyplanError("任务列表里出现了非 Task 对象")
        grouped[task.day].append(task)
    return grouped


def check_capacity(tasks: Sequence[Task], rows: int) -> int:
    """确认每天的任务数不超过行数，返回最大任务数。"""
    size = check_rows(rows)
    grouped = group_tasks(tasks)
    for day in range(1, 8):
        count = len(grouped[day])
        if count > size:
            raise WeeklyplanError(
                "%s有 %d 项任务，超过每页 %d 行，请减少任务或增大 --rows"
                % (DAY_NAMES[day - 1], count, size)
            )
    return max(len(grouped[day]) for day in range(1, 8)) if tasks else 0


def format_tasks(tasks: Sequence[Task]) -> str:
    """把任务写回 CSV 文本。"""
    if not isinstance(tasks, (list, tuple)) or not tasks:
        raise WeeklyplanError("任务列表不能为空")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["星期", "任务"])
    for task in tasks:
        if not isinstance(task, Task):
            raise WeeklyplanError("任务列表里出现了非 Task 对象")
        writer.writerow([task.day_name, task.text])
    return buffer.getvalue()
