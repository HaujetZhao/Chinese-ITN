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
    to_chinese = decimal_to_chinese if '.' in body else lambda s: int_to_chinese(int(s))
    if body.startswith('-'):
        return '负' + prefix + to_chinese(body[1:])
    return prefix + to_chinese(body)


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
    # 前导零或长串（电话/证件号类）逐位读；9 位以内按数值读
    if digits.startswith('0') or len(digits) >= 11:
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
