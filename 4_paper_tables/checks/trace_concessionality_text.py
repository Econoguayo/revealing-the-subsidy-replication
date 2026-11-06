"""Trace the concessionality numbers printed in the running text (Section 2, the note to Table 1 and
Appendix E) to the frozen data of the concessionality component.

Usage: python trace_concessionality_text.py FROZEN_DIR OUT_CSV
  FROZEN_DIR  1_concessionality/data/frozen_2026-10-07
  OUT_CSV     output file (one row per statement: id, location, claim, computed, verdict)

Each statement is written as printed in the working paper (source md5 7b4aa5ab, November 4, 2026).
The regressions repeat the definitions of code/recovered/build_table1_concessionality.py
(same sample filter, regressors, sponsor groups and cross-validation); fragility follows the
registry's designation, as in that table. Verdicts: match (agrees at the printed precision),
differs, or wording (the data support the number but the sentence can be read more than one way).
"""
import csv, json, math, re, sys
from collections import Counter

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

P, OUT = sys.argv[1], sys.argv[2]
reg = json.load(open(f"{P}/psw_data.json", encoding="utf-8"))
ifc = json.load(open(f"{P}/final_dataset.json", encoding="utf-8"))
mig = json.load(open(f"{P}/miga_results.json", encoding="utf-8"))
comb = json.load(open(f"{P}/combined_dataset.json", encoding="utf-8"))
rows = list(csv.DictReader(open(f"{P}/psw_concessionality_combined.csv", encoding="utf-8")))
out = []


def chk(cid, where, claim, computed, expected, verdict=None):
    v = verdict or ("match" if str(computed) == str(expected) else "differs")
    out.append(dict(id=cid, location=where, claim=claim, computed=str(computed), verdict=v))


# ---------------- counts (Section 2 and Appendix E) ----------------
est = [r for r in rows if r["concessionality_pct"]]
tpc_ifc = [r for r in est if r["agency"] == "IFC" and r["denominator_type"] == "total project cost"]
tpc_all = [r for r in est if r["denominator_type"] == "total project cost"]
migr = [r for r in est if r["agency"] == "MIGA"]
n_ifc_link = sum(1 for r in reg if r.get("IFCDisclosure1"))
n_mig_link = sum(1 for r in reg if r.get("MIGADisclosure1"))
n_both = sum(1 for r in reg if r.get("IFCDisclosure1") and r.get("MIGADisclosure1"))
ifc_ok = sum(1 for r in ifc if r.get("page") == "fetched")
mig_ok = sum(1 for r in mig if r.get("page") == "fetched")
chk("E1", "Sec. 2; App. E", "204 Board-approved transactions on the published list", len(reg), 204)
chk("E2", "App. E", "IFC disclosure links listed for 152 transactions", n_ifc_link, 152)
chk("E3", "App. E", "MIGA disclosure links listed for 34 transactions", n_mig_link, 34)
chk("E4", "App. E", "pages retrieved for 151 IFC transactions", ifc_ok, 151)
chk("E5", "App. E", "pages retrieved for all MIGA transactions", f"{mig_ok} of {len(mig)}", f"{n_mig_link} of {n_mig_link}")
chk("E6", "App. E", "three transactions list both links", n_both, 3)
chk("E7", "App. E", "182 unique transactions with at least one retrieved page", ifc_ok + mig_ok - n_both, 182)
chk("E8", "Sec. 2; App. E", "119 transactions disclose an estimate", len(est), 119)
c = Counter(r["agency"] for r in est)
chk("E9", "App. E", "106 IFC and 13 MIGA estimates", f"{c['IFC']} IFC, {c['MIGA']} MIGA", "106 IFC, 13 MIGA")
chk("E10", "App. E", "105 estimates against total project cost (92 IFC, 13 MIGA)",
    f"{len(tpc_all)} ({len(tpc_ifc)} IFC, {len(tpc_all) - len(tpc_ifc)} MIGA)", "105 (92 IFC, 13 MIGA)")
chk("E11", "Sec. 2; App. E; Table 1", "92 IFC transactions report estimates as shares of total project cost", len(tpc_ifc), 92)
other = [r for r in est if r["denominator_type"] != "total project cost"]
chk("E12", "App. E", "14 estimates not expressed against total project cost", len(other), 14)
chk("E13", "App. E", "two state no denominator", sum(r["denominator_type"] == "unstated" for r in other), 2)
top = sorted(tpc_ifc, key=lambda r: -float(r["concessionality_pct"]))[:2]
chk("E14", "App. E", "two largest estimates 60 and 51 percent, both Local Currency Facility",
    "; ".join(f"{float(r['concessionality_pct']):g} ({r['Facility']})" for r in top), "60 (LCF); 51 (LCF)")
ub = sum(r["is_upper_bound"] == "True" for r in migr)
chk("E15", "Sec. 2; App. E", "eleven of the thirteen MIGA estimates are upper bounds", f"{ub} of {len(migr)}", "11 of 13")
gy = sorted(int(r["guarantee_years"]) for r in migr if r["guarantee_years"])
chk("E16", "App. E", "MIGA guarantee periods from six to twenty years", f"{gy[0]} to {gy[-1]} ({len(gy)} of {len(migr)} stated)", "6 to 20 (13 of 13 stated)")
rng = [r for r in est if r["is_range"] == "True"]
brk = [r for r in rng if "[" in r["sentence"]]
chk("E17", "App. E", "one disclosure provides a range (recorded by lower bound, upper bound and midpoint)",
    f"{len(rng)} estimates carry a range; {len(brk)} of them inside square brackets "
    f"({', '.join(r['ProjName'] for r in brk)}); unbracketed: {', '.join(r['ProjName'] for r in rng if r not in brk)}",
    None, verdict="wording")
