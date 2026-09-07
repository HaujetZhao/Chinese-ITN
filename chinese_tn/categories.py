# coding: utf-8
"""类别表：24 个 (名称, 局部正则, 处理函数) 三元组，自包含。

引擎把本表自动合成一条命名组交替正则，单趟扫描后按类别组分发。
优先级 = 表中顺序 = 正则交替顺序（同一位置按交替顺序取首个匹配）。
注意：类别内部子组不命名（不参与引擎分发），需要取子串的 handler
用各自的局部正则 fullmatch 重新解析 m.group()。

歧义符号裁决表（高 → 低）：
| 符号 | 裁决顺序 |
| --- | --- |
| `-` | ISO日期 YYYY-M-D → 电话分段 → 字母/汉字-型号 A-320 歼-20 → 数字分段(≥3段)逐位 → 范围 n[-~～]n → 负号（仅当前一字符非数字/字母时） |
| `/` | 斜杠日期 YYYY/M/D → 分数 |
| `:` | 时间 HH:MM[:SS] → 多段比值 |
"""

import re

from .numbers import int_to_chinese, decimal_to_chinese, digitwise
from .tables import CURRENCY_SYMBOLS, METRIC_UNITS, NUMBER_CONTEXT_WORDS, PLATE_PROVINCES

_NUM = r'-?\d+(?:\.\d+)?'
# 多字母单位大小写不敏感（最长优先）；单字母仅小写（L 除外），避免 5G/3M 代号误判单位
_MULTI_UNITS = sorted((u for u in METRIC_UNITS if len(u) > 1), key=len, reverse=True)
_UNIT_FACTOR = {'万': 10**4, '亿': 10**8, '万亿': 10**12}

# 局部正则既写进类别表，也供 handler 解析子串复用
_YMD = r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
_DATE = r'\d{2,4}年(?:\d{1,2}月)?(?:\d{1,2}[日号])?|\d{1,2}月(?:\d{1,2}[日号])?|\d{1,2}[日号]'
_TIME = r'(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?'
_PERCENT = rf'{_NUM}[‰%]'
_FRACTION = r'\d{1,2}/\d{1,2}'
_RATIO = r'\d+(?::\d+)+'
_TEMP = rf'({_NUM})(℃|°C|°F|℉)'
_BAREDEG = rf'({_NUM})°'
_CURRENCY = r'([$￥€£])(\d+(?:\.\d+)?)'
_PHONE = r'\d{3,4}-\d{7,8}|\d{3}-\d{3,4}-\d{4}'
_PLATE = rf'([{PLATE_PROVINCES}])([A-Z])·?(\d{{5}})'
_MODEL = r'([一-鿿A-Za-z])-(\d{1,6})'
_NUMCTX = rf'({"|".join(sorted(NUMBER_CONTEXT_WORDS, key=len, reverse=True))})((?:\d+(?:-\d+)*))'
_THOUSANDS = r'\d{1,3}(?:,\d{3})+'
_SCI = r'\d+(?:\.\d+)?[eE]\d+'
_MEASURE = rf'(\d+(?:\.\d+)?)((?i:{"|".join(_MULTI_UNITS)})|[mgh]|[lL])'
_LETTERCODE = r'(航班)?([A-Za-z]{1,6})(\d{1,6})'
_DIGITCODE = r'(?<![A-Za-z0-9.])(\d+)(?=[A-Za-z])'
_HYPHENSEQ = r'\d+(?:-\d+){2,}'
_PLUSMINUS = rf'±({_NUM})'
_MATH = r'\d+(?:\.\d+)?(?:\s*[+=]\s*\d+(?:\.\d+)?)+'
_RANGE = r'(\d{1,4})[-~～](\d{1,4})(年?)'
_NUMBER = rf'(?<![A-Za-z0-9])({_NUM})(万亿|万|亿)?'

_DATE_PARTS = re.compile(r'(?:(\d{2,4})年)?(?:(\d{1,2})月)?(?:(\d{1,2})([日号]))?')
_TIME_PARTS = re.compile(r'(\d{1,2}):(\d{2})(?::(\d{2}))?')


def _read_value(body):
    """数值读：整数或小数字符串（可带负号）"""
    if '.' in body:
        return decimal_to_chinese(body)
    return int_to_chinese(int(body))


