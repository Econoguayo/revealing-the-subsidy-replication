"""C3: selection, expenditure and operating outcomes under the second-price award rule.

Designs: common tender terms W in {27, 30, 34}, r_c = 0.08, terminal value 0, maximum admissible
cap Vbar = 25; arrears entry 0.05 or 0.10 a year. Exit value L = 0 (baseline, costless exit) or
L = -2 (termination penalty). Sponsor pool: the 12 types c in {24, 25, 26} x rho in
{0.10, 0.12, 0.15, 0.20}, drawn independently and uniformly; every type is kept, whether it needs
no support, has a positive minimum cap, or abstains because no admissible cap suffices.

Award rule (C2): a bid qualifies if it does not exceed Vbar; sponsors bid their minimum acceptable
caps (threshold bids; weakly dominant given assumption A6, which holds in the baseline);
with two or more qualifying bids the lowest bidder wins and
receives the second-lowest qualifying bid as its cap; with one qualifying bid the bidder receives
Vbar; with none there is no award; ties are broken at random.

Selection comparisons: at the awarded cap, among the sponsors that would accept it (all contested
awards, and the restricted set with a positive cap and acceptors of different operating costs), and
at the common cap Vbar among all qualifying sponsors. The winner is classified as strictly lowest,
tied (within TOL_ES) or not lowest in expected disbursement. For every pair of sponsors that accept a
cap and differ in operating cost, the script checks on all 2**Tbar histories the exit-ordering
condition of Proposition 3 (the higher-cost sponsor does not exit before the lower-cost concession
ends).

All expectations over bidder draws are exact (full enumeration of type profiles); outcomes for a
sponsor at a cap come from the exact tree solver. No random numbers are used.
"""
import csv, hashlib, itertools, json, os, sys, datetime, platform
from multiprocessing import Pool
import numpy as np

from lpvs_core import Contract, Environment, SponsorType, solve, participation_threshold, leaf_probabilities

BASE = dict(Rstar=26.0, kappa=0.8, sbar=10.0, r_f=0.05, Tbar=20)
I = 20.0
VBAR = 25.0
R_C = 0.08
TYPES = [(c, rho) for c in (24.0, 25.0, 26.0) for rho in (0.10, 0.12, 0.15, 0.20)]
SHOCKS = {"p05": ((30.0, 20.0), ((0.95, 0.05), (1/3, 2/3))),
          "p10": ((30.0, 20.0), ((0.90, 0.10), (1/3, 2/3)))}
WS = (27.0, 30.0, 34.0)
LS = (0.0, -2.0)
NS = (2, 3)
TOL_ES = 0.01   # expenditure differences below this are treated as ties (exit effects within a cost group are of order 1e-4)
OUTCOME_KEYS = ("E_expenditure", "p_target", "p_abandon", "p_expiry", "E_periods", "U",
                "p_cap_exhausted")


def type_stage(args):
    """Classify every type and tabulate outcomes at every cap that can be awarded."""
    shock, W, L = args
    R, P = SHOCKS[shock]
    env = Environment(R=R, P=P, I=I, Lam=0.0, L=L)
    k = Contract(W=W, r_c=R_C, Vbar=VBAR, **BASE)
    cat, vstar, mono = {}, {}, {}
    for j, (c, rho) in enumerate(TYPES):
        typ = SponsorType(c=c, rho=rho)
        U0 = solve(0.0, typ, k, env)["U"]
        Ub = solve(VBAR, typ, k, env)["U"]
        if Ub < typ.omega:
            cat[j], vstar[j], mono[j] = "abstain", None, None
        elif U0 >= typ.omega:
            cat[j], vstar[j], mono[j] = "zero", 0.0, None
        else:
            res = participation_threshold(typ, k, env, grid_n=21, tol=1e-4)
            if res["Vstar"] is None:
                raise RuntimeError(f"threshold search failed: {args} type {j}: {res['status']}")
            cat[j], vstar[j], mono[j] = "positive", float(res["Vstar"]), bool(res["monotone_on_grid"])
    caps = sorted({v for v in vstar.values() if v is not None} | {VBAR})
    prob = leaf_probabilities(k, env)
    table, order = {}, {}
    for v in caps:
        stop = {}
        for j in vstar:
            if vstar[j] is None:
                continue
            typ = SponsorType(c=TYPES[j][0], rho=TYPES[j][1])
            o = solve(v, typ, k, env, policy=True)
            table[(j, v)] = {key: float(o[key]) for key in OUTCOME_KEYS}
            if vstar[j] <= v:
                stop[j] = (o["leaf_end"], o["leaf_kind"])
        # exit-ordering condition of Proposition 3 for every pair that accepts cap v and differs in cost:
        # on every history, the higher-cost sponsor does not exit before the lower-cost concession ends
        for i in stop:
            for j in stop:
                if TYPES[i][0] < TYPES[j][0]:
                    viol = (stop[j][1] == 1) & (stop[j][0] < stop[i][0])
                    order[(i, j, v)] = (not bool(viol.any()), float(prob[viol].sum()))
    return dict(shock=shock, W=W, L=L, cat=cat, vstar=vstar, mono=mono, caps=caps, table=table, order=order)


