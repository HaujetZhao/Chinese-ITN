import csv
import chinese_itn
import colorama; colorama.init()
from colorama import Fore

file_path = 'sample-set.csv'

# 打开 csv 文件，使用 UTF-BOM 格式，便于 Excel 识别
with open(file_path, 'r', encoding='utf-8-sig') as f:
    test_set = list(csv.DictReader(f, delimiter=','))

# 依次进行 ITN
for index in range(len(test_set)):
    test_set[index]['result'] = chinese_itn.chinese_to_num(test_set[index]['original']) 

# 输出结果
for sample in test_set:
    original = sample['original']
    expect = sample['expect']
    result = sample['result']
    if expect == result:
        print('\n' + Fore.GREEN + f'原始：{original}\n期待：{expect}\n结果：{result}' + Fore.RESET)
    else:
        print('\n' + Fore.RED + f'原始：{original}\n期待：{expect}\n结果：{result}' + Fore.RESET)

# 写回结果
with open(file_path, 'w', encoding='utf-8-sig') as f:
    fieldnames = ['original', 'expect', 'result']
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
    writer.writeheader()
    writer.writerows(test_set)