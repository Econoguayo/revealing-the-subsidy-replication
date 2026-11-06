"""Trace numerical summaries in the running text of the working paper to the package's results files.
Usage: python3 trace_text.py <package_dir> <out.csv>
Revised November 5, 2026 for the replication package: E15b checks the qualified wording of the
round-7 paper ("expected disbursement under the awarded cap changes by at most 0.04"), and F10b
compares each end of the range at its own printed precision (0.0002 and 0.011).
Each check states the claim as printed, the source, the value computed from the results files and a
verdict: match (agrees at the printed precision), differs, or definition unclear."""
import csv, json, sys
from decimal import Decimal, ROUND_HALF_UP

P = sys.argv[1]
rd = lambda f: list(csv.DictReader(open(f"{P}/{f}")))
num = lambda x: float(x) if x not in ("", "None") else None
A0 = rd("results_L0/exercise_A_reference_viability.csv")
B0, B2 = rd("results_L0/exercise_B_participation_map.csv"), rd("results_Lm2/exercise_B_participation_map.csv")
T = rd("results_c3/c3_types.csv"); AU = rd("results_c3/c3_auction.csv"); DS = rd("results_c3/c3_design_summary.csv")
HC = rd("results_c3/c3_higher_cost_decomposition.csv"); EO = rd("results_c3/c3_exit_ordering.csv")
EV = rd("results_c3/c3_exit_violation_dates.csv")
CMP = rd("results_c4/c4_comparison.csv"); DEC = rd("results_c4/c4_decomposition.csv")
AR = rd("results_c4/c4_access_rules.csv"); MON = rd("results_c4/c4_cap_monotonicity.csv")
STAGE = json.load(open(f"{P}/results_c3/c3_type_stage.json"))
L0 = lambda rows: [r for r in rows if r["L"] == "0.0"]
Lm = lambda rows: [r for r in rows if r["L"] == "-2.0"]

out = []


def r_(x, nd):
    return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


def rng(cid, where, claim, vals, lo, hi, nd, scale=1.0, source=""):
    v = [x * scale for x in vals if x is not None]
    nd_lo, nd_hi = nd if isinstance(nd, tuple) else (nd, nd)
    a, b = r_(min(v), nd_lo), r_(max(v), nd_hi)
    ok = (a == lo and b == hi)
    out.append(dict(id=cid, location=where, claim=claim, source=source, computed=f"{a} to {b}",
                    verdict="match" if ok else "differs"))


def eq(cid, where, claim, computed, expected, source=""):
    out.append(dict(id=cid, location=where, claim=claim, source=source, computed=str(computed),
                    verdict="match" if str(computed) == str(expected) else "differs"))


def note(cid, where, claim, computed, verdict, source=""):
    out.append(dict(id=cid, location=where, claim=claim, source=source, computed=computed, verdict=verdict))


def by(rows, **kw):
    return [r for r in rows if all(r[k] == v for k, v in kw.items())]


# ---------------- Section 5.3 ----------------
# return on I for c = 26 over 20 years: 20 = 4 * annuity(r, 20)
lo, hi = 0.0, 1.0
for _ in range(100):
    m = (lo + hi) / 2
    pv = sum(4 / (1 + m) ** t for t in range(1, 21))
    lo, hi = (m, hi) if pv > 20 else (lo, m)
note("P1", "5.3", "reference project (c = 26, 20 years) returns about 19 percent on I", f"{100*lo:.2f} percent",
     "match" if round(100 * lo) == 19 else "differs", "IRR of 20 annual payments of 30 - 26 on I = 20")
a8 = [r for r in A0 if r["r_c"] == "0.08"]
rng("P2", "5.3", "target 5 to 54 percent above I where a target suffices (r_c = 0.08)",
    [num(r["W_over_I_min"]) - 1 for r in a8 if num(r["W_over_I_min"]) is not None], "5", "54", 0, 100,
    "exercise_A W_over_I_min")
