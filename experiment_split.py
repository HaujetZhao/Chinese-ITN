"""
实验：测试主库 sequence_parser 的边界案例

从主库导入 try_parse，用外部案例文件驱动测试。
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from chinese_itn.sequence_parser import parse_sequence


def load_test_cases(path='test_cases_experiment.txt'):
    """从 txt 文件读取测试用例。支持 | 分隔多个可接受结果。"""
    cases = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ' -> ' not in line:
                continue
            parts = line.split(' -> ', 1)
            text = parts[0].strip()
            expected_raw = parts[1].strip()
            expected_list = [e.strip() for e in expected_raw.split('|')]
            cases.append((text, expected_list))
    return cases


def run_tests(cases):
    print("=" * 60)
    print("sequence_parser 测试")
    print(f"（导入自 chinese_itn.sequence_parser.try_parse）")
    print("=" * 60)

    passed = 0
    failed = 0

    for text, expected_list in cases:
        result = parse_sequence(text)
        expected_str = ' | '.join(expected_list)
        if result in expected_list:
            passed += 1
            status = '✓'
        else:
            failed += 1
            status = '✗'
        print(f"  {status} {text!r:30s} → {str(result)!r:25s} (期望: {expected_str})")

    print(f"\n通过: {passed}, 失败: {failed}, 共: {len(cases)}")

    if failed > 0:
        print(f"\n失败的详情:")
        for text, expected_list in cases:
            result = parse_sequence(text)
            if result not in expected_list:
                print(f"\n  tokenize 或 parse 失败")


if __name__ == '__main__':
    cases = load_test_cases()
    run_tests(cases)
