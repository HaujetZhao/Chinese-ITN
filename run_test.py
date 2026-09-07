# coding: utf-8
"""
简单的测试脚本：基于 test_cases.txt 测试 chinese_itn，基于 test_cases_tn.txt 测试 chinese_tn
"""

from pathlib import Path

from chinese_itn import chinese_to_num
from chinese_tn import num_to_chinese


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
    print()
    run_suite(
        "chinese_tn 测试", num_to_chinese,
        'test_cases_tn.txt', 'test_cases_tn_correct.txt', 'test_cases_tn_wrong.txt',
    )