def exit_order_holds(ts, sponsors, cap):
    """True if the exit-ordering condition holds on every history for every pair of the given
    sponsors (type indices) that differ in operating cost, all evaluated at the same cap."""
    order = ts["order"]
    for i in set(sponsors):
        for j in set(sponsors):
            if TYPES[i][0] < TYPES[j][0] and not order[(i, j, cap)][0]:
                return False
    return True


def classify(w, others, es_of):
    """Winner's expected disbursement against the other sponsors in the comparison set:
    'strict' (below every other by more than TOL_ES), 'tie_same' or 'tie_diff' (within TOL_ES of
    the lowest other; tie partners all of the winner's operating cost, or at least one of a
    different cost), or 'higher' (above the lowest other by more than TOL_ES)."""
    ew = es_of(w)
    eo = [es_of(j) for j in others]
    dgap = ew - min(eo)
    if dgap < -TOL_ES:
        return "strict"
    if dgap > TOL_ES:
        return "higher"
    partners = [j for j, e in zip(others, eo) if abs(e - ew) <= TOL_ES]
    return "tie_diff" if any(TYPES[j][0] != TYPES[w][0] for j in partners) else "tie_same"


def drop_one(lst, x):
    out = list(lst)
    out.remove(x)
    return out


def auction_stage(ts, n):
    """Exact expectations over all n-profiles of types under the second-price award rule."""
    cat, vstar, tab = ts["cat"], ts["vstar"], ts["table"]
    m = len(TYPES)
    p_prof = (1.0 / m) ** n
    acc = dict(p_award=0.0, p_single=0.0, p_cap_zero=0.0,
               cap=0.0, own_v=0.0, ES_cap=0.0, ES_own=0.0,
               tgt_cap=0.0, ext_cap=0.0, exp_cap=0.0, per_cap=0.0,
               tgt_own=0.0, ext_own=0.0, exp_own=0.0, per_own=0.0,
               win_zero=0.0, win_pos=0.0,
               p_cmp=0.0, p_min_at_cap=0.0, excess_at_cap=0.0,
               p_cmp_common=0.0, p_min_at_vbar=0.0, excess_at_vbar=0.0, p_cost_above_min=0.0,
               p_inf=0.0, p_min_inf=0.0, excess_inf=0.0, gap_single=0.0, gap_total=0.0,
               inf_strict=0.0, inf_tie_same=0.0, inf_tie_diff=0.0, inf_higher=0.0, inf_order=0.0,
               vb_strict=0.0, vb_tie_same=0.0, vb_tie_diff=0.0, vb_higher=0.0, vb_order=0.0, vb_diff=0.0)
    for prof in itertools.product(range(m), repeat=n):
        Q = [j for j in prof if vstar[j] is not None]
        if not Q:
            continue
        bids = sorted(vstar[j] for j in Q)
        low = bids[0]
        cap = bids[1] if len(Q) >= 2 else VBAR
        winners = [j for j in Q if vstar[j] == low]
        w_p = p_prof / len(winners)
        acc["p_award"] += p_prof
        acc["p_single"] += p_prof * (len(Q) == 1)
        acc["p_cap_zero"] += p_prof * (cap == 0.0)
        acceptors = [j for j in Q if vstar[j] <= cap]
        for w in winners:
            oc, oo = tab[(w, cap)], tab[(w, vstar[w])]
            acc["cap"] += w_p * cap
            acc["own_v"] += w_p * vstar[w]
            acc["ES_cap"] += w_p * oc["E_expenditure"]
            acc["ES_own"] += w_p * oo["E_expenditure"]
            for key, src in (("tgt", "p_target"), ("ext", "p_abandon"), ("exp", "p_expiry"), ("per", "E_periods")):
                acc[f"{key}_cap"] += w_p * oc[src]
                acc[f"{key}_own"] += w_p * oo[src]
            acc["win_zero"] += w_p * (cat[w] == "zero")
            acc["win_pos"] += w_p * (cat[w] == "positive")
            # selection at the awarded cap, among sponsors that would accept it
            if len(acceptors) >= 2:          # contested award: winner and runner-up both accept the cap
                es = [tab[(j, cap)]["E_expenditure"] for j in acceptors]
                acc["p_cmp"] += w_p
                acc["p_min_at_cap"] += w_p * (oc["E_expenditure"] <= min(es) + TOL_ES)
                acc["excess_at_cap"] += w_p * (oc["E_expenditure"] - min(es))
                # informative comparison: positive cap and acceptors that differ in operating cost
                if cap > 0 and len({TYPES[j][0] for j in acceptors}) >= 2:
                    acc["p_inf"] += w_p
                    acc["p_min_inf"] += w_p * (oc["E_expenditure"] <= min(es) + TOL_ES)
                    acc["excess_inf"] += w_p * (oc["E_expenditure"] - min(es))
                    cls = classify(w, drop_one(acceptors, w), lambda j: tab[(j, cap)]["E_expenditure"])
                    acc["inf_" + cls] += w_p
                    acc["inf_order"] += w_p * exit_order_holds(ts, acceptors, cap)
            gap = oc["E_expenditure"] - oo["E_expenditure"]
            acc["gap_total"] += w_p * gap
            acc["gap_single"] += w_p * gap * (len(Q) == 1)
            # selection at a common cap (Vbar), among all qualifying sponsors in the profile
            if len(Q) >= 2:
                esv = [tab[(j, VBAR)]["E_expenditure"] for j in Q]
                acc["p_cmp_common"] += w_p
                acc["p_min_at_vbar"] += w_p * (tab[(w, VBAR)]["E_expenditure"] <= min(esv) + TOL_ES)
                acc["p_cost_above_min"] += w_p * (TYPES[w][0] > min(TYPES[j][0] for j in Q))
                acc["excess_at_vbar"] += w_p * (tab[(w, VBAR)]["E_expenditure"] - min(esv))
                cls = classify(w, drop_one(Q, w), lambda j: tab[(j, VBAR)]["E_expenditure"])
                acc["vb_" + cls] += w_p
                diff = len({TYPES[j][0] for j in Q}) >= 2     # qualifiers differ in operating cost
                acc["vb_diff"] += w_p * diff
                acc["vb_order"] += w_p * (diff and exit_order_holds(ts, Q, VBAR))
    pa = acc["p_award"]
    out = dict(shock=ts["shock"], W=ts["W"], L=ts["L"], n=n, p_award=pa,
               ES_per_opportunity=acc["ES_cap"])
    for key in ("p_single", "p_cap_zero", "cap", "own_v", "ES_cap", "ES_own", "tgt_cap", "ext_cap",
                "exp_cap", "per_cap", "tgt_own", "ext_own", "exp_own", "per_own", "win_zero", "win_pos"):
        out[key + "_given_award"] = acc[key] / pa if pa > 0 else None
    out["p_contested_given_award"] = acc["p_cmp"] / pa if pa > 0 else None
    out["p_informative_given_contested"] = acc["p_inf"] / acc["p_cmp"] if acc["p_cmp"] > 0 else None
    out["p_winner_min_ES_informative"] = acc["p_min_inf"] / acc["p_inf"] if acc["p_inf"] > 0 else None
    out["mean_excess_ES_informative"] = acc["excess_inf"] / acc["p_inf"] if acc["p_inf"] > 0 else None
    out["share_of_ES_gap_from_single_qualifier"] = acc["gap_single"] / acc["gap_total"] if acc["gap_total"] > 0 else None
    out["p_winner_min_ES_at_cap"] = acc["p_min_at_cap"] / acc["p_cmp"] if acc["p_cmp"] > 0 else None
    out["mean_excess_ES_at_cap"] = acc["excess_at_cap"] / acc["p_cmp"] if acc["p_cmp"] > 0 else None
    out["p_winner_min_ES_at_vbar"] = acc["p_min_at_vbar"] / acc["p_cmp_common"] if acc["p_cmp_common"] > 0 else None
    out["mean_excess_ES_at_vbar"] = acc["excess_at_vbar"] / acc["p_cmp_common"] if acc["p_cmp_common"] > 0 else None
    out["p_winner_cost_above_min"] = acc["p_cost_above_min"] / acc["p_cmp_common"] if acc["p_cmp_common"] > 0 else None
    out["p_comparable_common"] = acc["p_cmp_common"] / pa if pa > 0 else None
    for tag, den in (("inf", acc["p_inf"]), ("vb", acc["p_cmp_common"])):
        for cls in ("strict", "tie_same", "tie_diff", "higher"):
            out[f"{tag}_{cls}"] = acc[f"{tag}_{cls}"] / den if den > 0 else None
    # exit-ordering share: among comparisons that contain at least one pair with different operating costs
    out["inf_order"] = acc["inf_order"] / acc["p_inf"] if acc["p_inf"] > 0 else None
    out["vb_diffcost_given_contested"] = acc["vb_diff"] / acc["p_cmp_common"] if acc["p_cmp_common"] > 0 else None
    out["vb_order"] = acc["vb_order"] / acc["vb_diff"] if acc["vb_diff"] > 0 else None
    return out