none = [(r["c"], r["rho"]) for r in a8 if num(r["W_over_I_min"]) is None]
eq("P2b", "5.3", "no target suffices only for the high-cost type at rho = 0.20", none, [("26.0", "0.2")], "exercise_A")
eq("P3", "5.3", "W = I: participation set empty for all 12 types, both shocks",
   sum(r["status"] == "empty" for r in B0 if r["W"] == "20.0"), 24, "exercise_B L0")
meets = [r for r in B0 if num(r["U_ref"]) >= 0]
eq("P4", "5.3", "60 combinations meet the outside option on the reference path; in 10 no cap restores participation",
   f"{len(meets)} / {sum(r['status'] == 'empty' for r in meets)}", "60 / 10", "exercise_B L0, U_ref >= 0")
eq("P5", "5.3", "interior minimum cap in 5 of 36 (p05) and 13 of 36 (p10) cells, W > I",
   f"{sum(r['status']=='threshold found' for r in B0 if r['shock']=='p05')} / {sum(r['status']=='threshold found' for r in B0 if r['shock']=='p10')}",
   "5 / 13", "exercise_B L0")
it = [r for r in B0 if r["status"] == "threshold found"]
rng("P6", "5.3", "expected disbursement 21 to 74 percent of the cap at V* (18 interior cases)",
    [num(r["at_Vstar_E_expenditure"]) / num(r["Vstar"]) for r in it], "21", "74", 0, 100, "exercise_B L0")
k2 = {(r["shock"], r["W"], r["c"], r["rho"]): r for r in B2}
same = all(r["status"] == k2[(r["shock"], r["W"], r["c"], r["rho"])]["status"] for r in B0)
mv = max(abs(num(r["Vstar"]) - num(k2[(r["shock"], r["W"], r["c"], r["rho"])]["Vstar"])) for r in it)
note("P7", "5.3", "penalty leaves classification unchanged; no minimum cap moves by more than 0.4",
     f"classification unchanged: {same}; max move {mv:.3f}", "match" if same and mv <= 0.4 else "differs",
     "exercise_B L0 vs Lm2")

# ---------------- Section 6.3 (C3, costless exit) ----------------
ds0 = L0(DS)
largest = sum(int(r["n_zero"]) > max(int(r["n_positive"]), int(r["n_abstain"])) for r in ds0)
eq("E1", "6.3", "no-support sponsors are the largest group in four of six designs", largest, 4, "c3_design_summary")
rng("E1b", "6.3", "between two and six of the twelve types abstain", [int(r["n_abstain"]) for r in ds0], "2", "6", 0, 1, "c3_design_summary")
a0 = L0(AU)
rng("E2", "6.3 and 8.1", "single qualifier in 7 to 67 percent of awards", [num(r["p_single_given_award"]) for r in a0], "7", "67", 0, 100, "c3_auction")
rng("E3", "6.3", "expected awarded cap 2.6 to 19.5", [num(r["cap_given_award"]) for r in a0], "2.6", "19.5", 1, 1, "c3_auction")
rng("E3b", "6.3", "winner's expected minimum cap 0.1 to 4.6", [num(r["own_v_given_award"]) for r in a0], "0.1", "4.6", 1, 1, "c3_auction")
rng("E4", "6.3", "E[S] under awarded cap 0.63 to 6.28", [num(r["ES_cap_given_award"]) for r in a0], "0.63", "6.28", 2, 1, "c3_auction")
rng("E4b", "6.3", "E[S] under own minimum cap 0.05 to 2.21", [num(r["ES_own_given_award"]) for r in a0], "0.05", "2.21", 2, 1, "c3_auction")
sh = {(r["shock"], r["W"], r["n"]): num(r["share_of_ES_gap_from_single_qualifier"]) for r in a0}
oth = [k for k in sh if not (k[0] == "p10" and k[1] in ("30.0", "34.0") and k[2] == "3")]
rng("E5", "6.3", "single-qualifier awards: 54 to 81 percent of the gap in ten combinations", [sh[k] for k in oth], "54", "81", 0, 100, "c3_auction")
eq("E5b", "6.3", "39 and 34 percent for W = 30 and 34, p10, n = 3",
   f"{r_(100*sh[('p10','30.0','3')],0)} and {r_(100*sh[('p10','34.0','3')],0)}", "39 and 34", "c3_auction")
