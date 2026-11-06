"""Core LPVS contract: smallest numerical implementation for the tractability check.

Model (outline of October 16, 2026):
  * Annual periods t = 1..Tbar. Revenue R_t follows an exogenous two-state Markov chain
    (state 0 = normal payment, state 1 = utility arrears), common to all sponsors and
    observed by the sponsor.
  * Payment rule:  s_t = min{ sbar, kappa*max(0, Rstar - R_t), (V - S_{t-1})(1+r_f)^t }.
    S_t = S_{t-1} + s_t (1+r_f)^(-t). The cap applies to gross disbursement and does not revolve.
  * Retained net cash x_t = R_t - c + s_t accumulates at r_c:  A_t = A_{t-1} + x_t (1+r_c)^(-t).
  * Compensation target: tau_W is the first t with A_{t-1} + (R_t - c + s_t)(1+r_c)^(-t) >= W.
    Support-first settlement at tau_W: the sponsor retains exactly M = (W - A_{t-1})(1+r_c)^t;
    support is reduced first; if operating cash R_t - c alone is >= M, no support is paid and the
    excess operating cash passes to the asset owner or successor. Only actual disbursement is
    recorded against the cap. The excess is kept separate from the sponsor's terminal value.
  * Termination: T* = min(tau_W, tau_A, Tbar). Terminal value Lam at handover (tau_W) and at expiry
    (Tbar); salvage L at abandonment. Abandonment is decided at the end of a period, on the state
    history observed to that date (exogenous states, so the history determines A and S).
  * Sponsor payoff  U(V) = -I + E[ sum_{t<=T*} x_t (1+rho)^(-t) + terminal (1+rho)^(-T*) ],
    under the optimal exit policy, computed exactly on the full binary tree of state histories.

Nothing here is calibrated: every parameter is an assumption stated by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import numpy as np


@dataclass(frozen=True)
class Contract:
    W: float            # compensation target (present value at r_c)
    Rstar: float        # viability threshold
    kappa: float        # coverage ratio
    sbar: float         # per-period support limit
    r_c: float          # contractual accumulation rate
    r_f: float          # fiscal discount rate (DFI)
    Tbar: int           # duration ceiling (periods)
    Vbar: float = np.inf  # maximum admissible cap


@dataclass(frozen=True)
class Environment:
    R: tuple = (30.0, 20.0)                 # revenue by state: (normal, arrears)
    P: tuple = ((0.95, 0.05), (1/3, 2/3))   # transition matrix P[from][to]
    z0: int = 0                             # state before period 1
    I: float = 25.0                         # sponsor's upfront investment
    Lam: float = 0.0                        # terminal value at handover and at expiry
    L: float = 0.0                          # salvage value at abandonment


@dataclass(frozen=True)
class SponsorType:
    c: float       # per-period operating cost (including scheduled debt service)
    rho: float     # private discount rate
    omega: float = 0.0  # outside option


# ---------------------------------------------------------------------------
# One period of the ledger (vectorized over nodes)
# ---------------------------------------------------------------------------
def period_step(t, R, A_prev, S_prev, V, c, k: Contract):
    """Apply the payment rule, accumulation and support-first settlement for period t.

    Returns s_paid, x (retained cash), excess (operating cash passed to the asset owner),
    A_new, S_new, hit (True where the compensation target is reached in period t).
    """
    R = np.asarray(R, dtype=float)
    A_prev = np.asarray(A_prev, dtype=float)
    S_prev = np.asarray(S_prev, dtype=float)
    gf = (1.0 + k.r_f) ** t
    gc = (1.0 + k.r_c) ** t
    g = np.minimum(k.sbar, k.kappa * np.maximum(0.0, k.Rstar - R))
    remaining_cap = np.maximum(0.0, (V - S_prev)) * gf
    s_raw = np.minimum(g, remaining_cap)
    op = R - c                                   # operating cash
    test = A_prev + (op + s_raw) / gc
    hit = test >= k.W
    M = (k.W - A_prev) * gc                      # retained cash needed to reach W exactly
    # support-first settlement where hit
    s_settle = np.where(op >= M, 0.0, M - op)    # <= s_raw because op + s_raw >= M
    excess = np.where(hit & (op >= M), op - M, 0.0)
    s_paid = np.where(hit, s_settle, s_raw)
    x = np.where(hit, M, op + s_raw)
    A_new = np.where(hit, k.W, A_prev + x / gc)
    S_new = S_prev + s_paid / gf
    return s_paid, x, excess, A_new, S_new, hit


def ledger_path(states, V, typ: SponsorType, k: Contract, env: Environment, abandon_after=None):
    """Deterministic ledger along one state path (list of 0/1 for periods 1..). For tests."""
    A, S = 0.0, 0.0
    rows = []
    for t, z in enumerate(states, start=1):
        if t > k.Tbar:
            break
        s, x, ex, A_new, S_new, hit = period_step(t, env.R[z], A, S, V, typ.c, k)
        rows.append(dict(t=t, z=z, R=env.R[z], s=float(s), x=float(x), excess=float(ex),
                         A=float(A_new), S=float(S_new), hit=bool(hit)))
        A, S = float(A_new), float(S_new)
        if hit:
            break
        if abandon_after is not None and t == abandon_after:
            break
    return rows


def payoff_on_path(states, V, typ: SponsorType, k: Contract, env: Environment, abandon_after=None):
    """Sponsor payoff (excluding -I) along one state path under a fixed abandonment date."""
    rows = ledger_path(states, V, typ, k, env, abandon_after)
    d = 1.0 / (1.0 + typ.rho)
    val = sum(r["x"] * d ** r["t"] for r in rows)
    T = rows[-1]["t"]
    if rows[-1]["hit"]:
        val += env.Lam * d ** T
    elif abandon_after is not None and T == abandon_after and T < k.Tbar:
        val += env.L * d ** T
    elif T == k.Tbar:
        val += env.Lam * d ** T
    else:
        raise ValueError("path shorter than the concession")
    return val


# ---------------------------------------------------------------------------
# Exact solution on the binary tree of state histories
# ---------------------------------------------------------------------------
def solve(V, typ: SponsorType, k: Contract, env: Environment, policy=False):
    """Exact sponsor payoff and outcome measures for cap V under the optimal exit policy.

    With policy=True, also returns, for each of the 2**Tbar state histories (leaf index in the
    order used by leaf_probabilities), the date on which the concession ends (leaf_end) and how it
    ends (leaf_kind: 0 compensation target, 1 exit, 2 expiry at Tbar).
    """
    T = k.Tbar
    P = np.array(env.P, dtype=float)
    Rv = np.array(env.R, dtype=float)
    d = 1.0 / (1.0 + typ.rho)

    # forward pass: ledger for every node at every level (policy-independent)
    lv = []  # per level t: dict of arrays for the 2^t children
    A = np.zeros(1); S = np.zeros(1); done = np.zeros(1, bool); zpar = np.array([env.z0])
    for t in range(1, T + 1):
        n = 2 ** t
        par = np.arange(n) // 2
        z = np.arange(n) % 2
        A_p, S_p, done_p, zp = A[par], S[par], done[par], zpar[par]
        s, x, ex, A_n, S_n, hit = period_step(t, Rv[z], A_p, S_p, V, typ.c, k)
        trans = P[zp, z]
        # nodes whose parent already terminated by handover are inactive
        s = np.where(done_p, 0.0, s); x = np.where(done_p, 0.0, x); ex = np.where(done_p, 0.0, ex)
        A_n = np.where(done_p, A_p, A_n); S_n = np.where(done_p, S_p, S_n)
        hit = np.where(done_p, False, hit)
        lv.append(dict(z=z, par=par, s=s, x=x, ex=ex, A=A_n, S=S_n, hit=hit,
                       done_p=done_p, trans=trans))
        A, S, done, zpar = A_n, S_n, (done_p | hit), z

    # backward pass: J[t] = value (time-0 PV, sponsor discounting) at end of period t,
    # for nodes alive and not yet handed over, under the optimal exit decision.
    J = [None] * (T + 1)
    abandon = [None] * (T + 1)
    # term value of a child at level t (value of reaching that node, excluding its x)
    def child_term(t):
        L_ = lv[t - 1]
        if t == T:
            # handover at T or expiry at T: both give Lam
            return np.full(2 ** t, env.Lam * d ** t)
        return np.where(L_["hit"], env.Lam * d ** t, J[t])

    for t in range(T - 1, 0, -1):
        ch = lv[t]  # children at level t+1
        contrib = ch["trans"] * (ch["x"] * d ** (t + 1) + child_term(t + 1))
        C = contrib.reshape(-1, 2).sum(axis=1)          # continuation value at level-t nodes
        Lval = env.L * d ** t
        J[t] = np.maximum(Lval, C)
        abandon[t] = Lval > C
    ch = lv[0]
    U0 = (ch["trans"] * (ch["x"] * d + child_term(1))).sum()
    U = -env.I + U0

    # forward probabilities under the optimal policy
    p_hand = np.zeros(T + 1); p_aband = np.zeros(T + 1); p_exp = 0.0
    ES = 0.0; Eexcess_pv = 0.0; P_exhaust = 0.0; EA_end = 0.0
    reach = np.ones(1)            # probability of reaching each node at level t-1 alive
    cont = np.ones(1, bool)       # whether the concession continues into the next period
    for t in range(1, T + 1):
        ch = lv[t - 1]
        par = ch["par"]
        r = reach[par] * cont[par] * ch["trans"]
        ex_pv = ch["ex"] / (1 + k.r_f) ** t
        Eexcess_pv += (r * ex_pv).sum()
        hit = ch["hit"]
        # handover at t
        p_hand[t] = (r * hit).sum()
        ES += (r * hit * ch["S"]).sum()
        EA_end += (r * hit * ch["A"]).sum()
        P_exhaust += (r * hit * ((V > 0) & (ch["S"] >= V - 1e-9))).sum()
        alive = ~hit
        if t == T:
            p_exp = (r * alive).sum()
            ES += (r * alive * ch["S"]).sum()
            EA_end += (r * alive * ch["A"]).sum()
            P_exhaust += (r * alive * ((V > 0) & (ch["S"] >= V - 1e-9))).sum()
            break
        ab = abandon[t] & alive
        p_aband[t] = (r * ab).sum()
        ES += (r * ab * ch["S"]).sum()
        EA_end += (r * ab * ch["A"]).sum()
        P_exhaust += (r * ab * ((V > 0) & (ch["S"] >= V - 1e-9))).sum()
        reach = r
        cont = alive & ~abandon[t]

    periods = np.arange(T + 1)
    out = dict(
        V=V, U=U, surplus=U - typ.omega,
        p_target=p_hand.sum(), p_abandon=p_aband.sum(), p_expiry=p_exp,
        E_periods=(periods * p_hand).sum() + (periods * p_aband).sum() + T * p_exp,
        E_expenditure=ES, E_A_end=EA_end, p_cap_exhausted=P_exhaust,
        E_excess_to_owner_pv=Eexcess_pv,
    )
    if policy:
        leaves = np.arange(2 ** T)
        end = np.full(2 ** T, T, dtype=np.int16)
        kind = np.full(2 ** T, 2, dtype=np.int8)
        open_ = np.ones(2 ** T, bool)
        for t in range(1, T + 1):
            anc = leaves >> (T - t)                      # ancestor of each history at level t
            h = lv[t - 1]["hit"][anc] & open_
            end[h] = t; kind[h] = 0; open_ &= ~h
            if t < T:
                a = abandon[t][anc] & open_
                end[a] = t; kind[a] = 1; open_ &= ~a
        out["leaf_end"] = end
        out["leaf_kind"] = kind
    return out


def leaf_probabilities(k: Contract, env: Environment):
    """Probability of each of the 2**Tbar state histories, indexed as in solve(policy=True)."""
    P = np.array(env.P, dtype=float)
    p = np.ones(1); zpar = np.array([env.z0])
    for t in range(1, k.Tbar + 1):
        n = 2 ** t
        par = np.arange(n) // 2
        z = np.arange(n) % 2
        p = p[par] * P[zpar[par], z]
        zpar = z
    return p


def V_max(k: Contract, env: Environment):
    """Largest discounted support any path can draw (above it U is flat in V)."""
    gmax = min(k.sbar, k.kappa * max(0.0, k.Rstar - min(env.R)))
    return sum(gmax / (1 + k.r_f) ** t for t in range(1, k.Tbar + 1))


def reference_payoff(typ: SponsorType, k: Contract, env: Environment):
    """Payoff on the path with normal payment in every period, under the best exit date.

    With R_N >= R*, no support is paid on this path, so the value does not depend on V.
    """
    best = payoff_on_path([0] * k.Tbar, 0.0, typ, k, env)
    for a in range(1, k.Tbar):
        best = max(best, payoff_on_path([0] * k.Tbar, 0.0, typ, k, env, abandon_after=a))
    return -env.I + best


def participation_threshold(typ, k, env, grid_n=41, tol=1e-6):
    """Grid diagnostic, then bisection for V* on [0, min(Vbar, V_max)].

    Returns dict with the grid, a monotonicity flag, and V* (None if P is empty).
    Bisection runs only if the grid shows no violation of weak monotonicity.
    """
    hi = min(k.Vbar, V_max(k, env))
    grid = np.linspace(0.0, hi, grid_n)
    Us = np.array([solve(v, typ, k, env)["U"] for v in grid])
    viol = np.where(np.diff(Us) < -1e-9)[0]
    res = dict(grid=grid, U=Us, monotone_on_grid=len(viol) == 0, violations=viol.tolist())
    if len(viol) > 0:
        res["Vstar"] = None
        res["status"] = "ordering violated on grid: investigate before any threshold search"
        return res
    if Us[-1] < typ.omega:
        res["Vstar"] = None
        res["status"] = "participation set empty"
        return res
    if Us[0] >= typ.omega:
        res["Vstar"] = 0.0
        res["status"] = "participates without support"
        return res
    lo_, hi_ = 0.0, hi
    while hi_ - lo_ > tol:
        mid = 0.5 * (lo_ + hi_)
        if solve(mid, typ, k, env)["U"] >= typ.omega:
            hi_ = mid
        else:
            lo_ = mid
    res["Vstar"] = hi_
    res["status"] = "threshold found"
    return res