def exit_order_rows(ts):
    """Pair-level summary of the exit-ordering condition at the common cap and at every awardable cap."""
    vb = [(key, val) for key, val in ts["order"].items() if key[2] == VBAR]
    allc = list(ts["order"].items())
    es_ordered = [ts["table"][(j, VBAR)]["E_expenditure"] >= ts["table"][(i, VBAR)]["E_expenditure"] - 1e-12
                  for (i, j, _), _v in vb]
    viol_vb = [val[1] for _k, val in vb if not val[0]]
    viol_all = [val[1] for _k, val in allc if not val[0]]
    es_ordered_all = [ts["table"][(j, v)]["E_expenditure"] >= ts["table"][(i, v)]["E_expenditure"] - 1e-12
                      for (i, j, v), _v in allc]
    return dict(shock=ts["shock"], W=ts["W"], L=ts["L"],
                pairs_vbar=len(vb), pairs_vbar_condition_holds=sum(val[0] for _k, val in vb),
                max_p_violation_vbar=max(viol_vb) if viol_vb else 0.0,
                pairs_vbar_ES_ordered=sum(es_ordered),
                pairs_vbar_ES_ordered_where_condition_fails=sum(o for o, (_k, val) in zip(es_ordered, vb) if not val[0]),
                pair_caps_all=len(allc), pair_caps_all_condition_holds=sum(val[0] for _k, val in allc),
                max_p_violation_all=max(viol_all) if viol_all else 0.0,
                pair_caps_all_ES_ordered=sum(es_ordered_all))


