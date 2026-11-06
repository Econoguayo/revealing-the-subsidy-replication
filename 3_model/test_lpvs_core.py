"""Tests for lpvs_core: ledger, terminal settlement, cap, stopping outcomes, exact tree, ordering."""
import itertools
import numpy as np
import pytest

from lpvs_core import (Contract, Environment, SponsorType, period_step, ledger_path,
                       payoff_on_path, solve, V_max, reference_payoff, leaf_probabilities)

K_EX = Contract(W=1e6, Rstar=26.0, kappa=0.8, sbar=25.0, r_c=0.08, r_f=0.05, Tbar=20)
ENV_EX = Environment(R=(30.0, 20.0))
T26 = SponsorType(c=26.0, rho=0.15)


# ---------------------------------------------------------------- ledger: worked example
def test_worked_example_partial_arrears():
    path = [0] * 6 + [1] * 3 + [0] * 3
    rows = ledger_path(path, 35.0, T26, K_EX, ENV_EX)
    for r in rows[6:9]:
        assert r["s"] == pytest.approx(4.8)
        assert r["x"] == pytest.approx(-1.2)
    for r in rows[:6] + rows[9:]:
        assert r["s"] == 0.0 and r["x"] == pytest.approx(4.0)
    assert rows[8]["S"] == pytest.approx(9.754, abs=5e-4)


def test_full_nonpayment_exhausts_cap_without_revolving():
    env = Environment(R=(30.0, 0.0))
    path = [0] * 6 + [1] * 4 + [0] * 2
    rows = ledger_path(path, 35.0, T26, K_EX, env)
    S7 = 20.8 / 1.05 ** 7
    S8 = S7 + 20.8 / 1.05 ** 8
    assert rows[6]["s"] == pytest.approx(20.8)
    assert rows[7]["s"] == pytest.approx(20.8)
    assert rows[8]["s"] == pytest.approx((35.0 - S8) * 1.05 ** 9)   # remaining cap paid in year 9
    assert rows[8]["S"] == pytest.approx(35.0)
    assert rows[9]["s"] == 0.0                                      # exhausted: no payment in year 10
    assert max(r["S"] for r in rows) <= 35.0 + 1e-9
    nonpay_pv = sum(20.8 / 1.05 ** t for t in (7, 8, 9))
    assert nonpay_pv == pytest.approx(42.27, abs=5e-3)


# ---------------------------------------------------------------- terminal settlement
def _hit_case(op_c, W):
    k = Contract(W=W, Rstar=26.0, kappa=0.8, sbar=25.0, r_c=0.08, r_f=0.05, Tbar=20)
    typ = SponsorType(c=op_c, rho=0.15)
    return k, typ


def test_settlement_reduces_support_first():
    # arrears revenue 20, cost 15: operating cash 5, raw support 4.8 (total 9.8)
    # choose W so that remaining compensation at t=1 is 7 (between 5 and 9.8)
    k, typ = _hit_case(15.0, 7.0 / 1.08)
    s, x, ex, A, S, hit = period_step(1, 20.0, 0.0, 0.0, 100.0, typ.c, k)
    assert hit and A == pytest.approx(k.W)
    assert x == pytest.approx(7.0)
    assert s == pytest.approx(2.0)          # support reduced from 4.8 to 2.0
    assert ex == 0.0
    assert S == pytest.approx(2.0 / 1.05)   # only actual disbursement counts against the cap


def test_settlement_excess_operating_cash_to_owner():
    k, typ = _hit_case(15.0, 3.0 / 1.08)    # remaining compensation 3 < operating cash 5
    s, x, ex, A, S, hit = period_step(1, 20.0, 0.0, 0.0, 100.0, typ.c, k)
    assert hit and s == 0.0 and S == 0.0
    assert x == pytest.approx(3.0)
    assert ex == pytest.approx(2.0)         # excess passes to the asset owner, not the sponsor
    assert A == pytest.approx(k.W)


