"""Cell-by-cell reconciliation of the working paper's numerical tables against the LaTeX tables
written by the replication package's table scripts.

Usage: python3 reconcile.py <wp.tex> <pkg_tex_dir> <out_prefix>
Compares, for each mapped pair, the ordered sequence of numeric and placeholder tokens in the
table body (from \\midrule to \\bottomrule). Reports every position at which the tokens differ.
"""
import csv
import re
import sys

MAP = [  # (WP label, WP number, package file, package label)
    ("tab:c1B", "4", "tables_numerical.tex", "tab:B"),
    ("tab:c3example", "5", "c3_tables_main.tex", "tab:c3example"),
    ("tab:c1A", "D1", "tables_numerical.tex", "tab:A"),
    ("tab:c1C", "D2", "tables_numerical.tex", "tab:C"),
    ("tab:c1B0", "D3", "tables_numerical.tex", "tab:B0"),
    ("tab:c3types", "D4", "c3_tables_main.tex", "tab:c3types"),
    ("tab:c3award", "D5", "c3_tables_main.tex", "tab:c3auction"),
    ("tab:c3oper", "D6", "c3_tables_main.tex", "tab:c3oper"),
    ("tab:c3pool", "D7", "c3_tables_appendix.tex", "tab:c3design"),
    ("tab:c3select_awarded", "D8", "c3_tables_appendix.tex", "tab:c3select"),
    ("tab:c3select_common", "D9", "c3_tables_appendix.tex", "tab:c3selectvbar"),
    ("tab:c4peropp", "D10", "c4_tables_main.tex", "tab:c4opp"),
    ("tab:c4cond", "D11", "c4_tables_main.tex", "tab:c4award"),
    ("tab:c4access", "D12", "c4_tables_main.tex", "tab:c4ar"),
    ("tab:c4decomp", "D13", "c4_tables_main.tex", "tab:c4dec"),
    ("tab:c4peropp_pen", "D14", "c4_tables_appendix.tex", "tab:c4opppen"),
    ("tab:c4cond_pen", "D15", "c4_tables_appendix.tex", "tab:c4awardpen"),
    ("tab:c4access_pen", "D16", "c4_tables_appendix.tex", "tab:c4arpen"),
    ("tab:c4decomp_pen", "D17", "c4_tables_appendix.tex", "tab:c4decpen"),
    ("tab:c4monotone", "D18", "c4_tables_appendix.tex", "tab:c4mono"),
]

TOK = re.compile(r"n\.a\.|---|--|\u2014|\u2013|-?\d+(?:,\d{3})*(?:\.\d+)?")


def table_block(tex, label):
    i = tex.index("\\label{" + label + "}")
    start = tex.rfind("\\begin{table}", 0, i)
    end = tex.index("\\end{table}", i)
    return tex[start:end]


def body(block):
    i = block.index("\\midrule")
    j = block.index("\\bottomrule", i)
    return block[i + len("\\midrule"):j]


def norm(s):
    s = s.replace("\u2212", "-")
    s = re.sub(r"\\(addlinespace|cmidrule\([^)]*\)\{[^}]*\}|cmidrule\{[^}]*\}|hline|midrule)", " ", s)
    s = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}", " ", s)
    s = re.sub(r"\\(text(bf|it|rm)?|emph|makecell|mathrm)\b", " ", s)
    s = s.replace("\\(", " ").replace("\\)", " ").replace("$", " ")
    s = re.sub(r"-\s+(?=\d)", "-", s)          # "- 0.004" -> "-0.004"
    s = re.sub(r"\{,\}", ",", s)
    return s


def rows(block):
    out = []
    for r in body(block).split("\\\\"):
        r = norm(r)
        toks = TOK.findall(r)
        if toks:
            out.append([t.replace("\u2014", "--").replace("\u2013", "--").replace("---", "--")
                        for t in toks])
    return out


def main(wp_path, pkg_dir, out_prefix):
    wp = open(wp_path, encoding="utf-8").read()
    summary, diffs = [], []
    for wl, num, pf, pl in MAP:
        pkg = open(f"{pkg_dir}/{pf}", encoding="utf-8").read()
        a, b = rows(table_block(wp, wl)), rows(table_block(pkg, pl))
        fa = [t for r in a for t in r]
        fb = [t for r in b for t in r]
        nd = 0
        for k in range(max(len(fa), len(fb))):
            x = fa[k] if k < len(fa) else "<missing>"
            y = fb[k] if k < len(fb) else "<missing>"
            if x != y:
                nd += 1
                diffs.append(dict(table=num, wp_label=wl, position=k, wp=x, package=y))
        summary.append(dict(table=num, wp_label=wl, package_file=pf, package_label=pl,
                            wp_rows=len(a), package_rows=len(b), wp_tokens=len(fa),
                            package_tokens=len(fb), differing_positions=nd))
    for name, data in (("summary", summary), ("differences", diffs)):
        with open(f"{out_prefix}_{name}.csv", "w", newline="") as f:
            keys = list(data[0]) if data else ["table"]
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(data)
    for s in summary:
        print(f"Table {s['table']:>4}  rows {s['wp_rows']:>3}/{s['package_rows']:<3} "
              f"tokens {s['wp_tokens']:>4}/{s['package_tokens']:<4} differing {s['differing_positions']}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
