# chinese_tn 实现规划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 新增 `chinese_tn` 包，将文本中的阿拉伯数字转换为中文读法（TN，ITN 的反向），依据规格 `docs/superpowers/specs/2026-09-07-chinese-tn-design.md`。

**架构：** 与 `chinese_itn` 平级的独立包，零代码耦合。`numbers.py` 承担核心数值→中文（整数按 4 位一级分节转换、小数、逐位读），`replacer.py` 承担扫描正则 + 按类别分发（日期 > 时间 > 百分/千分 > 分数 > 比值 > 数值）。纯 `re`，无外部依赖。

**技术栈：** Python 3 标准库 `re`，沿用仓库现有 `run_test.py` + `test_cases_*.txt` 测试模式（无 pytest）。

**约定（所有任务通用）：**
- 工作目录 `d:\Chinese-ITN`，shell 为 bash（PowerShell 分隔符不适用）
- 运行测试：`python run_test.py`
- 快速断言检查用 `python - <<'PY' ... PY` heredoc
- 提交信息用中文，不加 Co-Authored-By 署名
- `test_cases_*.txt` 已被 .gitignore 忽略，不提交

---

### Task 1: 重构 run_test.py 为套件运行器

**Files:**
- Modify: `run_test.py`（全文重写）

- [ ] **Step 1: 重写 run_test.py**

把写死路径的主体抽成 `run_suite()`，输出文件名保持 ITN 原名不变：

```python
# coding: utf-8
"""
简单的测试脚本：基于 test_cases.txt 测试 chinese_itn，基于 test_cases_tn.txt 测试 chinese_tn
"""

from pathlib import Path

from chinese_itn import chinese_to_num


def run_suite(title, convert, cases_name, correct_name, wrong_name):
    """运行单个测试套件：逐条比对转换结果，输出统计与错误案例"""
    print("=" * 60)
    print(title)
    print("=" * 60)

    test_cases = []
    with open(Path(cases_name), 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ' -> ' not in line:
                continue
            input_text, expected = line.split(' -> ', 1)
            test_cases.append((input_text.strip(), expected.strip()))

    print(f"共 {len(test_cases)} 个测试用例\n")

    correct, wrong = [], []
    for input_text, expected in test_cases:
        result = convert(input_text)
        if result == expected:
            correct.append((input_text, expected))
        else:
            wrong.append((input_text, expected, result))

    print(f"✓ 正确: {len(correct)} ({len(correct)/len(test_cases)*100:.1f}%)")
    print(f"✗ 错误: {len(wrong)} ({len(wrong)/len(test_cases)*100:.1f}%)")

    if wrong:
        print("\n错误案例:")
        for i, (input_text, expected, result) in enumerate(wrong[:20]):
            print(f"  {i+1}. {input_text}")
            print(f"     期望: {expected}")
            print(f"     实际: {result}")
        if len(wrong) > 20:
            print(f"  ... 还有 {len(wrong) - 20} 个")

    with open(Path(correct_name), 'w', encoding='utf-8') as f:
        f.write("# 测试通过的用例\n# 格式: 输入 -> 期望输出\n\n")
        for input_text, expected in correct:
            f.write(f"{input_text} -> {expected}\n")

    with open(Path(wrong_name), 'w', encoding='utf-8') as f:
        f.write("# 测试未通过的用例\n# 格式: 输入 -> 期望输出 (当前: 实际输出)\n\n")
        for input_text, expected, result in wrong:
            f.write(f"{input_text} -> {expected} (当前: {result})\n")

    print(f"\n结果已保存到 {correct_name} 和 {wrong_name}")
    return len(correct), len(wrong)


if __name__ == "__main__":
    run_suite(
        "chinese_itn 测试", chinese_to_num,
        'test_cases.txt', 'test_cases_correct.txt', 'test_cases_wrong.txt',
    )
```

- [ ] **Step 2: 跑测试确认 ITN 行为不变**

Run: `python run_test.py`
Expected: `共 254 个测试用例`，`✓ 正确: 254 (100.0%)`

- [ ] **Step 3: 提交**

```bash
git add run_test.py && git commit -m "重构 run_test.py 为通用套件运行器"
```

---

### Task 2: 写 test_cases_tn.txt（预期先行）

**Files:**
- Create: `test_cases_tn.txt`

- [ ] **Step 1: 写入 TN 测试用例**

创建 `test_cases_tn.txt`，内容如下（格式与现有用例一致）：