# ---------- 日期类 ----------

def _convert_ymd(m):
    """斜杠/ISO 日期：年份逐位读，月日数值读（2026/09/07 -> 二零二六年九月七日）"""
    y, mo, d = re.fullmatch(_YMD, m.group()).groups()
    return digitwise(y) + '年' + int_to_chinese(int(mo)) + '月' + int_to_chinese(int(d)) + '日'


def _convert_date(m):
    year, month, day, day_suffix = _DATE_PARTS.fullmatch(m.group()).groups()
    out = ''
    if year:
        out += digitwise(year) + '年'
    if month:
        out += int_to_chinese(int(month)) + '月'
    if day:
        out += int_to_chinese(int(day)) + day_suffix
    return out


# ---------- 时间 / 比值 ----------

def _small_unit(n, unit):
    """分/秒读法：不足 10 补「零」（08:05 -> 八点零五分）"""
    return ('零' + int_to_chinese(n) if n < 10 else int_to_chinese(n)) + unit


def _convert_time(m):
    hour, minute, second = _TIME_PARTS.fullmatch(m.group()).groups()
    if int(minute) == 0 and second is None:
        # 整点：9:00 -> 九点整、00:00 -> 零点整
        return int_to_chinese(int(hour)) + '点整'
    out = int_to_chinese(int(hour)) + '点' + _small_unit(int(minute), '分')
    if second:
        out += _small_unit(int(second), '秒')
    return out


def _convert_ratio(m):
    return '比'.join(int_to_chinese(int(seg)) for seg in m.group().split(':'))


# ---------- 百分 / 分数 ----------

def _convert_percent(m):
    text = m.group()
    body, suffix = text[:-1], text[-1]
    prefix = '千分之' if suffix == '‰' else '百分之'
    if body.startswith('-'):
        return '负' + prefix + _read_value(body[1:])
    return prefix + _read_value(body)


def _convert_fraction(m):
    a, b = m.group().split('/')
    return int_to_chinese(int(b)) + '分之' + int_to_chinese(int(a))


# ---------- 温度 / 角度 / 货币 ----------

def _convert_temp(m):
    value, sym = re.fullmatch(_TEMP, m.group()).groups()
    prefix = '零下' if value.startswith('-') else ''
    unit = '华氏度' if sym in ('°F', '℉') else '度'
    return prefix + _read_value(value.lstrip('-')) + unit


def _convert_baredeg(m):
    """裸角度号：30° -> 三十度（°C/°F 已被 temp 类别吃掉）"""
    return _read_value(re.fullmatch(_BAREDEG, m.group()).group(1)) + '度'


def _convert_currency(m):
    sym, value = re.fullmatch(_CURRENCY, m.group()).groups()
    return _read_value(value) + CURRENCY_SYMBOLS[sym]


# ---------- 号码语境 / 字母数字代号（逐位） ----------

def _convert_phone(m):
    # 分段间用空格停顿（不引入原文没有的标点，TTS 逗号会带句内韵律）
    return ' '.join(digitwise(seg, one='幺') for seg in m.group().split('-'))


def _convert_plate(m):
    province, letter, digits = re.fullmatch(_PLATE, m.group()).groups()
    return province + letter + digitwise(digits, one='幺')


def _convert_numctx(m):
    # 数字部分允许电话分段形态（热线400-800-1234）；「幺」语境换 1 的读法，「零」语境用默认逐位
    word, digits = re.fullmatch(_NUMCTX, m.group()).groups()
    one = NUMBER_CONTEXT_WORDS[word]
    return word + ' '.join(digitwise(seg, one=one) if one == '幺' else digitwise(seg)
                           for seg in digits.split('-'))


def _convert_lettercode(m):
    """字母+数字紧贴代号：C919 -> C九一九；航班语境逐位读「幺」（航班CA1856 -> 航班CA幺八五六）"""
    flight, letters, digits = re.fullmatch(_LETTERCODE, m.group()).groups()
    return (flight or '') + letters + (digitwise(digits, one='幺') if flight else digitwise(digits))


def _convert_digitcode(m):
    """数字+字母紧贴代号：1080P -> 一零八零、5G -> 五G（单位已被 measure 类别吃掉）"""
    return digitwise(m.group())


