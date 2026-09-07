# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

中文逆文本正则化 (Chinese ITN)，将语音识别结果中的中文数字转为阿拉伯数字。纯 Python 实现，无外部依赖，仅使用 `re` 标准库。

除 ITN 外，本库还包含反向的 TN（`chinese_tn`）：将文本中的阿拉伯数字转为中文读法。

## 核心命令

```powershell
# 运行全部测试
python run_test.py

# 快速测试单条转换
python -c "from chinese_itn import chinese_to_num; print(chinese_to_num('一万两千三百'))"

# 快速测试单条 TN 转换
python -c "from chinese_tn import num_to_chinese; print(num_to_chinese('2025年10月3日 12:30'))"

# 添加新测试用例后验证（编辑 test_cases.txt 再运行）
python run_test.py
```

## 项目结构

| 文件 | 用途 |
|------|------|
| `chinese_itn/` | 核心包，拆分为 6 个模块 |
| `chinese_itn/__init__.py` | 导出 `chinese_to_num` |
| `chinese_itn/mappings.py` | 映射表数据（单位、数字、习语黑名单） |
| `chinese_itn/utils.py` | 底层通用字符与物理单位剥离等基础辅助工具 |
| `chinese_itn/patterns.py` | 全局正则筛选模式定义 |
| `chinese_itn/sequence_parser.py` | 词法分析 (Lexer) 与大数序列解析器 (Parser) |
| `chinese_itn/ranges.py` | 范围表达式转换 |
| `chinese_itn/replacer.py` | 语法树规约管线 (Parser Pipeline) + `chinese_to_num()` 入口 |
| `chinese_tn/` | TN 核心包（ITN 的反向） |
| `chinese_tn/__init__.py` | 导出 `num_to_chinese` |
| `chinese_tn/numbers.py` | 核心数值转中文（整数分节、小数、逐位读） |
| `chinese_tn/tables.py` | 纯数据表（货币、公制单位、号码上下文词、车牌省份字） |
| `chinese_tn/categories.py` | 类别表：24 个 (名称, 正则, 处理函数) 三元组 |
| `chinese_tn/replacer.py` | 薄引擎：合成类别表为单条正则 + 单趟分发 + `num_to_chinese()` 入口 |
| `run_test.py` | 测试运行器，依次跑 `test_cases.txt`（ITN）与 `test_cases_tn.txt`（TN） |
| `test_cases.txt` | 测试用例，格式 `输入 -> 期望输出` |

## 架构概览

依赖链（标准的有向无环 DAG 架构）：
```
mappings.py (纯映射数据)
    ↑
utils.py (基础字符与单位清洗，依赖 mappings)
    ↑
patterns.py (全局筛选正则，依赖 mappings)
    ↑
sequence_parser.py (Lexer + 序列 Parser，依赖 mappings + utils)
    ↑
ranges.py (范围解析器，依赖 sequence_parser)
    ↑
replacer.py (规约管线入口，依赖 utils + sequence_parser + ranges)
    ↑
__init__.py (对外接口)
```

### mappings.py
- `unit_mapping`: 中文单位映射（克→g, 千米→km/h 等）
- `num_mapper`: 中文数字→ASCII 数字的单字映射
- `value_mapper`: 中文数字→整数值的映射（含位值 十百千万亿）
- `idioms`: 成语黑名单

### utils.py
- `strip_unit()`: 剥离并映射尾随物理单位（例如将千米映射为 km/h）
- `convert_pure_num()`: 纯数字单字序列翻译（例如将二零二五翻译为 2025）

### patterns.py
- 总筛选正则 `pattern`：高效扫描文本中可能含数字的片段，作为整个解析的前置漏斗

### sequence_parser.py
- `tokenize()`: 词法分析 (Lexer)，将中文数字字符串拆为 Token 流
- `parse_sequence()`: 解析含十百千万亿的数字序列
- `parse_tokens()`: 将 Token 列表解析为数值列表

