# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

中文逆文本正则化 (Chinese ITN)，将语音识别结果中的中文数字转为阿拉伯数字。纯 Python 实现，无外部依赖，仅使用 `re` 标准库。

## 核心命令

```powershell
# 运行全部测试
python run_test.py

# 快速测试单条转换
python -c "from chinese_itn import chinese_to_num; print(chinese_to_num('一万两千三百'))"

# 添加新测试用例后验证（编辑 test_cases.txt 再运行）
python run_test.py
```

## 项目结构

| 文件 | 用途 |
|------|------|
| `chinese_itn/` | 核心包，拆分为 5 个模块 |
| `chinese_itn/__init__.py` | 导出 `chinese_to_num` |
| `chinese_itn/mappings.py` | 映射表数据（单位、数字、习语黑名单） |
| `chinese_itn/patterns.py` | 所有正则模式定义 |
| `chinese_itn/converters.py` | 转换函数和辅助函数 |
| `chinese_itn/replacer.py` | `replace()` 替换逻辑 + `chinese_to_num()` 入口 |
| `run_test.py` | 测试运行器，读取 `test_cases.txt` 逐条比对 |
| `test_cases.txt` | 测试用例，格式 `输入 -> 期望输出` |

## 架构概览

依赖链：
```
mappings.py (纯数据)
    ↑
patterns.py (正则，依赖 mappings)
    ↑
converters.py (转换逻辑，依赖 mappings + patterns)
    ↑
replacer.py (主替换逻辑，依赖 converters)
    ↑
__init__.py (对外接口)
```

### mappings.py
- `unit_mapping`: 中文单位映射（克→g, 千米→km/h 等）
- `num_mapper`: 中文数字→ASCII 数字的单字映射
- `value_mapper`: 中文数字→整数值的映射（含位值 十百千万亿）
- `idioms`: 成语黑名单

### patterns.py
- 总筛选正则 `pattern`：扫描文本中可能含数字的片段
- 7 个子模式：纯数字、数值、百分数、分数、比值、时间、日期

### converters.py
- `strip_unit()`: 剥离并映射尾随单位
- `is_consecutive_value()` / `split_consecutive_value()`: 处理连续数值（十五十六十七→15 16 17）
- 每种数字类型的转换器：`convert_pure_num`, `convert_value_num`, `convert_percent_permille_value`, `convert_fraction_value`, `convert_ratio_value`, `convert_time_value`, `convert_date_value`

### replacer.py
- `replace()`: 按优先级链式判断：成语→模糊→时间→纯数字→连续数值→数值→百分数→分数→比值→日期
- `chinese_to_num()`: 调用 `pattern.sub(replace, text)` 全局替换

## 设计约定

- 测试用例文件每行一条，`#` 开头为注释，空行分隔不同类别
- 转换优先级：黑名单（成语/习语）> 模糊表达（含"几"）> 时间 > 纯数字 > 连续数值 > 数值 > 百分数 > 分数 > 比值 > 日期
- 添加新数字类型时需在 `replace()` 的优先级链中插入对应的判断分支