def _convert_hyphenseq(m):
    """≥3 段连字符数字（ISBN 978-7-111-11111-3）：逐位读，段间空格停顿"""
    return ' '.join(digitwise(seg) for seg in m.group().split('-'))


# ---------- 数值形态 ----------

_MATH_OPS = {'+': '加', '=': '等于'}


def _convert_plusminus(m):
    return '正负' + _read_value(re.fullmatch(_PLUSMINUS, m.group()).group(1))


def _convert_math(m):
    """加减等号算式：1+1=2 -> 一加一等于二（纯 `-` 链走 range 类别）"""
    parts = re.split(r'([+=])', m.group())
    return ''.join(_MATH_OPS[p] if i % 2 else _read_value(p.strip()) for i, p in enumerate(parts))


def _convert_model(m):
    letter, digits = re.fullmatch(_MODEL, m.group()).groups()
    return letter + digitwise(digits)


def _convert_thousands(m):
    return int_to_chinese(int(m.group().replace(',', '')))


def _convert_sci(m):
    v = float(m.group())
    if v.is_integer():
        return int_to_chinese(int(v))
    return decimal_to_chinese(format(v, 'f'))


def _convert_measure(m):
    value, unit = re.fullmatch(_MEASURE, m.group()).groups()
    return _read_value(value) + METRIC_UNITS[unit.lower()]


def _convert_range(m):
    a, b, year = re.fullmatch(_RANGE, m.group()).groups()
    if len(a) == 4 and len(b) == 4:
        # 两侧均为 4 位按年份逐位读，吞掉尾「年」（2000-2010年 -> 二零零零年到二零一零年）
        return digitwise(a) + '年到' + digitwise(b) + '年'
    return int_to_chinese(int(a)) + '到' + int_to_chinese(int(b)) + year


def _convert_number(m):
    body, unit = re.fullmatch(_NUMBER, m.group()).groups()
    if '.' in body:
        # 带小数时不折算单位：20.1万 -> 二十点一万
        return decimal_to_chinese(body) + (unit or '')
    if unit:
        return int_to_chinese(int(body) * _UNIT_FACTOR[unit])
    digits = body.lstrip('-')
    # 前导零、14 位以上长串、11 位手机号（1 开头）逐位读；其余数值读
    if digits.startswith('0') or len(digits) >= 14 or (len(digits) == 11 and digits.startswith('1')):
        return ('负' if body.startswith('-') else '') + digitwise(digits)
    return int_to_chinese(int(body))


# 类别优先级表（高 → 低）
CATEGORIES = [
    ('slashdate', _YMD.replace('[/-]', '/'), _convert_ymd),
    ('isodate', _YMD.replace('[/-]', '-'), _convert_ymd),
    ('date', _DATE, _convert_date),
    ('time', _TIME, _convert_time),
    ('percent', _PERCENT, _convert_percent),
    ('fraction', _FRACTION, _convert_fraction),
    ('ratio', _RATIO, _convert_ratio),
    ('temp', _TEMP, _convert_temp),
    ('baredeg', _BAREDEG, _convert_baredeg),
    ('currency', _CURRENCY, _convert_currency),
    ('phone', _PHONE, _convert_phone),
    ('plate', _PLATE, _convert_plate),
    ('model', _MODEL, _convert_model),
    ('numctx', _NUMCTX, _convert_numctx),
    ('thousands', _THOUSANDS, _convert_thousands),
    ('sci', _SCI, _convert_sci),
    ('measure', _MEASURE, _convert_measure),
    ('lettercode', _LETTERCODE, _convert_lettercode),
    ('digitcode', _DIGITCODE, _convert_digitcode),
    ('hyphenseq', _HYPHENSEQ, _convert_hyphenseq),
    ('plusminus', _PLUSMINUS, _convert_plusminus),
    ('math', _MATH, _convert_math),
    ('range', _RANGE, _convert_range),
    ('number', _NUMBER, _convert_number),
]

# 已知局限（记录不修）：
# - 四段时间 `12:30:45:60` 尾段漏转（ratio 只吃掉前三段，末段 `:60` 残留）
# - 裸短号如 `110`、`12306` 无上下文词时按数值读（996工作制 同理，无本地信号）
# - 减号链（5-3=2）不做算式读法，`-` 交给范围/分段裁决；±N% 只转 ±N，% 残留
