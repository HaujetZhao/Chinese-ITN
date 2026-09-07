# coding: utf-8
"""薄引擎：合成类别表为单条正则，单趟扫描分发，入口 num_to_chinese()"""

import re

from .categories import CATEGORIES

# 表序即优先级：同一位置按交替顺序取首个匹配
pattern = re.compile('|'.join(f'(?P<{name}>{rx})' for name, rx, _ in CATEGORIES))
_HANDLERS = {name: fn for name, _, fn in CATEGORIES}


def _replace(m):
    return _HANDLERS[m.lastgroup](m)


def num_to_chinese(text):
    """主函数：将文本中的阿拉伯数字转换为中文读法"""
    return pattern.sub(_replace, text)