def test_accumulation_never_exceeds_target():
    k = Contract(W=30.0, Rstar=26.0, kappa=0.8, sbar=25.0, r_c=0.08, r_f=0.05, Tbar=20)
    rng = np.random.default_rng(1)
    for _ in range(200):
        path = list(rng.integers(0, 2, 20))
        rows = ledger_path(path, 20.0, SponsorType(c=24.0, rho=0.15), k, ENV_EX)
        assert all(r["A"] <= k.W + 1e-9 for r in rows)
        if rows[-1]["hit"]:
            assert rows[-1]["A"] == pytest.approx(k.W)


# ---------------------------------------------------------------- exact tree against brute force
def _step_indep(t, R, A, S, V, c, k):
    """One period of the contract, written separately from lpvs_core.period_step."""
    want = min(k.sbar, k.kappa * max(0.0, k.Rstar - R))
    left = max(0.0, V - S) * (1 + k.r_f) ** t
    s = min(want, left)
    need = (k.W - A) * (1 + k.r_c) ** t          # retained cash that would reach W exactly
    op = R - c
    if op + s >= need:                            # target reached: support-first settlement
        s = 0.0 if op >= need else need - op
        return s, need, k.W, S + s / (1 + k.r_f) ** t, True
    return s, op + s, A + (op + s) / (1 + k.r_c) ** t, S + s / (1 + k.r_f) ** t, False


def _brute_force(V, typ, k, env):
    """Recursive optimal stopping over explicit histories, with its own ledger."""
    P = np.array(env.P); d = 1 / (1 + typ.rho)

    def rec(t, z_prev, A, S):
        val = 0.0; es = 0.0; po = np.zeros(3)
        for z in (0, 1):
            p = P[z_prev, z]
            s, x, A2, S2, hit = _step_indep(t, env.R[z], A, S, V, typ.c, k)
            if hit:
                v = x * d ** t + env.Lam * d ** t; e = S2; o = np.array([1, 0, 0])
            elif t == k.Tbar:
                v = x * d ** t + env.Lam * d ** t; e = S2; o = np.array([0, 0, 1])
            else:
                cv, ce, co = rec(t + 1, z, A2, S2)
                if env.L * d ** t > cv:
                    v = x * d ** t + env.L * d ** t; e = S2; o = np.array([0, 1, 0])
                else:
                    v = x * d ** t + cv; e = ce; o = co
            val += p * v; es += p * e; po += p * o
        return val, es, po

    v, es, po = rec(1, env.z0, 0.0, 0.0)
    return -env.I + v, es, po


@pytest.mark.parametrize("V", [0.0, 5.0, 12.0, 40.0])
@pytest.mark.parametrize("L", [0.0, -100.0])
def test_tree_matches_brute_force(V, L):
    k = Contract(W=22.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=8)
    env = Environment(R=(30.0, 20.0), P=((0.8, 0.2), (0.4, 0.6)), I=15.0, Lam=1.0, L=L)
    typ = SponsorType(c=25.0, rho=0.15)
    out = solve(V, typ, k, env)
    U_bf, ES_bf, po_bf = _brute_force(V, typ, k, env)
    assert out["U"] == pytest.approx(U_bf, abs=1e-10)
    assert out["E_expenditure"] == pytest.approx(ES_bf, abs=1e-10)
    assert [out["p_target"], out["p_abandon"], out["p_expiry"]] == pytest.approx(list(po_bf), abs=1e-12)


@pytest.mark.parametrize("V", [0.0, 2.0, 8.0])
def test_tree_matches_brute_force_with_exit(V):
    """A case in which exit occurs with positive probability (end-game exit, costless exit)."""
    k = Contract(W=20.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=10)
    env = Environment(R=(30.0, 20.0), P=((0.95, 0.05), (1/3, 2/3)), I=20.0, Lam=0.0, L=0.0)
    typ = SponsorType(c=25.0, rho=0.15)
    out = solve(V, typ, k, env)
    U_bf, ES_bf, po_bf = _brute_force(V, typ, k, env)
    if V == 0.0:
        assert out["p_abandon"] > 0.5
    assert out["U"] == pytest.approx(U_bf, abs=1e-10)
    assert out["E_expenditure"] == pytest.approx(ES_bf, abs=1e-10)
    assert [out["p_target"], out["p_abandon"], out["p_expiry"]] == pytest.approx(list(po_bf), abs=1e-12)


