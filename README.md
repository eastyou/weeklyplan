# weeklyplan

[![CI](https://github.com/eastyou/weeklyplan/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/weeklyplan/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给学生用的周计划表生成器：把「星期,任务」整理成 CSV，一条命令生成一页 A4 可打印周计划。**零依赖，不联网，打印即用。**

七天七列，每项任务前面带勾选框；不传任务文件也能生成空白周计划，打印出来手写。指定本周周一的日期后，表头会自动标出每一天的日期。

## 特性

- **一周七列**：周一到周日固定排列，周末浅红底，任务按星期自动归位
- **勾选框**：每项任务前一个小方框，完成一项打一个勾
- **日期标注**：`--start 2026-11-23` 后表头显示 11/23 ~ 11/29，并校验必须是周一
- **空白模式**：不传 `-i` 就生成空白周计划，适合统一打印发给学生
- **行数可调**：`--rows 5~12`，每天能写的任务数量可控，超出会明确报错
- **星期宽松**：`周一`、`星期一`、`礼拜一`、`1`、`一` 都能识别
- **逐行校验**：缺星期、缺任务、多余列、任务超长都会指出具体行号
- **编码兼容**：UTF-8（含 BOM）与 GBK 自动识别，Excel 导出的 CSV 可直接用
- **68 个单元测试**：覆盖任务解析、星期归一化、日期计算、容量校验、渲染与命令行

## 安装

```bash
pip install weeklyplan
```

也可以直接下载源码，在项目目录里运行：

```bash
python -m weeklyplan --help
```

## 用法

准备任务表 `任务.csv`：

```csv
星期,任务
周一,背单词 20 个
周一,完成数学练习册第 12 页
周三,整理错题本
周六,阅读课外书 30 分钟
```

生成带日期的周计划：

```bash
python -m weeklyplan -i 任务.csv --start 2026-11-23 -o 周计划.html
```

生成空白周计划：

```bash
python -m weeklyplan --rows 6 -o 空白周计划.html
```

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `-i, --input` | 任务 CSV（星期,任务）；不传则生成空白表 | 空 |
| `-o, --output` | 输出 HTML 路径 | `周计划.html` |
| `--rows` | 每天行数 5~12 | `8` |
| `--start` | 本周周一日期 `YYYY-MM-DD` | 空 |
| `--title` | 页面标题 | `周计划` |

### 任务格式

```csv
星期,任务
周一,背单词
周三,做习题
```

- 表头可有可无，支持 `星期/任务`、`日期/内容`、`周/计划`
- 星期支持 `周一~周日`、`星期一~星期日`、`1~7`、`一~日`
- 同一星期可以写多项任务，但每天不能超过 `--rows`
- 任务内容最多 40 个字符
- 编码支持 UTF-8（含 BOM）与 GBK

## 打印

用浏览器打开生成的 HTML，按 `Ctrl/Cmd + P`：

- 纸张：A4 纵向
- 边距：无 / 默认
- 勾选「背景图形」，周末底色才会打印

## 项目结构

```text
weeklyplan/
├── weeklyplan/
│   ├── model.py    # 任务解析、星期归一化、日期与容量校验
│   ├── render.py   # A4 周计划排版
│   └── cli.py      # 命令行入口
├── tests/          # 68 个单元测试
└── examples/       # 示例任务表
```

## 开发

```bash
python -m unittest discover -s tests
```

## 许可证

[MIT](LICENSE) © 2026 eastyou
