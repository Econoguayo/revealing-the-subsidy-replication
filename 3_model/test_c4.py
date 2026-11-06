"""Tests of the C4 enumeration on a synthetic type stage (no solver calls)."""
import itertools
import pytest

from c3_selection import TYPES, VBAR, auction_stage
from c4_posted_offer import c4_stage, decomposition_rows, MEASURES

M = len(TYPES)
# synthetic minimum caps: abstainers, zero bidders, a tie at 3.0, distinct positive caps
VSTAR = [None, 0.0, 0.0, 3.0, 3.0, 5.5, None, 0.0, 8.0, 12.0, None, 20.0]


def synthetic_stage():
    vstar = {j: VSTAR[j] for j in range(M)}
    cat = {j: ("abstain" if v is None else "zero" if v == 0.0 else "positive") for j, v in vstar.items()}
    caps = sorted({v for v in vstar.values() if v is not None} | {VBAR})
    table = {}
    for j in range(M):
        if vstar[j] is None:
            continue
        for v in caps:
            table[(j, v)] = dict(E_expenditure=0.1 * v * (1 + 0.05 * j), p_target=0.5 + 0.01 * v - 0.002 * j,
                                 p_abandon=0.1 - 0.002 * v, p_expiry=0.4 - 0.008 * v + 0.002 * j,
                                 E_periods=10 + 0.1 * j, U=0.2 * v - 0.3 * j + 2.0, p_cap_exhausted=0.0)
    # exit-ordering flags are needed only by c3_selection.auction_stage; their values do not matter here
    order = {(i, j, v): (True, 0.0) for i in range(M) for j in range(M) for v in caps}
    return dict(shock="syn", W=0.0, L=0.0, cat=cat, vstar=vstar, caps=caps, table=table, order=order)


def brute(ts, n):
    """Independent computation: explicit profiles, explicit winner lottery."""
    vstar, tab = ts["vstar"], ts["table"]
    tot = dict(p=0.0, cap=0.0, ES=0.0, tgt=0.0, surplus=0.0)
    for prof in itertools.product(range(M), repeat=n):
        pr = (1 / M) ** n
        bidders = [(vstar[j], j) for j in prof if vstar[j] is not None]
        if not bidders:
            continue
        bidders.sort()
        cap = bidders[1][0] if len(bidders) > 1 else VBAR
        lows = [j for b, j in bidders if b == bidders[0][0]]
        tot["p"] += pr
        for w in lows:
            q = pr / len(lows)
            tot["cap"] += q * cap
            tot["ES"] += q * tab[(w, cap)]["E_expenditure"]
            tot["tgt"] += q * tab[(w, cap)]["p_target"]
            tot["surplus"] += q * tab[(w, cap)]["U"]
    return tot


@pytest.mark.parametrize("n", [1, 2, 3])
def test_c4_matches_brute_force(n):
    ts = synthetic_stage()
    r = c4_stage(ts, n)
    b = brute(ts, n)
    assert r["p_award"] == pytest.approx(b["p"], abs=1e-12)
    for mine, theirs in (("cap", "cap"), ("ES", "ES"), ("tgt", "tgt"), ("surplus", "surplus")):
        assert r[f"{mine}_per_opportunity"] == pytest.approx(b[theirs], abs=1e-12)
        assert r[f"{mine}_given_award"] == pytest.approx(b[theirs] / b["p"], abs=1e-12)


def test_posted_offer_is_single_bidder_rule():
    ts = synthetic_stage()
    r = c4_stage(ts, 1)
    acceptors = [j for j in range(M) if VSTAR[j] is not None]
    assert r["p_award"] == pytest.approx(len(acceptors) / M)
    assert r["cap_given_award"] == pytest.approx(VBAR)
    assert r["p_single_given_award"] == pytest.approx(1.0)
    es = sum(ts["table"][(j, VBAR)]["E_expenditure"] for j in acceptors) / len(acceptors)
    assert r["ES_given_award"] == pytest.approx(es)
    # the posted offer evaluates the recipient at Vbar, so the at-Vbar and at-cap measures coincide
    for key in MEASURES:
        assert r[f"{key}_vbar_given_award"] == pytest.approx(r[f"{key}_given_award"])


def test_award_probability_formula():
    ts = synthetic_stage()
    a = sum(v is None for v in VSTAR) / M
    for n in (1, 2, 3):
        assert c4_stage(ts, n)["p_award"] == pytest.approx(1 - a ** n)


@pytest.mark.parametrize("n", [1, 2, 3])
def test_agrees_with_c3_auction_stage(n):
    ts = synthetic_stage()
    r, a = c4_stage(ts, n), auction_stage(ts, n)
    for mine, theirs in (("p_award", "p_award"), ("cap_given_award", "cap_given_award"),
                         ("ES_given_award", "ES_cap_given_award"), ("ES_own_given_award", "ES_own_given_award"),
                         ("tgt_given_award", "tgt_cap_given_award"), ("ext_given_award", "ext_cap_given_award"),
                         ("exp_given_award", "exp_cap_given_award"), ("per_given_award", "per_cap_given_award"),
                         ("ES_per_opportunity", "ES_per_opportunity")):
        assert r[mine] == pytest.approx(a[theirs], abs=1e-12)


def test_decomposition_identity():
    ts = synthetic_stage()
    p = c4_stage(ts, 1)
    for n in (2, 3):
        for d in decomposition_rows(p, c4_stage(ts, n)):
            assert d["difference"] == pytest.approx(d["selection_at_vbar"] + d["cap_term"], abs=1e-12)
            if d["measure"] == "cap":
                assert d["selection_at_vbar"] == pytest.approx(0.0, abs=1e-12)