### ranges.py
- `is_range_expression()`: 检测范围表达式（X到Y）
- `convert_range_expression()`: 转换范围表达式为 `X-Y` 格式

### replacer.py
- **语法树规约管线**：Token 流依次经 7 个规约器匹配，首个非 `None` 结果即终止
- `try_reduce_percent()`: 百分比/千分比（百分之三十→30%）
- `try_reduce_fraction()`: 分数（三分之二→2/3）
- `try_reduce_ratio()`: 比值（一比三→1:3）
- `try_reduce_time()`: 时间（十二点三十分五秒→12:30:05）
- `try_reduce_date()`: 日期（二零二五年十月三日→2025年10月3日）
- `try_reduce_range()`: 范围表达式（十五到二十→15-20）
- `try_reduce_numerical()`: 纯数字/数值/数字序列
- `replace()`: `pattern.sub` 回调，成语/模糊表达拦截 → 词法分析 → 规约管线
- `chinese_to_num()`: 入口函数

## 设计约定

- 测试用例文件每行一条，`#` 开头为注释，空行分隔不同类别
- 优先级：成语/习语 > 模糊表达 > 百分比 > 分数 > 比值 > 时间 > 日期 > 范围表达式 > 数值解析 > 降级未匹配
- 所有规约器签名统一为 `(tokens, original)`，使用 `for` 循环遍历规约器链，`for...else` 处理全不匹配的降级
- 新增规约器时：①定义 `try_reduce_xxx(tokens, original)` 返回字符串或 `None`  ②在 `replacer.py` 的管线列表中添加一行即可

## chinese_tn 架构

依赖链：

```
numbers.py (整数分节转换 / 小数 / 逐位读，无依赖)
    ↑
tables.py (纯数据：货币、公制单位、号码上下文词、车牌省份字)
    ↑
categories.py (类别表：24 个 (名称, 正则, 处理函数) 三元组)
    ↑
replacer.py (薄引擎：合成正则 + 单趟分发 + 入口)
    ↑
__init__.py (导出 num_to_chinese)
```

核心抽象是**类别**：一个类别 = (名称, 局部正则, 处理函数) 三元组，自包含。引擎把类别表合成一条命名组交替正则做单趟扫描，按 `lastgroup` 分发；表序即优先级（同一位置按交替顺序取首个匹配）。歧义符号裁决表（`-` `/` `:` 的多义消解顺序）写在 categories.py 文件头。

- 候选片段优先级：斜杠/ISO日期 > 中文日期 > 时间 > 百分/千分 > 分数 > 比值 > 温度 > 裸角度 > 货币 > 电话 > 车牌 > 型号 > 号码上下文 > 千分位 > 科学计数 > 公制单位 > 字母代号 > 数字代号 > 连字符分段 > 正负号 > 算式 > 范围 > 数值
- 字母数字代号（TTS 接入约定）：字母+数字紧贴（C919、A4、1080P）逐位读「零」，仅「航班」语境读「幺」；≥3 段连字符数字（ISBN）逐位+空格分段；电话/号码分段间用空格停顿（不用逗号，避免 TTS 句内韵律）
- 单位匹配：多字母单位大小写不敏感，单字母仅小写（`L` 除外——升的标准符号），避免 `5G`、`3M` 代号误判单位
- 时间正则要求小时 ≤23、分/秒两位 ≤59，不满足自然落入比值（1:3、25:70）
- 读法三分：数值读（`int_to_chinese`/`decimal_to_chinese`）、逐位「一」（`digitwise`）、逐位「幺」（`digitwise(s, one='幺')`，仅号码语境）
- 数值末位判定：前导零、≥14 位、或 11 位且 1 开头（手机号）逐位读，其余按数值读
- 标准书面读法，全用「二」不用「两」
- 新增转换类别：在 `categories.py` 的 `CATEGORIES` 表中按优先级插入一个三元组即可，引擎不改
