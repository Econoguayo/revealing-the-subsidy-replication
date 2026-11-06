"""Tractability check for the core LPVS contract (single sponsor; no auction, no bidder counts).

Exercise A. Reference-case viability: the smallest compensation target W (as a multiple of I)
            at which a sponsor's payoff on the all-normal path reaches its outside option,
            by sponsor discount rate rho and contractual rate r_c.
Exercise B. Participation map with shocks: for each design (W, r_c) and shock process, classify
            each sponsor type as participating without support, having an interior minimum cap V*,
            or having an empty participation set. Interior cases get the grid diagnostic before
            any threshold search.
Exercise C. Outcomes at V* for the interior cases: committed exposure, expected expenditure,
            stopping outcomes, operating periods, cap exhaustion.

All parameters are assumptions; none is calibrated. Exact computation on the tree of state
histories; no random numbers are used in the results.
"""
import csv, hashlib, json, platform, sys, datetime
from multiprocessing import Pool
import numpy as np

from lpvs_core import (Contract, Environment, SponsorType, solve, V_max, reference_payoff,
                       participation_threshold)

import os as _os
L_EXIT = float(_os.environ.get("L_EXIT", "0.0"))   # value at exit (baseline 0: costless exit; -2: termination penalty)
OUT = _os.environ.get("OUT_DIR", "results")
BASE = dict(Rstar=26.0, kappa=0.8, sbar=10.0, r_f=0.05, Tbar=20)
I = 20.0
TYPES_C = (24.0, 25.0, 26.0)
TYPES_RHO = (0.10, 0.12, 0.15, 0.20)
SHOCKS = {"p05": ((30.0, 20.0), ((0.95, 0.05), (1/3, 2/3))),
          "p10": ((30.0, 20.0), ((0.90, 0.10), (1/3, 2/3)))}
DESIGNS_B = [(20.0, 0.08), (27.0, 0.08), (30.0, 0.08), (34.0, 0.08)]


def exercise_A():
    rows = []
    env = Environment(R=(30.0, 20.0), I=I, L=L_EXIT)
    for c in TYPES_C:
        for rho in TYPES_RHO:
            for r_c in (0.06, 0.08, 0.10, 0.12):
                typ = SponsorType(c=c, rho=rho)
                k_hi = Contract(W=1e6, r_c=r_c, **BASE)
                u_full = reference_payoff(typ, k_hi, env)       # concession runs to Tbar
                if u_full < typ.omega:
                    rows.append(dict(c=c, rho=rho, r_c=r_c, W_over_I_min=None,
                                     U_ref_at_W_eq_I=reference_payoff(typ, Contract(W=I, r_c=r_c, **BASE), env),
                                     note="not attainable within Tbar"))
                    continue
                lo, hi = 0.0, 1e6
                for _ in range(200):
                    mid = 0.5 * (lo + hi)
                    if reference_payoff(typ, Contract(W=mid, r_c=r_c, **BASE), env) >= typ.omega:
                        hi = mid
                    else:
                        lo = mid
                    if hi - lo < 1e-6:
                        break
                rows.append(dict(c=c, rho=rho, r_c=r_c, W_over_I_min=hi / I,
                                 U_ref_at_W_eq_I=reference_payoff(typ, Contract(W=I, r_c=r_c, **BASE), env),
                                 note=""))
    return rows


def _case_B(args):
    shock, W, r_c, c, rho = args
    R, P = SHOCKS[shock]
    env = Environment(R=R, P=P, I=I, L=L_EXIT)
    k = Contract(W=W, r_c=r_c, **BASE)
    typ = SponsorType(c=c, rho=rho)
    vm = V_max(k, env)
    U0 = solve(0.0, typ, k, env)["U"]
    Um = solve(vm, typ, k, env)["U"]
    Uref = reference_payoff(typ, k, env)
    row = dict(shock=shock, W=W, r_c=r_c, c=c, rho=rho, V_max=vm, U_0=U0, U_Vmax=Um, U_ref=Uref)
    if Um < typ.omega:
        row.update(status="empty", Vstar=None, grid_monotone=None)
    elif U0 >= typ.omega:
        row.update(status="no support needed", Vstar=0.0, grid_monotone=None)
    else:
        res = participation_threshold(typ, k, env, grid_n=21, tol=1e-4)
        row.update(status=res["status"], Vstar=res["Vstar"], grid_monotone=res["monotone_on_grid"])
    if row["Vstar"] is not None:
        o = solve(row["Vstar"], typ, k, env)
        row.update({f"at_Vstar_{key}": val for key, val in o.items() if key != "V"})
    o0 = solve(0.0, typ, k, env)
    row.update({f"at_0_{key}": o0[key] for key in ("p_target", "p_abandon", "p_expiry", "E_periods")})
    return {k_: (float(v) if isinstance(v, (np.floating,)) else v) for k_, v in row.items()}


def exercise_B():
    jobs = [(s, W, r_c, c, rho) for s in SHOCKS for (W, r_c) in DESIGNS_B
            for c in TYPES_C for rho in TYPES_RHO]
    with Pool(2) as pool:
        return pool.map(_case_B, jobs)


def write_csv(path, rows):
    keys = sorted({k for r in rows for k in r})
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    A = exercise_A(); write_csv(f"{OUT}/exercise_A_reference_viability.csv", A)
    B = exercise_B(); write_csv(f"{OUT}/exercise_B_participation_map.csv", B)
    manifest = dict(
        run_utc=datetime.datetime.utcnow().isoformat(timespec="seconds"),
        python=sys.version.split()[0], numpy=np.__version__, platform=platform.platform(),
        code_sha256_16={f: sha(f) for f in ("lpvs_core.py", "run_tractability.py")},
        assumptions=dict(BASE=BASE, I=I, TYPES_C=TYPES_C, TYPES_RHO=TYPES_RHO, SHOCKS=SHOCKS,
                         DESIGNS_B=DESIGNS_B, Lam=0.0, L=L_EXIT, omega=0.0, z0="normal",
                         exit_timing="end of period, on observed state history",
                         settlement="support first; excess operating cash to asset owner"),
        random_numbers="none in results (exact tree computation)",
        outputs={f: sha(f"{OUT}/{f}") for f in os.listdir(OUT) if f.endswith(".csv")},
    )
    json.dump(manifest, open(f"{OUT}/manifest.json", "w"), indent=2, default=str)
    print("done", len(A), len(B))
