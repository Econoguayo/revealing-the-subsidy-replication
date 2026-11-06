"""Diagnostic for the exit-ordering condition of Proposition 3 at the common cap Vbar (baseline, costless exit).

For every design and every pair of participating types with different operating costs, collects the
histories on which the higher-cost type exits before the lower-cost type's concession ends, and
reports the distribution (by probability) of the higher-cost exit date and of how the lower-cost
concession ends on those histories. Reads results_c3/c3_type_stage.json; writes
results_c3/c3_exit_violation_dates.csv. No random numbers are used.
"""
import collections, csv, json
from multiprocessing import Pool
import numpy as np
from lpvs_core import Contract, Environment, SponsorType, solve, leaf_probabilities
from c3_selection import BASE, I, VBAR, R_C, SHOCKS, TYPES, WS

ST = {(t["shock"], t["W"], t["L"]): t for t in json.load(open("results_c3/c3_type_stage.json"))}


def job(a):
    shock, W = a
    ts = ST[(shock, W, 0.0)]
    R, P = SHOCKS[shock]
    env = Environment(R=R, P=P, I=I, Lam=0.0, L=0.0)
    k = Contract(W=W, r_c=R_C, Vbar=VBAR, **BASE)
    p = leaf_probabilities(k, env)
    part = [j for j in range(len(TYPES)) if ts["vstar"][str(j)] is not None]
    o = {j: solve(VBAR, SponsorType(*TYPES[j]), k, env, policy=True) for j in part}
    dates, lend = collections.Counter(), collections.Counter()
    for i in part:
        for j in part:
            if TYPES[i][0] < TYPES[j][0]:
                v = (o[j]["leaf_kind"] == 1) & (o[j]["leaf_end"] < o[i]["leaf_end"])
                for idx in np.nonzero(v)[0]:
                    dates[int(o[j]["leaf_end"][idx])] += p[idx]
                    lend[int(o[i]["leaf_kind"][idx])] += p[idx]
    s = sum(dates.values())
    row = dict(shock=shock, W=W, L=0.0, earliest_exit_date=min(dates), latest_exit_date=max(dates))
    for d in range(1, k.Tbar):
        if d in dates:
            row[f"share_exit_date_{d}"] = dates[d] / s
    for kind, name in ((0, "target"), (1, "exit"), (2, "expiry")):
        row[f"share_lower_cost_ends_by_{name}"] = lend[kind] / s
    return row


if __name__ == "__main__":
    with Pool(2) as pool:
        rows = pool.map(job, [(s, W) for s in SHOCKS for W in WS])
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open("results_c3/c3_exit_violation_dates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    for r in rows:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