```
# ============ 整数 ============
0 -> 零
10 -> 十
19 -> 十九
20 -> 二十
110 -> 一百一十
105 -> 一百零五
1005 -> 一千零五
2010 -> 二千零一十
100 -> 一百
1000 -> 一千
10000 -> 一万
10001 -> 一万零一
10010 -> 一万零一十
10011 -> 一万零一十一
10111 -> 一万零一百一十一
100000 -> 十万
100001 -> 十万零一
1234567 -> 一百二十三万四千五百六十七
100070000 -> 一亿零七万
100010000 -> 一亿零一万
100000001 -> 一亿零一
100070010 -> 一亿零七万零一十
-5 -> 负五

# ============ 小数 ============
3.14 -> 三点一四
0.5 -> 零点五
0.00123 -> 零点零零一二三
1.10 -> 一点一零
3.1415926 -> 三点一四一五九二六
10000.123 -> 一万点一二三
-3.14 -> 负三点一四

# ============ 逐位串（前导零或长度≥8） ============
0421 -> 零四二一
007 -> 零零七
13812345678 -> 一三八一二三四五六七八
340203193701010517 -> 三四零二三一九三七零一零一零五一七
2025 -> 两千零二十五
13702 -> 一万三千七百零二

# ============ 万/亿后缀 ============
3万 -> 三万
20.1万 -> 二十点一万
300亿 -> 三百亿
2万亿 -> 二万亿
10000.123万 -> 一万点一二三万

# ============ 百分/千分 ============
50% -> 百分之五十
32.68% -> 百分之三十二点六八
0.70% -> 百分之零点七零
1.86% -> 百分之一点八六
5‰ -> 千分之五
-5% -> 负百分之五

# ============ 分数/比值 ============
2/3 -> 三分之二
1/2 -> 二分之一
16/3 -> 三分之十六
1:3 -> 一比三
25:70 -> 二十五比七十

# ============ 日期 ============
2025年 -> 二零二五年
2025年10月3日 -> 二零二五年十月三日
2008年8月8日 -> 二零零八年八月八日
86年 -> 八六年
1919年 -> 一九一九年
10月 -> 十月
10月3日 -> 十月三日
8月29日 -> 八月二十九日
2月4号 -> 二月四号
3日 -> 三日
3号 -> 三号

# ============ 时间 ============
12:30 -> 十二点三十分
09:21 -> 九点二十一分
00:10 -> 零点十分
08:05 -> 八点零五分
23:15 -> 二十三点十五分
13:10:36 -> 十三点十分三十六秒
05:35:36 -> 五点三十五分三十六秒

# ============ 混合文本 ============
明天有62%的概率降雨 -> 明天有百分之六十二的概率降雨
现场有2/3的观众投出了赞成票 -> 现场有三分之二的观众投出了赞成票
会议定在14:30开始 -> 会议定在十四点三十分开始
2018年5月23号上午10:10 -> 二零一八年五月二十三号上午十点十分
下单3件共66.6元 -> 下单三件共六十六点六元
今年有望超300亿美元 -> 今年有望超三百亿美元
这块黄金重达324.75g -> 这块黄金重达三百二十四点七五g
尾号1702 -> 尾号一千七百零二
可以拨打12306来咨询 -> 可以拨打一万二千三百零六来咨询
每一天都比昨天更好 -> 每一天都比昨天更好
2019年 -> 两千零一九年
```

注意三条锁定行为的用例：`2025 -> 两千零二十五`（无「年」字按数值，规格已声明的不对称）、`尾号1702 -> 尾号一千七百零二`（无前导零且不足 8 位，阈值规则的既定代价）、`可以拨打12306来咨询 -> 一万二千三百零六`（同上）。

- [ ] **Step 2: 提交（用例文件被 .gitignore 忽略则无文件可提交，跳过即可）**

```bash
git status --short
```

Expected: 无 test_cases_tn.txt 出现（被忽略）。若有则 `git add` 会失败，确认后跳过。

---

### Task 3: 实现 numbers.py（核心数值转换）

**Files:**
- Create: `chinese_tn/__init__.py`
- Create: `chinese_tn/numbers.py`

- [ ] **Step 1: 创建包骨架（空实现），确认检查失败**

`chinese_tn/__init__.py`（本任务只放 docstring，`num_to_chinese` 的导出在 Task 4 接入，避免提前 import 尚不存在的 replacer）：

```python
# coding: utf-8
"""中文文本正则化 (TN)：将文本中的阿拉伯数字转换为中文读法"""
```