rng("E6", "6.3", "no-support sponsor awarded Vbar: E[S] 3.1 to 9.7", [num(r["vbar_E_expenditure"]) for r in L0(T) if r["category"] == "zero"], "3.1", "9.7", 1, 1, "c3_types")
cz = [num(r["p_cap_zero_given_award"]) / num(r["p_contested_given_award"]) for r in a0]
rng("E7", "6.3", "cap zero in 11 to 91 percent of contested awards", cz, "11", "91", 0, 100, "c3_auction: p_cap_zero_given_award / p_contested_given_award")
rng("E8", "6.3", "positive cap and acceptors differ in cost: 7 to 61 percent of contested awards", [num(r["p_informative_given_contested"]) for r in a0], "7", "61", 0, 100, "c3_auction")
rng("E9", "6.3", "winner strictly lowest in 55 to 100 percent of these awards", [num(r["p_winner_min_ES_informative"]) for r in a0], "55", "100", 0, 100, "c3_auction")
eq("E9b", "6.3", "no ties among these awards", sum(num(r["inf_tie_same"]) + num(r["inf_tie_diff"]) for r in a0) == 0, True, "c3_auction inf_tie_*")
rng("E10", "6.3", "average excess 0 to 0.46", [num(r["mean_excess_ES_informative"]) for r in a0], "0.00", "0.46", 2, 1, "c3_auction")
rng("E11", "6.3", "awarded cap raises target probability by 0.02 to 0.12", [num(r["tgt_cap_given_award"]) - num(r["tgt_own_given_award"]) for r in a0], "0.02", "0.12", 2, 1, "c3_auction")
rng("E11b", "6.3", "awarded cap lowers exit probability by 0.01 to 0.06", [num(r["ext_own_given_award"]) - num(r["ext_cap_given_award"]) for r in a0], "0.01", "0.06", 2, 1, "c3_auction")
for cid, col, lo_, hi_ in (("E12a", "tgt_cap_given_award", "0.65", "0.90"), ("E12b", "ext_cap_given_award", "0.03", "0.13"),
                           ("E12c", "exp_cap_given_award", "0.07", "0.22"), ("E12d", "tgt_own_given_award", "0.57", "0.85"),
                           ("E12e", "ext_own_given_award", "0.04", "0.17"), ("E12f", "exp_own_given_award", "0.11", "0.26")):
    rng(cid, "6.3", f"{col} {lo_} to {hi_}", [num(r[col]) for r in a0], lo_, hi_, 2, 1, "c3_auction")
m0 = L0(MON)
eq("E13", "6.3", "E[S] and U nondecreasing across awardable caps for every participating type and design",
   all(r["ES_nondecreasing"] == "True" and r["U_nondecreasing"] == "True" for r in m0), True, "c4_cap_monotonicity L0")
eq("E14", "6.3", "target falls for 13 of 50, by at most 0.028; exit rises for 20 of 50, by at most 0.053",
   f"{sum(r['target_nondecreasing']=='False' for r in m0)} of {len(m0)}, {r_(max(num(r['max_fall_target']) for r in m0),3)}; "
   f"{sum(r['exit_nonincreasing']=='False' for r in m0)} of {len(m0)}, {r_(max(num(r['max_rise_exit']) for r in m0),3)}",
   "13 of 50, 0.028; 20 of 50, 0.053", "c4_cap_monotonicity L0")
