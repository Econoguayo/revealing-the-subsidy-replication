"""Supplementary checks: worked example (Section 6.2, introduction), Table 6 cells cited in Section 6.4,
and the share comparison of Appendix C. Usage: python3 trace_text2.py <package_dir> <wp.tex> <out.csv>"""
import csv, sys, importlib.util, os
P, WP, OUT = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(sys.argv[0]))
spec = importlib.util.spec_from_file_location("rc", here + "/reconcile.py"); rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
rd = lambda f: list(csv.DictReader(open(f"{P}/{f}")))
wp = open(WP, encoding="utf-8").read()
out = []
t5 = rc.rows(rc.table_block(wp, "tab:c3example"))
flat5 = [t for r in t5 for t in r]
for v in ("1.125", "0.689", "0.587", "0.60", "0.15", "0.74", "0.10"):
    out.append(dict(id="X-" + v, location="Intro and 6.2", claim=f"worked example value {v}", source="Table 5 (reconciled with package)",
                    computed="present in Table 5" if v in flat5 else "not found in Table 5",
                    verdict="match" if v in flat5 else "check"))
C = rd("results_c4/c4_comparison.csv"); SEQ = rd("results_c4/c4_sequential.csv")
a = [r for r in C if r["shock"] == "p10" and r["W"] == "30.0" and r["L"] == "0.0" and r["n"] == "2"][0]
s = [r for r in SEQ if r["shock"] == "p10" and r["W"] == "30.0" and r["L"] == "0.0" and r["n"] == "2"][0]
f = lambda x, nd: f"{float(x):.{nd}f}"
got = (f(a["p_award"], 3), f(s["ES_per_opportunity"], 2), f(a["ES_per_opportunity"], 2), f(s["tgt_per_opportunity"], 3),
       f(a["tgt_per_opportunity"], 3), f(s["ext_per_opportunity"], 3), f(a["ext_per_opportunity"], 3))
exp = ("0.889", "7.44", "5.58", "0.708", "0.687", "0.050", "0.070")
out.append(dict(id="F3", location="6.4", claim="W = 30, p10, n = 2: award 0.889; E[S] 7.44 vs 5.58; target 0.708 vs 0.687; exit 0.050 vs 0.070",
                source="c4_comparison, c4_sequential", computed="; ".join(got), verdict="match" if got == exp else "differs"))
AU = [r for r in rd("results_c3/c3_auction.csv") if r["L"] == "0.0"]
HC = {(r["shock"], r["W"], r["n"]): r for r in rd("results_c3/c3_higher_cost_decomposition.csv") if r["L"] == "0.0"}
rows = []
for r in AU:
    notlow = float(r["p_contested_given_award"]) and 1 - float(r["p_winner_min_ES_at_cap"])
    rows.append(((r["shock"], r["W"], r["n"]), 1 - float(r["p_winner_min_ES_at_cap"]), float(HC[(r["shock"], r["W"], r["n"])]["p_strictly_lower_Vstar"])))
eq2 = all(abs(x - y) < 1e-12 for k, x, y in rows if k[2] == "2")
three = [(x, y) for k, x, y in rows if k[2] == "3"]
smaller = sum(x < y - 1e-12 for x, y in three); nolarger = all(x <= y + 1e-12 for x, y in three)
out.append(dict(id="C1", location="App. C", claim="n = 2: winner-not-lowest share equals strictly-lower-V* share; n = 3: no larger, smaller in five of six",
                source="c3_auction p_winner_min_ES_at_cap; c3_higher_cost_decomposition p_strictly_lower_Vstar",
                computed=f"n=2 equal: {eq2}; n=3 no larger: {nolarger}, smaller in {smaller} of 6",
                verdict="match" if eq2 and nolarger and smaller == 5 else "definition unclear"))
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "location", "claim", "source", "computed", "verdict"]); w.writeheader(); w.writerows(out)
for o in out: print(o["id"], o["verdict"], o["computed"])