def test_outcome_probabilities_sum_to_one_and_expenditure_below_cap():
    k = Contract(W=35.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=14)
    env = Environment(R=(30.0, 20.0), I=25.0)
    for V in (0.0, 3.0, 10.0, 30.0):
        out = solve(V, SponsorType(c=25.0, rho=0.15), k, env)
        assert out["p_target"] + out["p_abandon"] + out["p_expiry"] == pytest.approx(1.0, abs=1e-12)
        assert out["E_expenditure"] <= V + 1e-9


def test_flat_above_V_max():
    k = Contract(W=35.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=12)
    env = Environment(R=(30.0, 20.0), I=25.0)
    typ = SponsorType(c=25.0, rho=0.15)
    vm = V_max(k, env)
    assert solve(vm, typ, k, env)["U"] == pytest.approx(solve(3 * vm, typ, k, env)["U"], abs=1e-12)


# ---------------------------------------------------------------- C1: pathwise dominance
@pytest.mark.parametrize("seed", range(5))
def test_pathwise_dominance_fixed_policy(seed):
    """For a fixed path and abandonment date, a higher cap never lowers the sponsor's payoff
    when rho > r_c and Lam >= max(L, 0)."""
    rng = np.random.default_rng(seed)
    for _ in range(300):
        r_c = rng.uniform(0.0, 0.12)
        rho = r_c + rng.uniform(0.005, 0.12)
        k = Contract(W=rng.uniform(10, 60), Rstar=26.0, kappa=rng.uniform(0.3, 0.95),
                     sbar=rng.uniform(2, 25), r_c=r_c, r_f=0.05, Tbar=15)
        Lam = rng.uniform(0, 10)
        env = Environment(R=(30.0, rng.uniform(0, 25)), I=20.0, Lam=Lam, L=rng.uniform(0, Lam))
        typ = SponsorType(c=rng.uniform(20, 29), rho=rho)
        path = list(rng.integers(0, 2, 15))
        a = None if rng.random() < 0.5 else int(rng.integers(1, 15))
        V1, V2 = sorted(rng.uniform(0, 80, 2))
        p1 = payoff_on_path(path, V1, typ, k, env, a)
        p2 = payoff_on_path(path, V2, typ, k, env, a)
        assert p2 >= p1 - 1e-9


def test_reference_bound():
    """No cap raises the payoff above the reference path payoff (R_N >= R*)."""
    k = Contract(W=35.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=12)
    env = Environment(R=(30.0, 20.0), I=25.0)
    typ = SponsorType(c=25.0, rho=0.15)
    Uref = reference_payoff(typ, k, env)
    for V in (0.0, 5.0, 20.0, 100.0):
        assert solve(V, typ, k, env)["U"] <= Uref + 1e-9


def test_negative_rates_break_ordering():
    """Remark (ii): with negative rates, a higher cap can bring handover forward and lower U."""
    k = Contract(W=1.5, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=-0.20, r_f=0.05, Tbar=2)
    env = Environment(R=(30.0, 20.0), P=((0.95, 0.05), (1/3, 2/3)), I=20.0, Lam=100.0, L=0.0)
    typ = SponsorType(c=19.0, rho=-0.10)
    u0 = solve(0.0, typ, k, env)["U"]
    u1 = solve(0.3, typ, k, env)["U"]
    assert u0 == pytest.approx(93.0605, abs=1e-3)
    assert u1 == pytest.approx(92.4444, abs=1e-3)
    assert u1 < u0


