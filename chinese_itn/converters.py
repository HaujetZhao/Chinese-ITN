"""
转换函数和辅助函数
"""

import re
from .mappings import unit_mapping, common_units, num_mapper, value_mapper
from .patterns import consecutive_tens, consecutive_hundreds


# 用于去除末尾单位的正则
_unit_suffix_pattern = re.compile(rf'({common_units}|[a-zA-Z]+)$')


def strip_trailing_unit(text):
    """用正则去除末尾的单位"""
    match = _unit_suffix_pattern.search(text)
    if match:
        return text[:match.start()]
    return text


def is_consecutive_value(text):
    """检测是否是连续数值结构"""
    return consecutive_tens.match(text) or consecutive_hundreds.match(text)


def split_consecutive_value(text):
    """分割连续数值为空格分隔的阿拉伯数字"""
    unit = ''
    for c in common_units:
        if text.endswith(c):
            unit = c
            text = text[:-1]
            break

    if consecutive_tens.match(text + unit):
        parts = re.findall(r'十[一二三四五六七八九]', text)
        nums = [convert_value_num(p) for p in parts]
        return ' '.join(nums) + unit

    if consecutive_hundreds.match(text + unit):
        parts = re.findall(r'[一二三四五六七八九]百零?[一二三四五六七八九]', text)
        nums = [convert_value_num(p) for p in parts]
        return ' '.join(nums) + unit



def strip_unit(original):
    """把数字后面跟着的单位剥离开，并应用单位映射"""
    unit_pattern = re.compile(rf'({common_units})$')
    match = unit_pattern.search(original)

    if match:
        unit_cn = match.group(1)
        stripped = original[:match.start()]
        mapped_unit = unit_mapping.get(unit_cn)
        unit = mapped_unit if mapped_unit is not None else unit_cn
    else:
        stripped = original
        unit = ''

    if not unit and stripped:
        letter_match = re.search(r'[a-zA-Z]+$', stripped)
        if letter_match:
            unit = letter_match.group()
            stripped = stripped[:letter_match.start()]

    return stripped.strip(), unit


def convert_pure_num(original, strict=False):
    """把中文数字转为对应的阿拉伯数字"""
    stripped, unit = strip_unit(original)
    if stripped in ['一'] and not strict:
        return original
    converted = [num_mapper[c] for c in stripped]
    return ''.join(converted) + unit


def convert_value_num(original):
    """把中文数值转为阿拉伯数字"""
    stripped, unit = strip_unit(original)
    if '点' not in stripped:
        stripped += '点'
    int_part, decimal_part = stripped.split("点")
    if not int_part:
        return original

    value, temp, base = 0, 0, 1
    for c in int_part:
        if c == '十':
            temp = 10 if temp == 0 else value_mapper[c] * temp
            base = 1
        elif c == '零':
            base = 1
        elif c in '一二两三四五六七八九':
            temp += value_mapper[c]
        elif c in '万':
            value += temp
            value *= value_mapper[c]
            base = value_mapper[c] // 10
            temp = 0
        elif c in '百千':
            value += temp * value_mapper[c]
            base = value_mapper[c] // 10
            temp = 0
    value += temp * base
    final = str(value)

    decimal_str = convert_pure_num(decimal_part, strict=True)
    if decimal_str:
        final += '.' + decimal_str
    final += unit

    return final


def convert_fraction_value(original):
    """转换分数"""
    denominator, numerator = original.split('分之')
    return convert_value_num(numerator) + '/' + convert_value_num(denominator)


def convert_percent_permille_value(original):
    """转换百分数/千分比"""
    suffix = '%' if original[0] == '百' else '‰'
    return convert_value_num(original[3:]) + suffix


def convert_ratio_value(original):
    """转换比值"""
    num1, num2 = original.split("比")
    return convert_value_num(num1) + ':' + convert_value_num(num2)


def convert_time_value(original):
    """转换时间"""
    res = [x for x in re.split('[点分秒]', original) if x]
    final = ''
    hour = convert_value_num(res[0])
    final += hour.zfill(2)
    minute = convert_value_num(res[1])
    final += ':' + minute.zfill(2)
    if len(res) > 2:
        second = convert_value_num(res[2])
        final += ':' + second.zfill(2)
    if len(res) > 3:
        final += '.' + convert_pure_num(res[3])
    return final


def convert_date_value(original):
    """转换日期"""
    final = ''
    if '年' in original:
        year, original = original.split('年')
        final += convert_pure_num(year) + '年'
    if '月' in original:
        month, original = original.split('月')
        final += convert_value_num(month) + '月'
    if '日' in original:
        day, original = original.split('日')
        final += convert_value_num(day) + '日'
    elif '号' in original:
        day, original = original.split('号')
        final += convert_value_num(day) + '号'
    return final
