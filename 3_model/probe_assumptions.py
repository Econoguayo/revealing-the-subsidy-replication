"""Probes reported in the C1 note.

1. Pathwise ordering under a fixed exit date when A2 (rho > r_c) or A4 (Lambda_W >= L) is dropped.
2. End-game exit under costless exit: exit probabilities by period for one case.
Seeds are fixed; results are printed and written to results_probes.json.
"""
import json
import numpy as np
from lpvs_core import Contract, Environment, SponsorType, payoff_on_path

import lpvs_core


def draw(rng, mode):
    r_c = rng.uniform(0.02, 0.12)
    if mode == "rho_below_rc":
        rho = r_c - rng.uniform(0.005, 0.02)          # rho < r_c, rho > 0
    else:
        rho = r_c + rng.uniform(0.005, 0.12)          # A2 holds
    k = Contract(W=rng.uniform(10, 60), Rstar=26.0, kappa=rng.uniform(0.3, 0.95),
                 sbar=rng.uniform(2, 25), r_c=r_c, r_f=0.05, Tbar=15)
    if mode == "L_above_Lam":
        Lam = rng.uniform(0, 5); L = Lam + rng.uniform(1, 10)   # A4 fails
    else:
        Lam = rng.uniform(0, 10); L = rng.uniform(0, Lam)       # A4 holds
    env = Environment(R=(30.0, rng.uniform(0, 25)), I=20.0, Lam=Lam, L=L)
    typ = SponsorType(c=rng.uniform(20, 29), rho=rho)
    path = list(rng.integers(0, 2, 15))
    a = None if rng.random() < 0.5 else int(rng.integers(1, 15))
    V1, V2 = sorted(rng.uniform(0, 80, 2))
    return (payoff_on_path(path, V2, typ, k, env, a) - payoff_on_path(path, V1, typ, k, env, a))


def ordering_probe(mode, n=4000, seed=0):
    rng = np.random.default_rng(seed)
    diffs = np.array([draw(rng, mode) for _ in range(n)])
    return dict(mode=mode, draws=n, seed=seed, violations=int((diffs < -1e-9).sum()),
                worst=float(diffs.min()))


def endgame_probe():
    src = open(lpvs_core.__file__).read().replace(
        "        E_excess_to_owner_pv=Eexcess_pv,\n    )",
        "        E_excess_to_owner_pv=Eexcess_pv,\n        p_abandon_by_t=p_aband.tolist(),\n    )")
    ns = {}
    exec(compile(src, "lpvs_core_diag", "exec"), ns)
    k = ns["Contract"](W=20.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=20)
    out = {}
    for L in (0.0, -2.0):
        env = ns["Environment"](R=(30.0, 20.0), P=((0.95, 0.05), (1/3, 2/3)), I=20.0, L=L)
        o = ns["solve"](0.0, ns["SponsorType"](25.0, 0.15), k, env)
        out[f"L={L}"] = dict(p_exit=float(o["p_abandon"]), p_exit_by_t=[round(x, 6) for x in o["p_abandon_by_t"]],
                             p_target=float(o["p_target"]))
    return out


if __name__ == "__main__":
    res = dict(baseline=ordering_probe("A2_A4_hold"),
               rho_below_rc=ordering_probe("rho_below_rc"),
               L_above_Lam=ordering_probe("L_above_Lam"),
               endgame_case=dict(description="W=I=20, r_c=0.08, c=25, rho=0.15, arrears entry 0.05, V=0",
                                 **endgame_probe()))
    json.dump(res, open("results_probes.json", "w"), indent=2)
    print(json.dumps({k: v for k, v in res.items() if k != "endgame_case"}, indent=1))
    e = res["endgame_case"]
    for L in ("L=0.0", "L=-2.0"):
        print(L, round(e[L]["p_exit"], 4), "at t=5:", e[L]["p_exit_by_t"][5])