`chinese_tn/numbers.py` 先只写：

```python
# coding: utf-8
"""核心数值转中文：整数分级转换、小数、逐位读"""
```

Run:
```bash
python -c "from chinese_tn.numbers import int_to_chinese"
```
Expected: `ImportError: cannot import name 'int_to_chinese'`（红）

- [ ] **Step 2: 实现 numbers.py 完整代码**

```python
# coding: utf-8
"""核心数值转中文：整数分级转换、小数、逐位读"""

_DIGITS = '零一二三四五六七八九'
_SECTION_UNITS = ['', '万', '亿', '万亿']


def _section_to_chinese(n, leading):
    """转换 1..9999 的单个节（四位一级），不带头节单位

    leading: 是否为整个数的最高非零节。仅最高节的十位 1 读「十」（10->十），
    其余位置的十位 1 读「一十」（110->一百一十、10010->一万零一十）
    """
    units = ['千', '百', '十', '']
    chars = []
    for i, c in enumerate(f'{n:04d}'):
        d = int(c)
        if d == 0:
            # 节内零合并：已有内容且上一个字符不是零时才补零
            if chars and chars[-1] != '零':
                chars.append('零')
        elif d == 1 and i == 2 and not chars:
            chars.append('十' if leading else '一十')
        else:
            chars.append(_DIGITS[d] + units[i])
    if chars and chars[-1] == '零':
        chars.pop()
    return ''.join(chars)


def int_to_chinese(n):
    """整数转中文读法：100070000 -> 一亿零七万"""
    if n < 0:
        return '负' + int_to_chinese(-n)
    if n == 0:
        return '零'

    # 按低位到高位每 4 位切节
    sections = []
    while n > 0:
        n, s = divmod(n, 10000)
        sections.append(s)

    parts = []
    for i in range(len(sections) - 1, -1, -1):
        s = sections[i]
        if s == 0:
            continue
        # 节间补零：非最高节不足千位时补一个零（一亿[零]七万）
        if parts and s < 1000:
            parts.append('零')
        parts.append(_section_to_chinese(s, leading=not parts))
        parts.append(_SECTION_UNITS[i])
    return ''.join(parts)


def decimal_to_chinese(s):
    """小数字符串转中文：'3.14' -> 三点一四，'-0.5' -> 负零点五"""
    sign = ''
    if s.startswith('-'):
        sign, s = '负', s[1:]
    int_part, frac_part = s.split('.')
    # 小数部分逐位读，尾随零保留（1.10 -> 一点一零）
    return sign + int_to_chinese(int(int_part)) + '点' + ''.join(_DIGITS[int(c)] for c in frac_part)


def digitwise(digits):
    """纯数字串逐位转中文：'0421' -> 零四二一"""
    return ''.join(_DIGITS[int(c)] for c in digits)
```

- [ ] **Step 3: 跑断言检查（先失败后通过的含义：本步应在实现后全绿）**

Run:
```bash
python - <<'PY'
from chinese_tn.numbers import int_to_chinese, decimal_to_chinese, digitwise

cases = [
    (int_to_chinese, 0, '零'), (int_to_chinese, 10, '十'),
    (int_to_chinese, 19, '十九'), (int_to_chinese, 110, '一百一十'),
    (int_to_chinese, 105, '一百零五'), (int_to_chinese, 1005, '一千零五'),
    (int_to_chinese, 2010, '二千零一十'), (int_to_chinese, 10010, '一万零一十'),
    (int_to_chinese, 100070000, '一亿零七万'), (int_to_chinese, 100000001, '一亿零一'),
    (int_to_chinese, 100070010, '一亿零七万零一十'),
    (int_to_chinese, 1234567, '一百二十三万四千五百六十七'),
    (int_to_chinese, -5, '负五'),
    (decimal_to_chinese, '3.14', '三点一四'), (decimal_to_chinese, '0.5', '零点五'),
    (decimal_to_chinese, '1.10', '一点一零'), (decimal_to_chinese, '-3.14', '负三点一四'),
    (decimal_to_chinese, '10000.123', '一万点一二三'),
    (digitwise, '0421', '零四二一'), (digitwise, '13812345678', '一三八一二三四五六七八'),
]
bad = [(f.__name__, x, got, want) for f, x, want in cases if (got := f(x)) != want]
for b in bad:
    print('FAIL', b)
assert not bad
print(f'OK: {len(cases)} cases')
PY
```
Expected: `OK: 20 cases`