def decompose(ts, n):
    """Contested awards won by a higher-cost sponsor: ties at the lowest bid versus a strictly lower minimum cap."""
    vstar = ts["vstar"]
    m = len(TYPES)
    p = (1 / m) ** n
    contested = tot = tie = strict = 0.0
    for prof in itertools.product(range(m), repeat=n):
        Q = [j for j in prof if vstar[j] is not None]
        if len(Q) < 2:
            continue
        contested += p
        low = min(vstar[j] for j in Q)
        winners = [j for j in Q if vstar[j] == low]
        cmin = min(TYPES[j][0] for j in Q)
        for w in winners:
            wp = p / len(winners)
            if TYPES[w][0] > cmin:
                tot += wp
                lower = [j for j in Q if TYPES[j][0] < TYPES[w][0]]
                if all(vstar[j] > vstar[w] for j in lower):
                    strict += wp
                else:
                    tie += wp
    pos = sorted(v for v in vstar.values() if v is not None and v > 0)
    return dict(shock=ts["shock"], W=ts["W"], L=ts["L"], n=n,
                p_higher_cost=tot / contested, p_tie_break=tie / contested,
                p_strictly_lower_Vstar=strict / contested,
                tie_share_of_higher_cost=(tie / tot) if tot > 0 else None,
                duplicate_positive_Vstar_across_types=len(set(pos)) < len(pos))