tk = {(r["shock"], r["W"], r["c"], r["rho"]): r for r in Lm(T)}
flip = any(r["category"] != tk[(r["shock"], r["W"], r["c"], r["rho"])]["category"] for r in L0(T))
dv = max(abs(num(r["Vstar"]) - num(tk[(r["shock"], r["W"], r["c"], r["rho"])]["Vstar"])) for r in L0(T) if r["Vstar"] not in ("", "None"))
eq("E15", "6.3", "penalty: no type flips category; minimum caps move by at most 0.39", f"flip={flip}; {r_(dv,2)}", "flip=False; 0.39", "c3_types L0 vs L-2")
cands = {}
for col in ("own_E_expenditure", "vbar_E_expenditure"):
    cands[col] = max(abs(num(r[col]) - num(tk[(r["shock"], r["W"], r["c"], r["rho"])][col]))
                     for r in L0(T) if r[col] not in ("", "None") and tk[(r["shock"], r["W"], r["c"], r["rho"])][col] not in ("", "None"))
ak = {(r["shock"], r["W"], r["n"]): r for r in Lm(AU)}
cands["ES_cap_given_award"] = max(abs(num(r["ES_cap_given_award"]) - num(ak[(r["shock"], r["W"], r["n"])]["ES_cap_given_award"])) for r in a0)
note("E15b", "6.3", "penalty: expected disbursement under the awarded cap changes by at most 0.04",
     "; ".join(f"{k}: {v:.3f}" for k, v in cands.items()),
     "match" if round(cands["ES_cap_given_award"], 2) <= 0.04 else "differs", "c3_auction L0 vs L-2 (ES_cap_given_award)")
rng("E16", "6.3", "penalty: exit under awarded cap 0.008 to 0.022", [num(r["ext_cap_given_award"]) for r in Lm(AU)], "0.008", "0.022", 3, 1, "c3_auction L-2")
rng("E16b", "6.3", "penalty: expiry before W 0.08 to 0.31", [num(r["exp_cap_given_award"]) for r in Lm(AU)], "0.08", "0.31", 2, 1, "c3_auction L-2")

# ---------------- Section 6.4 (C4) ----------------
def arm(rows, measure, n_in=("2", "3")):
    return [r for r in rows if r["measure"] == measure and r["n"] in n_in]
ar0, arm2 = L0(AR), Lm(AR)
print("access-rules measures:", sorted({r["measure"] for r in AR}))
rng("F1", "6.4", "auction E[S] per opportunity lower than sequential by 0.96 to 5.35", [-num(r["rules"]) for r in arm(ar0, "ES")], "0.96", "5.35", 2, 1, "c4_access_rules rules term")
rng("F1b", "6.4", "target lower by 0.01 to 0.09", [-num(r["rules"]) for r in arm(ar0, "tgt")], "0.01", "0.09", 2, 1, "c4_access_rules")
rng("F1c", "6.4", "exit higher by 0.01 to 0.07", [num(r["rules"]) for r in arm(ar0, "ext")], "0.01", "0.07", 2, 1, "c4_access_rules")
rng("F2", "6.4", "exposure per opportunity lower by 4.1 to 22.3", [-num(r["rules"]) for r in arm(ar0, "cap")], "4.1", "22.3", 1, 1, "c4_access_rules")
rng("F2b", "6.4", "surplus per opportunity lower by 0.20 to 1.56", [-num(r["rules"]) for r in arm(ar0, "surplus")], "0.20", "1.56", 2, 1, "c4_access_rules")
eq("F2c", "6.4", "expiry higher in eleven of the twelve combinations", sum(num(r["rules"]) > 0 for r in arm(ar0, "exp")), 11, "c4_access_rules")
c0 = L0(CMP)
for n_, lo_, hi_ in (("2", "8.6", "19.5"), ("3", "2.6", "15.1")):
    rng(f"F4n{n_}", "6.4", f"awarded cap given award, n = {n_}: {lo_} to {hi_}", [num(r["cap_given_award"]) for r in c0 if r["n"] == n_], lo_, hi_, 1, 1, "c4_comparison")
