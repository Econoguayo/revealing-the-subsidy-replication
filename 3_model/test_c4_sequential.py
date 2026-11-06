"""Tests of the sequential-offer comparator on the synthetic type stage of test_c4.py."""
import pytest

from c4_posted_offer import c4_stage, MEASURES
from c4_sequential import sequential_rows, enumerate_sequential, access_rules_rows
from test_c4 import synthetic_stage, VSTAR, M


def rows_for(ts):
    return [c4_stage(ts, n) for n in (1, 2, 3)]


def as_saved(ts):
    """The synthetic stage in the key format of results_c3/c3_type_stage.json."""
    return dict(vstar={str(j): v for j, v in ts["vstar"].items()},
                table={f"{j}|{v}": o for (j, v), o in ts["table"].items()})


@pytest.mark.parametrize("n", [2, 3])
def test_formula_matches_enumeration(n):
    ts = synthetic_stage()
    seq = {q["n"]: q for q in sequential_rows(rows_for(ts))}
    pa, acc = enumerate_sequential(as_saved(ts), n)
    assert seq[n]["p_award"] == pytest.approx(pa, abs=1e-12)
    for key in MEASURES:
        assert seq[n][f"{key}_per_opportunity"] == pytest.approx(acc[key], abs=1e-12)


def test_award_probability_matches_auction_and_conditional_matches_single():
    ts = synthetic_stage()
    rows = rows_for(ts)
    single = rows[0]
    for q in sequential_rows(rows):
        auction = next(r for r in rows if r["n"] == q["n"])
        assert q["p_award"] == pytest.approx(auction["p_award"], abs=1e-12)
        for key in MEASURES:
            assert q[f"{key}_given_award"] == pytest.approx(single[f"{key}_given_award"], abs=1e-12)


def test_access_term_formula_and_identity():
    ts = synthetic_stage()
    rows = rows_for(ts)
    a = sum(v is None for v in VSTAR) / M
    single = rows[0]
    for d in access_rules_rows(rows, sequential_rows(rows)):
        assert d["total"] == pytest.approx(d["access"] + d["rules"], abs=1e-12)
        expected_access = (a - a ** d["n"]) * single[f"{d['measure']}_given_award"]
        assert d["access"] == pytest.approx(expected_access, abs=1e-12)