- [ ] **Step 4: 提交**

```bash
git add chinese_tn/__init__.py chinese_tn/numbers.py && git commit -m "chinese_tn: 核心数值转中文（整数分节/小数/逐位）"
```

---

### Task 4: 实现 replacer.py（扫描分发 + 入口），接入测试跑全套

**Files:**
- Create: `chinese_tn/replacer.py`
- Modify: `chinese_tn/__init__.py`
- Modify: `run_test.py`

- [ ] **Step 1: 实现 replacer.py**

```python
# coding: utf-8
"""扫描正则与类别分发，入口 num_to_chinese()"""

import re

from .numbers import int_to_chinese, decimal_to_chinese, digitwise

_NUM = r'-?\d+(?:\.\d+)?'

# 候选片段按优先级排列：日期 > 时间 > 百分/千分 > 分数 > 比值 > 数值
# 时间要求小时 <=23、分/秒两位且 <=59，不满足的自然落入比值（1:3、25:70）
pattern = re.compile('|'.join([
    r'(?P<date>\d{2,4}年(?:\d{1,2}月)?(?:\d{1,2}[日号])?|\d{1,2}月(?:\d{1,2}[日号])?|\d{1,2}[日号])',
    r'(?P<time>(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?)',
    rf'(?P<percent>{_NUM}[‰%])',
    r'(?P<fraction>\d+/\d+)',
    r'(?P<ratio>\d+:\d+)',
    rf'(?P<number>{_NUM}(?:万亿|万|亿)?)',
]))

_DATE_PARTS = re.compile(r'(?:(\d{2,4})年)?(?:(\d{1,2})月)?(?:(\d{1,2})([日号]))?')
_TIME_PARTS = re.compile(r'(\d{1,2}):(\d{2})(?::(\d{2}))?')
_UNIT_FACTOR = {'万': 10**4, '亿': 10**8, '万亿': 10**12}


def _convert_date(text):
    year, month, day, day_suffix = _DATE_PARTS.fullmatch(text).groups()
    out = ''
    if year:
        out += digitwise(year) + '年'
    if month:
        out += int_to_chinese(int(month)) + '月'
    if day:
        out += int_to_chinese(int(day)) + day_suffix
    return out


def _small_unit(n, unit):
    """分/秒读法：不足 10 补「零」（08:05 -> 八点零五分）"""
    return ('零' + int_to_chinese(n) if n < 10 else int_to_chinese(n)) + unit


def _convert_time(text):
    hour, minute, second = _TIME_PARTS.fullmatch(text).groups()
    out = int_to_chinese(int(hour)) + '点' + _small_unit(int(minute), '分')
    if second:
        out += _small_unit(int(second), '秒')
    return out


def _convert_percent(text):
    body, suffix = text[:-1], text[-1]
    prefix = '千分之' if suffix == '‰' else '百分之'
    if body.startswith('-'):
        return '负' + prefix + decimal_to_chinese(body[1:])
    return prefix + decimal_to_chinese(body)


def _convert_fraction(text):
    a, b = text.split('/')
    return int_to_chinese(int(b)) + '分之' + int_to_chinese(int(a))


def _convert_ratio(text):
    a, b = text.split(':')
    return int_to_chinese(int(a)) + '比' + int_to_chinese(int(b))


def _convert_number(text):
    body, unit = re.fullmatch(r'(-?\d+(?:\.\d+)?)(万亿|万|亿)?', text).groups()
    if '.' in body:
        # 带小数时不折算单位：20.1万 -> 二十点一万
        return decimal_to_chinese(body) + (unit or '')
    if unit:
        return int_to_chinese(int(body) * _UNIT_FACTOR[unit])
    digits = body.lstrip('-')
    # 前导零或长串（电话/单号类）逐位读
    if digits.startswith('0') or len(digits) >= 8:
        return ('负' if body.startswith('-') else '') + digitwise(digits)
    return int_to_chinese(int(body))


_HANDLERS = {
    'date': _convert_date,
    'time': _convert_time,
    'percent': _convert_percent,
    'fraction': _convert_fraction,
    'ratio': _convert_ratio,
    'number': _convert_number,
}


def _replace(m):
    return _HANDLERS[m.lastgroup](m.group())


def num_to_chinese(text):
    """主函数：将文本中的阿拉伯数字转换为中文读法"""
    return pattern.sub(_replace, text)
```

- [ ] **Step 2: 接入导出与测试套件**