rng("F5", "6.4", "posted-offer E[S] given award 3.96 to 9.15", [num(r["ES_given_award"]) for r in c0 if r["n"] == "1"], "3.96", "9.15", 2, 1, "c4_comparison n = 1")
d0 = L0(DEC)
rng("F5b", "6.4", "auction E[S] lower given award by 1.28 to 5.43", [num(r["difference"]) for r in d0 if r["measure"] == "ES"], "1.28", "5.43", 2, 1, "c4_decomposition")
rng("F5c", "6.4", "surplus lower by 0.27 to 1.57", [num(r["difference"]) for r in d0 if r["measure"] == "surplus"], "0.27", "1.57", 2, 1, "c4_decomposition")
rng("F6", "6.4", "access term raises E[S] per opportunity by 0.69 to 2.72", [num(r["access"]) for r in arm(ar0, "ES")], "0.69", "2.72", 2, 1, "c4_access_rules")
rng("F6b", "6.4", "access term raises target by 0.12 to 0.33", [num(r["access"]) for r in arm(ar0, "tgt")], "0.12", "0.33", 2, 1, "c4_access_rules")
rng("F6c", "6.4", "access term raises exit by 0.002 to 0.017", [num(r["access"]) for r in arm(ar0, "ext")], "0.002", "0.017", 3, 1, "c4_access_rules")
sg = all(num(r["access"]) * num(r["rules"]) < 0 for r in arm(ar0, "ES") + arm(ar0, "tgt")) and all(num(r["access"]) * num(r["rules"]) > 0 for r in arm(ar0, "ext"))
eq("F6d", "6.4", "rules term opposite in sign to access for E[S] and target, same for exit", sg, True, "c4_access_rules")
rng("F7", "6.4", "auction target per opportunity exceeds single offer by 0.04 to 0.30", [num(r["total"]) for r in arm(ar0, "tgt")], "0.04", "0.30", 2, 1, "c4_access_rules total")
pos = [(r["shock"], r["W"], r["n"]) for r in arm(ar0, "ES") if num(r["total"]) > 0]
eq("F8", "6.4", "auction E[S] per opportunity exceeds single offer in 2 of 12 combinations, both p10 W = 27", pos, [("p10", "27.0", "2"), ("p10", "27.0", "3")], "c4_access_rules total")
eq("F8b", "6.4", "half of the types abstain in p10 W = 27", by(ds0, shock="p10", W="27.0")[0]["n_abstain"], "6", "c3_design_summary")
es0 = [r for r in d0 if r["measure"] == "ES"]
rng("F9", "6.4", "selection term 0.02 to 0.53", [num(r["selection_at_vbar"]) for r in es0], "0.02", "0.53", 2, 1, "c4_decomposition ES")
rng("F9b", "6.4", "cap term 1.07 to 5.07", [num(r["cap_term"]) for r in es0], "1.07", "5.07", 2, 1, "c4_decomposition ES")
rng("F9c", "6.4", "cap term 84 to 99 percent of the difference", [num(r["cap_term"]) / num(r["difference"]) for r in es0], "84", "99", 0, 100, "c4_decomposition ES")
rng("F10", "6.4", "at Vbar, winner's target higher by 0.004 to 0.063", [-num(r["selection_at_vbar"]) for r in d0 if r["measure"] == "tgt"], "0.004", "0.063", 3, 1, "c4_decomposition tgt selection")
rng("F10b", "6.4", "at Vbar, winner's exit lower by 0.0002 to 0.011", [num(r["selection_at_vbar"]) for r in d0 if r["measure"] == "ext"], "0.0002", "0.011", (4, 3), 1, "c4_decomposition ext selection")
rng("F11", "6.4", "target lower at awarded cap than at Vbar by 0.03 to 0.14", [num(r["cap_term"]) for r in d0 if r["measure"] == "tgt"], "0.03", "0.14", 2, 1, "c4_decomposition tgt cap term")
rng("F11b", "6.4", "exit higher at awarded cap by 0.01 to 0.08", [-num(r["cap_term"]) for r in d0 if r["measure"] == "ext"], "0.01", "0.08", 2, 1, "c4_decomposition ext cap term")
eq("F12", "6.4", "surplus: selection term negative and cap term positive everywhere",
   all(num(r["selection_at_vbar"]) < 0 and num(r["cap_term"]) > 0 for r in d0 if r["measure"] == "surplus"), True, "c4_decomposition surplus")
