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


def digitwise(digits, one='一'):
    """纯数字串逐位转中文：'0421' -> 零四二一；号码语境 1 读「幺」"""
    return ''.join(one if c == '1' else _DIGITS[int(c)] for c in digits)
