import json, sys
sys.stdout.reconfigure(encoding='utf-8')
cases = json.load(open(r'D:\Chinese-ITN\docs\superpowers\specs\retest_cases.json', encoding='utf-8'))
from wetext import Normalizer
n = Normalizer(lang="zh", operator="tn")
out = []
for cat, inp, exp in cases:
    try:
        wt = n.normalize(inp)
    except Exception as e:
        wt = f'<EXC {e}>'
    out.append({'cat': cat, 'in': inp, 'wetext': wt, 'exp': exp})
json.dump(out, open(r'D:\Chinese-ITN\docs\superpowers\specs\retest_out_wetext.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in out:
    print(f"[{r['cat']}] {r['in']}\n  wetext: {r['wetext']}\n  exp:    {r['exp']}")