v = np.array(sorted(float(r["concessionality_pct"]) for r in tpc_ifc))
ratio = float(pd.Series(v).quantile(0.9) / pd.Series(v).quantile(0.1))
chk("E18", "Sec. 2; App. E", "90th/10th percentile ratio 9.1 (a factor of nine)", f"{ratio:.1f}", "9.1")

# ---------------- disclosure rates by fragility (registry coding) ----------------
any_page = []
for i, r in enumerate(reg):
    m = [x for x in mig if x["ProjName"] == r["ProjName"] and x.get("ReplenishmentCode") == r["ReplenishmentCode"]
         and x.get("url") == r.get("MIGADisclosure1")]
    any_page.append(ifc[i].get("page") == "fetched" or (bool(m) and m[0].get("page") == "fetched"))
fig = [comb[i].get("concessionality_pct") is not None for i in range(len(reg))]
fcs = [r["FCS/FCV"] for r in reg]
def rate(grp, pages_only):
    idx = [i for i in range(len(reg)) if fcs[i] == grp and (any_page[i] or not pages_only)]
    return 100 * sum(fig[i] for i in idx) / len(idx)
chk("E19", "App. E", "retrieved pages: 58 percent of FCS transactions state an estimate, 70 percent of others",
    f"{rate('FCS', True):.0f} and {rate('non-FCS', True):.0f}", "58 and 70")
chk("E20", "App. E", "full registry: 56 and 60 percent", f"{rate('FCS', False):.0f} and {rate('non-FCS', False):.0f}", "56 and 60")

# ---------------- regressions (Section 2, note to Table 1) ----------------
ok = [r for r in comb if r.get("concessionality_pct") is not None and r.get("denominator_type") == "total project cost" and r["agency"] == "IFC"]
df = pd.DataFrame([{"conc": r["concessionality_pct"], "fac": r["Facility"], "ind": r["Industry"], "cycle": r["ReplenishmentCode"],
                    "fcs": r["FCS/FCV"], "cost": r.get("project_cost_musd"), "name": r["ProjName"], "cty": r["Country"]} for r in ok])
df["fac2"] = df.fac.apply(lambda s: "BFF" if s == "BFF" else ("LCF" if s == "LCF" else "mixed"))
df["ind2"] = df.ind.str.split("/").str[0].str.strip().str[:22]
df["lc"] = np.log(df.conc)
df["rowid"] = range(len(df))
SPON = [("nmb", "NMB Tanzania", "Tanzania"), ("kicb", "KICB Kyrgyz", "Kyrgyz"), ("sonatel", "Sonatel group", None),
        ("acep", "ACEP", None), ("orange", "Sonatel group", None)]
def grp(r):
    n = r["name"].lower()
    for tok, lab, cty in SPON:
        if re.search(r"\b" + tok, n) and (cty is None or cty.lower() in r["cty"].lower()):
            return lab
    return "solo::" + r["name"]
df["grp"] = df.apply(grp, axis=1)
multi = df[~df.grp.str.startswith("solo::")]
chk("R1", "Table 1 note", "11 transactions belong to the four sponsors that appear more than once",
    f"{len(multi)} transactions, {multi.grp.nunique()} sponsors", "11 transactions, 4 sponsors")

def cv(sub, f, by):
    e = []
    for k in sub[by].unique():
        tr, te = sub[sub[by] != k], sub[sub[by] == k]
        p = smf.ols(f, data=tr).fit().predict(te)
        e += [a - b for a, b in zip(te.lc.values, p.values) if not np.isnan(b)]
    return math.sqrt(np.mean(np.array(e) ** 2))

F1, F2, FULL = "lc ~ C(fac2)", "lc ~ C(fac2)+C(ind2)", "lc ~ C(fac2)+C(ind2)+C(cycle)+C(fcs)"
r2_fac = smf.ols(F1, data=df).fit().rsquared
r2_ind = smf.ols(F2, data=df).fit().rsquared
chk("R2", "Sec. 2", "facility alone explains 32 percent of the variation", f"{100 * r2_fac:.0f}", "32")
chk("R3", "Sec. 2", "adding industry raises this to 41 percent", f"{100 * r2_ind:.0f}", "41")
b1, b2 = cv(df, "lc ~ 1", "rowid"), cv(df, "lc ~ 1", "grp")
f1, f2 = cv(df, FULL, "rowid"), cv(df, FULL, "grp")
chk("R4", "Sec. 2", "full specification reduces leave-one-out RMSE by 15.6 percent", f"{100 * (1 - f1 / b1):.1f}", "15.6")
chk("R5", "Sec. 2", "or 15.4 percent when all transactions of a sponsor are held out together", f"{100 * (1 - f2 / b2):.1f}", "15.4")
chk("R6", "Table 1 note", "reduction in mean squared error for the full conditioning set 28.8 percent", f"{100 * (1 - (f1 / b1) ** 2):.1f}", "28.8")
sub = df.dropna(subset=["cost"]).copy()
chk("R7", "Table 1 note", "final row: 79 transactions report a project cost", len(sub), 79)
chk("R8", "Table 1 note", "benchmark for those 79 observations is 2.57 rather than 2.47",
    f"{math.exp(cv(sub, 'lc ~ 1', 'rowid')):.2f} rather than {math.exp(b1):.2f}", "2.57 rather than 2.47")

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "location", "claim", "computed", "verdict"])
    w.writeheader()
    w.writerows(out)
print(Counter(o["verdict"] for o in out))
for o in out:
    if o["verdict"] != "match":
        print(o["id"], o["verdict"], o["computed"])
