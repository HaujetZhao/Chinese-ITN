"""
Tokenizer+Parser 架构的中文数字序列解析器

用于在主库 else 分支中尝试拆分混合数字序列。
"""

import re
from dataclasses import dataclass
from .mappings import common_units


# ============================================================
# Token 定义
# ============================================================

@dataclass
class Token:
    type: str     # 'DIGIT' | 'TEN' | 'HUNDRED' | 'THOUSAND' | 'TEN_THOUSAND' | 'HUNDRED_MILLION' | 'ZERO' | 'DOT'
    value: int    # 对应的数值
    char: str     # 原始字符
    pos: int      # 在源文本中的位置


# ============================================================
# 词法分析器
# ============================================================

_CHAR_TOKEN_MAP = {
    '零': ('ZERO', 0),
    '一': ('DIGIT', 1),  '二': ('DIGIT', 2),  '三': ('DIGIT', 3),
    '四': ('DIGIT', 4),  '五': ('DIGIT', 5),  '六': ('DIGIT', 6),
    '七': ('DIGIT', 7),  '八': ('DIGIT', 8),  '九': ('DIGIT', 9),
    '幺': ('DIGIT', 1),  '两': ('DIGIT', 2),
    '十': ('TEN', 10),
    '百': ('HUNDRED', 100),
    '千': ('THOUSAND', 1000),
    '万': ('TEN_THOUSAND', 10000),
    '亿': ('HUNDRED_MILLION', 100000000),
    '点': ('DOT', 0),
}


def tokenize(text):
    """逐字符扫描，生成 Token 列表。遇到不识别的字符则返回 None。"""
    tokens = []
    for i, ch in enumerate(text):
        entry = _CHAR_TOKEN_MAP.get(ch)
        if entry is None:
            return None
        token_type, token_value = entry
        tokens.append(Token(type=token_type, value=token_value, char=ch, pos=i))
    return tokens


# ============================================================
# 语法分析器
# ============================================================

def _parse_atomic(tokens, i):
    """从位置 i 解析一个原子数值，返回 (值, 消耗_token数) 或 None"""
    n = len(tokens)
    if i >= n:
        return None

    t = tokens[i]

    # === DIGIT 开头 ===
    if t.type == 'DIGIT':
        d = t.value

        # DIGIT + 亿 → d * 10^8
        if i + 1 < n and tokens[i+1].type == 'HUNDRED_MILLION':
            return (d * 100000000, 2)

        # DIGIT + 万 → d * 10000
        if i + 1 < n and tokens[i+1].type == 'TEN_THOUSAND':
            return (d * 10000, 2)

        # DIGIT + 千
        if i + 1 < n and tokens[i+1].type == 'THOUSAND':
            return (d * 1000, 2)

        # DIGIT + 百
        if i + 1 < n and tokens[i+1].type == 'HUNDRED':
            base = d * 100
            consumed = 2
            j = i + 2
            if j < n and tokens[j].type == 'ZERO':
                if j + 1 < n and tokens[j+1].type == 'DIGIT':
                    base += tokens[j+1].value
                    consumed += 2
            elif j < n and tokens[j].type == 'DIGIT':
                tens_d = tokens[j].value
                if j + 1 < n and tokens[j+1].type == 'TEN':
                    base += tens_d * 10
                    consumed += 2
                    j += 2
                    if j < n and tokens[j].type == 'DIGIT':
                        base += tokens[j].value
                        consumed += 1
                else:
                    base += tens_d * 10
                    consumed += 1
            return (base, consumed)

        # DIGIT + TEN + DIGIT → d*10 + d2
        if (i + 2 < n
            and tokens[i+1].type == 'TEN'
            and tokens[i+2].type == 'DIGIT'):
            if i + 3 < n and tokens[i+3].type == 'TEN':
                pass  # 后跟 TEN → 倾向拆开
            else:
                return (10 * d + tokens[i+2].value, 3)

        # DIGIT + TEN → d*10（前方是 DIGIT run 时不组合）
        if i + 1 < n and tokens[i+1].type == 'TEN':
            if i > 0 and tokens[i-1].type == 'DIGIT':
                pass
            else:
                return (10 * d, 2)

        return (d, 1)

    # === TEN 开头 ===
    if t.type == 'TEN':
        if (i + 2 < n
            and tokens[i+1].type == 'DIGIT'
            and tokens[i+2].type == 'HUNDRED_MILLION'):
            return ((10 + tokens[i+1].value) * 100000000, 3)
        if i + 1 < n and tokens[i+1].type == 'HUNDRED_MILLION':
            return (10 * 100000000, 2)
        if i + 1 < n and tokens[i+1].type == 'DIGIT':
            return (10 + tokens[i+1].value, 2)
        return (10, 1)

    # === ZERO ===
    if t.type == 'ZERO':
        return (0, 1)

    # 百千万亿 单独
    if t.type in ('HUNDRED', 'THOUSAND', 'TEN_THOUSAND', 'HUNDRED_MILLION'):
        return (t.value, 1)

    return None


