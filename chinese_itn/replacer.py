"""
主替换逻辑和入口函数
"""

from .mappings import idioms, fuzzy_regex
from .patterns import (
    pattern, pure_num, value_num,
    percent_permille_value, fraction_value, ratio_value, time_value, data_value,
)
from .converters import (
    strip_trailing_unit, is_consecutive_value,
    convert_pure_num, convert_fraction_value,
    convert_percent_permille_value, convert_ratio_value,
    convert_time_value, convert_date_value,
)
from .sequence_parser import parse_sequence, tokenize
from .ranges import is_range_expression, convert_range_expression


def replace(original):
    """主替换函数"""
    string = original.string
    l_pos, r_pos = original.regs[2]
    l_pos = max(l_pos - 2, 0)
    head = original.group(1)
    original_text = original.group(2)
    original = original_text

    DEBUG = False

    try:
        # 成语/习语检测
        if idioms and any(
            (string.find(idiom) in range(l_pos, r_pos) and not (len(original) > len(idiom) and idiom in original))
            for idiom in idioms
        ):
            num_type = '成语/习语'
            final = original

        # 模糊表达检测
        elif fuzzy_regex.search(original):
            num_type = '模糊表达'
            final = original

        # 范围表达式
        elif is_range_expression(original):
            num_type = '范围表达式'
            final = convert_range_expression(original)

        # 时间
        elif time_value.fullmatch(original):
            num_type = '时间'
            final = convert_time_value(original)

        # 纯数字
        elif pure_num.fullmatch(strip_trailing_unit(original)):
            num_type = '纯数字'
            final = convert_pure_num(original)

        # 数值解析（Parser，value_num / 连续数值 / 序列解析 守卫）
        elif (value_num.fullmatch(strip_trailing_unit(original)) 
              or is_consecutive_value(original)
              or (tokenize(strip_trailing_unit(original)) is not None 
                  and not original.endswith('点') 
                  and parse_sequence(original) is not None)):
            num_type = '数值解析'
            final = parse_sequence(original)

        # 百分数 / 千分比
        elif percent_permille_value.fullmatch(original):
            num_type = '百分比数值'
            final = convert_percent_permille_value(original)

        # 分数
        elif fraction_value.fullmatch(original):
            num_type = '分数'
            final = convert_fraction_value(original)

        # 比值
        elif ratio_value.fullmatch(original):
            num_type = '比值'
            final = convert_ratio_value(original)

        # 日期
        elif data_value.fullmatch(original):
            num_type = '日期'
            final = convert_date_value(original)

        else:
            num_type = '未匹配'
            final = original

        if head:
            final = head + final

        if DEBUG and original_text != final:
            print(f"[{num_type}] {original_text} → {final}")

    except Exception as e:
        num_type = '错误'
        final = original
        if DEBUG:
            print(f"[错误] {original_text}: {e}")

    return final


def chinese_to_num(original):
    """主函数：将中文数字转换为阿拉伯数字"""
    result = pattern.sub(replace, original)
    return result
