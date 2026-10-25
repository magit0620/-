"""完成版の受注の現状 .docx から data.json（次回の比較元）を取り出す。
使い方: python3 extract.py 受注の現状_YYYYMMDD.docx data.json"""
import sys, json, docx
from docx.oxml.ns import qn

FLAG = {'C6EFCE': '完工', 'CCFFCC': '完工', 'FFEB9C': '受注', 'D9D9D9': '失注', 'BDD7EE': '新規'}
KEYS = ['所在', '名前', '担当', '工事内容', '金額', '変更']

def cell_info(c):
    runs = list(c._tc.iter(qn('w:r')))
    red = any(r.find('.//' + qn('w:color')) is not None and r.find('.//' + qn('w:color')).get(qn('w:val')) not in ('000000', 'auto') for r in runs)
    strike = any(r.find('.//' + qn('w:strike')) is not None and r.find('.//' + qn('w:strike')).get(qn('w:val'), 'true') not in ('0', 'false') for r in runs)
    return c.text.replace('\n', '／'), red, strike

d = docx.Document(sys.argv[1])
body = d.element.body
out, cur = {'sections': [], 'notes': []}, None
from docx.text.paragraph import Paragraph
from docx.table import Table
for el in body:
    if el.tag == qn('w:p'):
        t = Paragraph(el, d).text.strip()
        if t.startswith('【'):
            cur = {'title': t, 'rows': []}; out['sections'].append(cur)
        elif t.startswith('・'):
            out['notes'].append(t[1:])
        elif t.startswith('受注の現状') and not out.get('date'):
            out['date'] = t
    elif el.tag == qn('w:tbl') and cur is not None:
        for row in Table(el, d).rows[1:]:
            shd = row.cells[1]._tc.find('.//' + qn('w:shd'))
            fill = shd.get(qn('w:fill')) if shd is not None else None
            rec, red_keys, strike = {}, [], False
            for k, c in zip(KEYS, row.cells):
                txt, red, st = cell_info(c); rec[k] = txt
                if red: red_keys.append(k)
                strike = strike or st
            if not ''.join(rec.values()).strip(): continue
            rec['色'] = FLAG.get(fill, '')
            rec['赤字'] = red_keys
            if strike: rec['取消線'] = True
            cur['rows'].append(rec)
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