rng("F13", "6.4", "penalty: auction E[S] per opportunity lower by 0.95 to 5.31", [-num(r["rules"]) for r in arm(arm2, "ES")], "0.95", "5.31", 2, 1, "c4_access_rules L-2")
rng("F13b", "6.4", "penalty: target lower by 0.01 to 0.08", [-num(r["rules"]) for r in arm(arm2, "tgt")], "0.01", "0.08", 2, 1, "c4_access_rules L-2")
rng("F13c", "6.4", "penalty: exit difference -0.004 to 0.017", [num(r["rules"]) for r in arm(arm2, "ext")], "-0.004", "0.017", 3, 1, "c4_access_rules L-2")
eq("F13d", "6.4", "penalty: auction exit higher in eight of twelve", sum(num(r["rules"]) > 0 for r in arm(arm2, "ext")), 8, "c4_access_rules L-2")

# ---------------- Appendix C ----------------
rng("C2", "App. C", "winner at Vbar strictly lowest in 24 to 56 percent of contested awards", [num(r["vb_strict"]) for r in a0], "24", "56", 0, 100, "c3_auction vb_strict")
rng("C2b", "App. C", "tied in 34 to 44 percent", [num(r["vb_tie_same"]) + num(r["vb_tie_diff"]) for r in a0], "34", "44", 0, 100, "c3_auction vb_tie_*")
eq("C2c", "App. C", "every tie is with sponsors of the winner's operating cost", all(num(r["vb_tie_diff"]) == 0 for r in a0), True, "c3_auction vb_tie_diff")
rng("C3", "App. C", "higher-cost winner in 6 to 37 percent", [num(r["vb_higher"]) for r in a0], "6", "37", 0, 100, "c3_auction vb_higher")
rng("C3b", "App. C", "mean excess at Vbar 0.09 to 0.52", [num(r["mean_excess_ES_at_vbar"]) for r in a0], "0.09", "0.52", 2, 1, "c3_auction")
h0 = L0(HC)
rng("C4", "App. C", "p05: 60 to 100 percent of higher-cost wins are ties at zero", [num(r["tie_share_of_higher_cost"]) for r in h0 if r["shock"] == "p05"], "60", "100", 0, 100, "c3_higher_cost_decomposition")
rng("C4b", "App. C", "p10: 0 to 47 percent", [num(r["tie_share_of_higher_cost"]) for r in h0 if r["shock"] == "p10"], "0", "47", 0, 100, "c3_higher_cost_decomposition")
rng("C5", "App. C", "higher-cost win with strictly lower V*: 0 to 13 percent of contested awards", [num(r["p_strictly_lower_Vstar"]) for r in h0], "0", "13", 0, 100, "c3_higher_cost_decomposition")
rng("C6", "App. C", "qualifiers differ in cost in 61 to 80 percent of contested awards", [num(r["vb_diffcost_given_contested"]) for r in a0], "61", "80", 0, 100, "c3_auction")

# ---------------- Appendix A (exit ordering) ----------------
eo0, eo2 = L0(EO), Lm(EO)
eq("A2", "App. A", "costless exit: condition fails for all 138 pairs at Vbar and all 464 pair-cap combinations",
   f"{sum(int(r['pairs_vbar']) for r in eo0)}/{sum(int(r['pairs_vbar_condition_holds']) for r in eo0)}; {sum(int(r['pair_caps_all']) for r in eo0)}/{sum(int(r['pair_caps_all_condition_holds']) for r in eo0)}",
   "138/0; 464/0", "c3_exit_ordering L0")
