"""Table 6 of the working paper (tab:c4compact) is a subset of the package's per-opportunity table
(tab:c4opp): the single offer and the n = 2 rows, without the Surplus column. Usage:
python3 table6.py <wp.tex> <pkg_dir> <out.csv>"""
import csv, re, sys, importlib.util
import os; here = os.path.dirname(os.path.abspath(sys.argv[0]))
spec = importlib.util.spec_from_file_location('rc', here + '/reconcile.py'); rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
wp = open(sys.argv[1], encoding='utf-8').read(); pkg = open(sys.argv[2] + '/c4_tables_main.tex', encoding='utf-8').read()
def cells(block):
    out = []
    for r in rc.body(block).split('\\\\'):
        r = rc.norm(r)
        parts = [p.strip() for p in r.split('&')]
        if len(parts) > 3: out.append(parts)
    return out
w = cells(rc.table_block(wp, 'tab:c4compact')); p = cells(rc.table_block(pkg, 'tab:c4opp'))
pk = {}
for r in p:
    proc = r[2].replace(' ', '')
    key = (r[0], r[1], 'Singleoffer' if proc.startswith('Single') else proc.replace(',n=2', '') if proc.endswith('n=2') else None)
    if key[2]: pk[key] = [r[3], r[4], r[5], r[7], r[8], r[9]]
diffs = []; n = 0
for r in w:
    key = (r[0], r[1], r[2].replace(' ', ''))
    vals = r[3:9]; ref = pk[key]; n += len(vals)
    for col, a, b in zip(('Award', 'Cap', 'E[S]', 'Target', 'Exit', 'Expiry'), vals, ref):
        if a != b: diffs.append(dict(table='6', arrears=r[0], W=r[1], procedure=r[2], column=col, wp=a, package=b))
print(f'Table 6: {len(w)} rows, {n} cells compared, {len(diffs)} differing')
with open(sys.argv[3], 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=['table', 'arrears', 'W', 'procedure', 'column', 'wp', 'package']); wr.writeheader(); wr.writerows(diffs)
for d in diffs: print(d)