`chinese_tn/__init__.py` 全文替换为：

```python
# coding: utf-8
"""中文文本正则化 (TN)：将文本中的阿拉伯数字转换为中文读法"""

from .replacer import num_to_chinese

__all__ = ['num_to_chinese']
```

在 `run_test.py` 顶部 import 区加：

```python
from chinese_tn import num_to_chinese
```

`__main__` 块改为依次跑两套：

```python
if __name__ == "__main__":
    run_suite(
        "chinese_itn 测试", chinese_to_num,
        'test_cases.txt', 'test_cases_correct.txt', 'test_cases_wrong.txt',
    )
    print()
    run_suite(
        "chinese_tn 测试", num_to_chinese,
        'test_cases_tn.txt', 'test_cases_tn_correct.txt', 'test_cases_tn_wrong.txt',
    )
```

- [ ] **Step 3: 跑全套测试，修到全绿**

Run: `python run_test.py`
Expected: ITN 段 `254/254 (100.0%)`，TN 段全绿（0 错误）。

若有失败，按「期望 vs 实际」修正对应转换规则——只允许修 `chinese_tn/` 内部，禁止改 test_cases_tn.txt 的期望值来迁就实现（除非是规格允许的自由裁量且经确认）。

- [ ] **Step 4: 提交**

```bash
git add chinese_tn/replacer.py chinese_tn/__init__.py run_test.py && git commit -m "chinese_tn: 扫描分发与入口，接入测试套件"
```

---

### Task 5: 更新文档（CLAUDE.md / readme.md）

**Files:**
- Modify: `CLAUDE.md`
- Modify: `readme.md`

- [ ] **Step 1: 更新 CLAUDE.md**

「项目简介」末尾追加一句：

```markdown
除 ITN 外，本库还包含反向的 TN（`chinese_tn`）：将文本中的阿拉伯数字转为中文读法。
```

「核心命令」代码块末尾追加：

```powershell
# 快速测试单条 TN 转换
python -c "from chinese_tn import num_to_chinese; print(num_to_chinese('2025年10月3日 12:30'))"
```

「项目结构」表格追加两行（放在 `run_test.py` 行之前）：

```markdown
| `chinese_tn/` | TN 核心包（ITN 的反向） |
| `chinese_tn/__init__.py` | 导出 `num_to_chinese` |
| `chinese_tn/numbers.py` | 核心数值转中文（整数分节、小数、逐位读） |
| `chinese_tn/replacer.py` | 扫描正则 + 类别分发 + `num_to_chinese()` 入口 |
```

「项目结构」表格中 `run_test.py` 行的用途改为：

```markdown
| `run_test.py` | 测试运行器，依次跑 `test_cases.txt`（ITN）与 `test_cases_tn.txt`（TN） |
```

文件末尾追加一节：

```markdown
## chinese_tn 架构

```
numbers.py (整数分节转换 / 小数 / 逐位读，无依赖)
    ↑
replacer.py (扫描正则 + 类别分发 + 入口)
    ↑
__init__.py (导出 num_to_chinese)
```

- 候选片段优先级：日期 > 时间 > 百分/千分 > 分数 > 比值 > 数值
- 时间正则要求小时 ≤23、分/秒两位 ≤59，不满足自然落入比值（1:3、25:70）
- 数值末位判定：前导零或长度 ≥8 的纯整数串逐位读，其余按数值读
- 新增转换类别：在 `replacer.py` 的 `pattern` 优先级序列中加入命名组，并注册 `_HANDLERS` 一项
```

- [ ] **Step 2: 更新 readme.md**

「简介」节追加：

```markdown
本库同时提供反向的文本正则化 (TN)：将阿拉伯数字转为中文读法，适用于 TTS 前端等场景。
```

「用法示例」节追加：

````markdown
TN 用法：

```python
from chinese_tn import num_to_chinese

text = '明天有62%的概率降雨，会议定在14:30开始'
result = num_to_chinese(text)

print(result)
```
````

- [ ] **Step 3: 跑全套测试确认无回归**

Run: `python run_test.py`
Expected: ITN 254/254，TN 全绿

- [ ] **Step 4: 提交**

```bash
git add CLAUDE.md readme.md && git commit -m "文档：补充 chinese_tn 结构与用法"
```

---

## 收尾

- [ ] `python run_test.py` 两套全绿
- [ ] `git log --oneline` 确认 4 个提交（重构运行器 / numbers / replacer+接入 / 文档）