pv = [val[1] for s in STAGE if s["L"] == 0.0 for k, val in s["order"].items() if k.endswith("|25.0") and not val[0]]
pa = [val[1] for s in STAGE if s["L"] == 0.0 for k, val in s["order"].items() if not k.endswith("|25.0") and not val[0]]
note("A3", "App. A", "violating histories: probability 0.003 to 0.07 at Vbar; at most 0.15 at lower caps",
     f"{r_(min(pv),3)} to {r_(max(pv),2)}; {r_(max(pa),2)}",
     "match" if (r_(min(pv), 3), r_(max(pv), 2), r_(max(pa), 2)) == ("0.003", "0.07", "0.15") else "differs", "c3_type_stage order")
ev0 = L0(EV)
eq("A4", "App. A", "exits in years 15 to 19", f"{min(int(r['earliest_exit_date']) for r in ev0)} to {max(int(r['latest_exit_date']) for r in ev0)}", "15 to 19", "c3_exit_violation_dates")
mn = min(num(r["share_lower_cost_ends_by_exit"]) + num(r["share_lower_cost_ends_by_expiry"]) for r in ev0)
note("A4b", "App. A", "more than 96.9 percent: lower-cost concession ends by a later exit or at expiry", f"minimum {100*mn:.1f} percent",
     "match" if 100 * mn > 96.9 - 1e-9 else "differs", "c3_exit_violation_dates")
eq("A5", "App. A", "penalty: condition holds for 60 of 138 pairs at Vbar and 232 of 464 combinations",
   f"{sum(int(r['pairs_vbar_condition_holds']) for r in eo2)} of {sum(int(r['pairs_vbar']) for r in eo2)}; {sum(int(r['pair_caps_all_condition_holds']) for r in eo2)} of {sum(int(r['pair_caps_all']) for r in eo2)}",
   "60 of 138; 232 of 464", "c3_exit_ordering L-2")
rng("A5b", "App. A", "penalty: holds for every pair in 31 to 55 percent of contested awards with qualifiers of different cost, at Vbar", [num(r["vb_order"]) for r in Lm(AU)], "31", "55", 0, 100, "c3_auction vb_order L-2")
note("A5c", "App. A", "penalty: in at most 61 percent of restricted awards", f"max {100*max(num(r['inf_order']) for r in Lm(AU)):.1f} percent",
     "match" if r_(100 * max(num(r["inf_order"]) for r in Lm(AU)), 0) == "61" else "differs", "c3_auction inf_order L-2")
eq("A6", "App. A", "costless exit: no restricted award, and no contested award at Vbar, satisfies the condition for every pair",
   all(num(r["inf_order"]) == 0 and num(r["vb_order"]) == 0 for r in a0), True, "c3_auction inf_order, vb_order L0")
ex = {r["c"] + "|" + r["rho"]: r for r in by(L0(T), shock="p10", W="30.0")}
eq("A1", "App. A", "example pair at Vbar: E[S] 8.55 and 6.81; exit 0.06 and 0.03",
   f"{r_(num(ex['25.0|0.1']['vbar_E_expenditure']),2)} and {r_(num(ex['24.0|0.15']['vbar_E_expenditure']),2)}; {r_(num(ex['25.0|0.1']['vbar_p_abandon']),2)} and {r_(num(ex['24.0|0.15']['vbar_p_abandon']),2)}",
   "8.55 and 6.81; 0.06 and 0.03", "c3_types p10 W30 L0")
st = [s for s in STAGE if s["shock"] == "p10" and s["W"] == 30.0 and s["L"] == 0.0][0]
v = st["order"].get("2|4|25.0")
note("A1b", "App. A", "the higher-cost sponsor exits first on histories with probability 0.02", str(v),
     "match" if v and r_(v[1], 2) == "0.02" else "differs", "c3_type_stage order 2|4|25.0")

with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "location", "claim", "source", "computed", "verdict"])
    w.writeheader(); w.writerows(out)
from collections import Counter
print(Counter(o["verdict"] for o in out))
for o in out:
    if o["verdict"] != "match":
        print(o)
