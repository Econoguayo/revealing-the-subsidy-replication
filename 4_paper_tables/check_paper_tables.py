"""Compare the numeric cells of each generated table with the table of the same label in the paper.
Usage: python check_paper_tables.py PAPER.tex DIR [DIR ...]
  PAPER.tex  LaTeX source of the working paper (not part of this package)
  DIR        folders holding generated tables, normally output/paper_tables (Tables 4 to 6 and D1 to D18)
             and ../1_concessionality/output/table1 (Table 1)
Only decimal entries in the first tabular of each table are compared (for Table 1, Panel A); rows must contain
'&'; notes are excluded; minus signs are preserved after alternative symbols are mapped to '-'.
The generated tables of paper_tables.py carry the paper's labels; MAP translates the remaining labels written
by the model and concessionality scripts. Output: one line per generated table and a final count."""
import re, sys, glob

def tables(text):
    out = {}
    for m in re.finditer(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", text, re.S):
        t = m.group(0)
        lab = re.search(r"\\label\{(tab:[^}]+)\}", t)
        if lab:
            out[lab.group(1)] = t
    return out

def norm(r):
    """Common representation of minus signs: U+2212, \\textminus, $-$ and a dash before a number become '-'; ranges ('--', or a dash after a digit) become ' to '."""
    r = r.replace("\\textminus", "-").replace("\u2212", "-").replace("$-$", "-")
    r = re.sub(r"(?<=\d)\s*(--|\u2013|\u2014)\s*(?=\d)", " to ", r)
    r = r.replace("\u2013", "-").replace("\u2014", "-").replace("--", "-")
    return r.replace("$", "").replace("\\", " ")

def cells(t):
    body = re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", t, re.S)
    txt = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}|\\cmidrule(\([^)]*\))?\{[^}]*\}", " ", body.group(0) if body else "")
    rows = [r for r in txt.split("\\\\") if "&" in r]
    toks = [re.findall(r"(?<![\d.])-?\d+(?:\.\d+)?", norm(r)) for r in rows]
    return [t for t in toks if t]

# Labels written by the table scripts and the labels used in the paper
MAP = {"tab:c3auction": "tab:c3award", "tab:c3design": "tab:c3pool", "tab:c3select": "tab:c3select_awarded",
       "tab:c3selectvbar": "tab:c3select_common", "tab:c4ar": "tab:c4access", "tab:c4arpen": "tab:c4access_pen",
       "tab:c4award": "tab:c4cond", "tab:c4awardpen": "tab:c4cond_pen", "tab:c4dec": "tab:c4decomp",
       "tab:c4decpen": "tab:c4decomp_pen", "tab:c4mono": "tab:c4monotone", "tab:c4opp": "tab:c4peropp",
       "tab:c4opppen": "tab:c4peropp_pen", "tab:concessionality-dispersion": "tab:concessionality"}
paper = tables(open(sys.argv[1], encoding="utf-8").read())
dirs = sys.argv[2:] or ["paper_tables"]
gen = {}
for d in dirs:
    for p in sorted(glob.glob(f"{d}/*.tex")):
        gen.update(tables(open(p, encoding="utf-8").read()))
bad = 0
for lab, t in sorted(gen.items()):
    pl = MAP.get(lab, lab)
    ok = pl in paper and cells(t) == cells(paper[pl])
    bad += not ok
    print(("match   " if ok else "DIFFER  ") + lab + (f"  (paper: {pl})" if pl != lab else ""))
print(f"{len(gen) - bad} of {len(gen)} generated tables match the paper")