def _build_number(tokens, i):
    """
    从位置 i 尝试解析一个完整数值（含累加+倍增），返回 (值, 消耗_token数) 或 None。

    流程：
      1. _parse_atomic 解析原子值
      2. 值表达式后跟 万/亿 → 倍增
      3. 倍增后累加低位（千/百/十/个）
      4. 千后累加百/十/个
    """
    result = _parse_atomic(tokens, i)
    if result is None:
        return None
    value, consumed = result
    n = len(tokens)
    j = i + consumed

    # 值表达式后跟 万/亿 → 倍增（必须在累加之前）
    if j < n:
        nxt = tokens[j]
        if nxt.type == 'TEN_THOUSAND' and isinstance(value, int) and 0 < value < 10000:
            value *= 10000
            consumed += 1
            j += 1
        elif nxt.type == 'HUNDRED_MILLION' and isinstance(value, int) and 0 < value < 100000000:
            value *= 100000000
            consumed += 1
            j += 1

    # 万/亿/千 后累加低位
    if value >= 10000:
        limit = 10000
    elif value >= 1000:
        limit = 1000
    else:
        limit = None

    if limit:
        while j < n:
            if tokens[j].type == 'ZERO':
                consumed += 1
                j += 1
                continue
            chunk = _parse_atomic(tokens, j)
            if chunk is None:
                break
            chunk_val, chunk_con = chunk
            if chunk_val >= limit:
                break
            value += chunk_val
            consumed += chunk_con
            j += chunk_con

    # 累加后再检查万/亿（七千九百零三亿 = 7903 * 10^8）
    if j < n:
        nxt = tokens[j]
        if nxt.type == 'TEN_THOUSAND' and isinstance(value, int) and 0 < value < 10000:
            value *= 10000
            consumed += 1
        elif nxt.type == 'HUNDRED_MILLION' and isinstance(value, int) and 0 < value < 100000000:
            value *= 100000000
            consumed += 1

    return (value, consumed)


def parse_tokens(tokens):
    """消耗 Token 流，解析为数字列表。"""
    numbers = []
    i = 0
    n = len(tokens)

    while i < n:
        # 先尝试建数（含累加）
        result = _build_number(tokens, i)
        if result is None:
            return None
        value, consumed = result

        # 小数点处理
        if i + consumed < n and tokens[i + consumed].type == 'DOT':
            dot_idx = i + consumed
            # 解析小数部分：DOT 后的连续 DIGIT / ZERO
            k = dot_idx + 1
            decimal_digits = []
            while k < n and tokens[k].type in ('DIGIT', 'ZERO'):
                decimal_digits.append(str(tokens[k].value))
                k += 1
            if decimal_digits:
                value = float(f"{value}.{''.join(decimal_digits)}")
                consumed = k - i
            else:
                value = float(f"{value}.")
                consumed += 1

        numbers.append(value)
        i += consumed

    return numbers


# ============================================================
# 对外接口
# ============================================================

_UNIT_PATTERN = re.compile(rf'({common_units})$')


def strip_trailing_chars(text):
    """去除末尾的已知单位。使用 common_units 做后缀匹配，最长优先。"""
    m = _UNIT_PATTERN.search(text)
    if m:
        return text[:m.start()]
    return text


def parse_sequence(text):
    """
    尝试用 parser 解析文本，成功返回 ' ' 分隔的数字串，失败返回 None。
    自动剥离末尾单位字符（含映射），解析后还原。
    注意：不剥离 万/亿（它们是数值乘数，不是物理单位）。
    """
    from .converters import strip_unit
    stripped, unit = strip_unit(text)

    # 如果剥离的是 万/亿，不要剥离（它们是数值乘数）
    if unit in ('万', '亿'):
        stripped = text
        unit = ''

    if not stripped:
        return None

    tokens = tokenize(stripped)
    if tokens is None:
        # tokenize 不识别的字符 → 尝试逐字符从尾部去掉非数字字符
        end = len(text)
        while end > 0:
            tokens = tokenize(text[:end])
            if tokens is not None:
                break
            end -= 1
        if tokens is None:
            return None
        stripped = text[:end]
        unit = text[end:]

    # 显示模式：token 流末尾是 万/亿/万亿 → 作单位处理而非数学乘
    if tokens and tokens[-1].type in ('TEN_THOUSAND', 'HUNDRED_MILLION'):
        display_unit = tokens[-1].char
        numbers = parse_tokens(tokens[:-1])
        if numbers is not None:
            result = ' '.join(str(n) for n in numbers) + display_unit
            if unit:
                result += unit
            return result

    numbers = parse_tokens(tokens)
    if numbers is None:
        return None

    result = ' '.join(str(n) for n in numbers)
    if unit:
        result += unit
    return result