@pytest.mark.parametrize("seed", range(3))
def test_disbursement_monotone_in_cost_and_free_of_rho(seed):
    """C3 Proposition: with a common exogenous revenue path, the same cap and an exit date that does
    not cut the higher-cost concession short, disbursement is weakly higher for the higher-cost sponsor."""
    rng = np.random.default_rng(100 + seed)
    for _ in range(300):
        k = Contract(W=rng.uniform(10, 60), Rstar=26.0, kappa=rng.uniform(0.3, 1.0),
                     sbar=rng.uniform(2, 25), r_c=rng.uniform(0.0, 0.12), r_f=0.05, Tbar=15)
        env = Environment(R=(30.0, rng.uniform(0, 25)), I=20.0)
        cL, cH = sorted(rng.uniform(18, 29, 2))
        path = list(rng.integers(0, 2, 15))
        a = None if rng.random() < 0.5 else int(rng.integers(1, 15))
        V = rng.uniform(0, 60)
        SL = ledger_path(path, V, SponsorType(c=cL, rho=0.10), k, env, a)[-1]["S"]
        SH = ledger_path(path, V, SponsorType(c=cH, rho=0.10), k, env, a)[-1]["S"]
        assert SL <= SH + 1e-9


def test_expected_disbursement_free_of_rho_without_exit():
    """With exit ruled out, expected disbursement at a common cap is identical across discount rates
    and weakly increasing in operating cost (exact tree solution)."""
    k = Contract(W=30.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=10)
    env = Environment(R=(30.0, 20.0), P=((0.9, 0.1), (1/3, 2/3)), I=20.0, Lam=0.0, L=-1e6)
    for V in (3.0, 12.0, 25.0):
        e = {(c, rho): solve(V, SponsorType(c=c, rho=rho), k, env)["E_expenditure"]
             for c in (24.0, 26.0) for rho in (0.10, 0.20)}
        assert e[(24.0, 0.10)] == pytest.approx(e[(24.0, 0.20)], abs=1e-12)
        assert e[(26.0, 0.10)] == pytest.approx(e[(26.0, 0.20)], abs=1e-12)
        assert e[(24.0, 0.10)] <= e[(26.0, 0.10)] + 1e-12


@pytest.mark.parametrize("L", [0.0, -2.0])
def test_stopping_profile_matches_solver(L):
    """Per-history stopping dates (used for the exit-ordering check in C3) reproduce the solver's
    outcome probabilities and expected duration, and agree with the one-path ledger."""
    k = Contract(W=30.0, Rstar=26.0, kappa=0.8, sbar=10.0, r_c=0.08, r_f=0.05, Tbar=12)
    env = Environment(R=(30.0, 20.0), P=((0.90, 0.10), (1/3, 2/3)), I=20.0, L=L)
    p = leaf_probabilities(k, env)
    assert p.sum() == pytest.approx(1.0, abs=1e-12)
    rng = np.random.default_rng(7)
    max_exit = 0.0
    for typ in (SponsorType(c=24.0, rho=0.10), SponsorType(c=26.0, rho=0.20), SponsorType(c=27.0, rho=0.15)):
        for V in (0.0, 1.5, 25.0):
            o = solve(V, typ, k, env, policy=True)
            end, kind = o["leaf_end"], o["leaf_kind"]
            assert p[kind == 0].sum() == pytest.approx(o["p_target"], abs=1e-12)
            assert p[kind == 1].sum() == pytest.approx(o["p_abandon"], abs=1e-12)
            assert p[kind == 2].sum() == pytest.approx(o["p_expiry"], abs=1e-12)
            assert (p * end).sum() == pytest.approx(o["E_periods"], abs=1e-10)
            max_exit = max(max_exit, o["p_abandon"])
            for leaf in rng.integers(0, 2 ** k.Tbar, 60):
                states = [int(b) for b in format(int(leaf), f"0{k.Tbar}b")]
                ab = int(end[leaf]) if kind[leaf] == 1 else None
                rows = ledger_path(states, V, typ, k, env, abandon_after=ab)
                assert rows[-1]["t"] == end[leaf]
                assert rows[-1]["hit"] == (kind[leaf] == 0)
    assert max_exit > (0.05 if L == 0.0 else 0.0)
