import json, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:\repos-tts\supertonic-mini')
cases = json.load(open(r'D:\Chinese-ITN\docs\superpowers\specs\retest_cases.json', encoding='utf-8'))
from chinese_tn import num_to_chinese
from misaki.zh_normalization.text_normalization import TextNormalizer
tn = TextNormalizer()
out = []
for cat, inp, exp in cases:
    try:
        ctn = num_to_chinese(inp)
    except Exception as e:
        ctn = f'<EXC {e}>'
    try:
        mk = tn.normalize_sentence(inp)
    except Exception as e:
        mk = f'<EXC {e}>'
    out.append({'cat': cat, 'in': inp, 'ctn': ctn, 'misaki': mk, 'exp': exp})
json.dump(out, open(r'D:\Chinese-ITN\docs\superpowers\specs\retest_out_ctn_misaki.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in out:
    print(f"[{r['cat']}] {r['in']}\n  ctn:    {r['ctn']}\n  misaki: {r['misaki']}\n  exp:    {r['exp']}")
