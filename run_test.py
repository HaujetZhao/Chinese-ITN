# coding: utf-8
"""
简单的测试脚本：基于 test_cases.txt 测试 chinese_itn.py
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from chinese_itn import chinese_to_num

def run_test():
    """运行测试"""
    print("=" * 60)
    print("chinese_itn 测试")
    print("=" * 60)
    
    # 读取测试用例
    test_cases = []
    with open('test_cases.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ' -> ' not in line:
                continue
            parts = line.split(' -> ')
            if len(parts) == 2:
                test_cases.append((parts[0].strip(), parts[1].strip()))
    
    print(f"共 {len(test_cases)} 个测试用例\n")
    
    correct = []
    wrong = []
    
    for input_text, expected in test_cases:
        result = chinese_to_num(input_text)
        if result == expected:
            correct.append((input_text, expected))
        else:
            wrong.append((input_text, expected, result))
    
    # 统计
    print(f"✓ 正确: {len(correct)} ({len(correct)/len(test_cases)*100:.1f}%)")
    print(f"✗ 错误: {len(wrong)} ({len(wrong)/len(test_cases)*100:.1f}%)")
    
    # 显示错误案例
    if wrong:
        print(f"\n错误案例:")
        for i, (input_text, expected, result) in enumerate(wrong[:20]):
            print(f"  {i+1}. {input_text}")
            print(f"     期望: {expected}")
            print(f"     实际: {result}")
        if len(wrong) > 20:
            print(f"  ... 还有 {len(wrong) - 20} 个")
    
    # 保存到文件
    with open('test_cases_correct.txt', 'w', encoding='utf-8') as f:
        f.write("# 测试通过的用例\n# 格式: 输入 -> 期望输出\n\n")
        for input_text, expected in correct:
            f.write(f"{input_text} -> {expected}\n")
    
    with open('test_cases_wrong.txt', 'w', encoding='utf-8') as f:
        f.write("# 测试未通过的用例\n# 格式: 输入 -> 期望输出 (当前: 实际输出)\n\n")
        for input_text, expected, result in wrong:
            f.write(f"{input_text} -> {expected} (当前: {result})\n")
    
    print(f"\n结果已保存到 test_cases_correct.txt 和 test_cases_wrong.txt")
    print("=" * 60)
    
    return len(correct), len(wrong)


if __name__ == "__main__":
    run_test()