def type_rows(ts):
    rows = []
    for j, (c, rho) in enumerate(TYPES):
        r = dict(shock=ts["shock"], W=ts["W"], L=ts["L"], c=c, rho=rho, category=ts["cat"][j],
                 Vstar=ts["vstar"][j], grid_monotone=ts["mono"][j])
        if ts["vstar"][j] is not None:
            for tag, v in (("own", ts["vstar"][j]), ("vbar", VBAR)):
                for key, val in ts["table"][(j, v)].items():
                    r[f"{tag}_{key}"] = val
        rows.append(r)
    return rows


def spearman(x, y):
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    if np.std(rx) == 0 or np.std(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


if __name__ == "__main__":
    out_dir = "results_c3"
    os.makedirs(out_dir, exist_ok=True)
    jobs = [(s, W, L) for L in LS for s in SHOCKS for W in WS]
    with Pool(2) as pool:
        stages = pool.map(type_stage, jobs)
    json.dump([dict(ts, table={f"{j}|{v}": o for (j, v), o in ts["table"].items()},
                    order={f"{i}|{j}|{v}": o for (i, j, v), o in ts["order"].items()}) for ts in stages],
              open(f"{out_dir}/c3_type_stage.json", "w"), default=str)
    trows, arows, crow = [], [], []
    for ts in stages:
        trows += type_rows(ts)
        for n in NS:
            arows.append(auction_stage(ts, n))
        q = [j for j in range(len(TYPES)) if ts["vstar"][j] is not None]
        vs = [ts["vstar"][j] for j in q]
        es_own = [ts["table"][(j, ts["vstar"][j])]["E_expenditure"] for j in q]
        es_vbar = [ts["table"][(j, VBAR)]["E_expenditure"] for j in q]
        crow.append(dict(shock=ts["shock"], W=ts["W"], L=ts["L"],
                         n_zero=sum(ts["cat"][j] == "zero" for j in range(len(TYPES))),
                         n_positive=sum(ts["cat"][j] == "positive" for j in range(len(TYPES))),
                         n_abstain=sum(ts["cat"][j] == "abstain" for j in range(len(TYPES))),
                         all_monotone=all(m_ is not False for m_ in ts["mono"].values()),
                         spearman_Vstar_ES_own=spearman(vs, es_own),
                         spearman_Vstar_ES_vbar=spearman(vs, es_vbar)))
    write_csv(f"{out_dir}/c3_types.csv", trows)
    write_csv(f"{out_dir}/c3_auction.csv", arows)
    write_csv(f"{out_dir}/c3_design_summary.csv", crow)
    write_csv(f"{out_dir}/c3_higher_cost_decomposition.csv", [decompose(ts, n) for ts in stages for n in NS])
    write_csv(f"{out_dir}/c3_exit_ordering.csv", [exit_order_rows(ts) for ts in stages])
    manifest = dict(
        run_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        python=sys.version.split()[0], numpy=np.__version__, platform=platform.platform(),
        code_sha256_16={f: sha(f) for f in ("lpvs_core.py", "c3_selection.py")},
        assumptions=dict(BASE=BASE, I=I, VBAR=VBAR, R_C=R_C, TYPES=TYPES, SHOCKS=SHOCKS, WS=WS, LS=LS,
                         NS=NS, TOL_ES=TOL_ES, Lam=0.0, omega=0.0, type_prior="uniform, independent draws",
                         bidding="each sponsor bids its minimum acceptable cap (threshold bid); weakly dominant under the C2 second-price rule given assumption A6 (payoff at a positive threshold equals the outside option), which holds in the baseline with L = Lam = 0 (working paper, Remark 1); for L = -2 the results describe allocations under threshold bids, without an equilibrium claim"),
        random_numbers="none (exact enumeration and exact tree computation)",
        outputs={f: sha(f"{out_dir}/{f}") for f in os.listdir(out_dir) if f.endswith(".csv")},
    )
    json.dump(manifest, open(f"{out_dir}/manifest.json", "w"), indent=2, default=str)
    print("done", len(trows), len(arows))
