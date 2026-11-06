"""C4: the second-price auction against a posted offer under the same contract and maximum cap.

Posted offer (outline, C4): one sponsor, drawn from the same type distribution as the auction
bidders, is offered the maximum admissible cap Vbar under the same contract. It accepts if its
minimum acceptable cap V* does not exceed Vbar and then receives Vbar. This is the C2 award rule
applied to a single bidder, so the posted offer is computed by the same enumeration with n = 1.
Auctions have n = 2 or n = 3 bidders, as in C3. Every type is kept: sponsors that need no
support, sponsors with a positive minimum cap, and sponsors that abstain.

Measures, per procurement opportunity (zero when there is no award) and conditional on award:
award probability; committed exposure (the awarded cap); expected expenditure E[S] under the
awarded cap (and, as a reference, under the winner's own V*); sponsor surplus U - omega at the
awarded cap; the probabilities that the concession ends at the compensation target, by exit and at
the duration ceiling; expected operating periods.

Accounting decomposition, conditional on award, of the difference between the posted offer and an
auction in each measure m:
    m_posted - m_auction = [E_posted m_i(Vbar) - E_auction m_w(Vbar)]      (selection, at Vbar)
                         + [E_auction m_w(Vbar) - E_auction m_w(cap)]       (cap)
The posted offer always awards Vbar, so the first bracket compares who receives the contract at a
common cap and the second compares caps for the auction winner. The split is an identity; it
attributes nothing causally.

Diagnostic: for each type, whether E[S], the target probability, the exit probability and U are
monotone across the caps the auction can award (C1 establishes monotonicity of U only).

The type stage is recomputed with c3_selection.type_stage and checked against the saved C3 type
stage; the n = 2 and n = 3 rows are checked against results_c3/c3_auction.csv. No random numbers.
"""
import csv, hashlib, itertools, json, os, sys, datetime, platform
from multiprocessing import Pool
import numpy as np

from c3_selection import type_stage, auction_stage, TYPES, SHOCKS, WS, LS, VBAR, BASE, I, R_C

NS_C4 = (1, 2, 3)          # n = 1 is the posted offer of Vbar to one sponsor
OMEGA = 0.0                # outside option of every type (as in C1 and C3)
MEASURES = ("cap", "ES", "surplus", "tgt", "ext", "exp", "per")
SRC = dict(ES="E_expenditure", surplus="U", tgt="p_target", ext="p_abandon", exp="p_expiry",
           per="E_periods")


def m_at(tab, j, v, key):
    """Measure `key` for type j at cap v (cap itself for key 'cap')."""
    if key == "cap":
        return v
    val = tab[(j, v)][SRC[key]]
    return val - OMEGA if key == "surplus" else val


def c4_stage(ts, n):
    """Exact expectations over all n-profiles under the C2 award rule (n = 1: posted offer)."""
    vstar, cat, tab = ts["vstar"], ts["cat"], ts["table"]
    m = len(TYPES)
    p_prof = (1.0 / m) ** n
    acc = {"p_award": 0.0, "p_single": 0.0, "p_cap_zero": 0.0, "win_zero": 0.0, "win_pos": 0.0,
           "ES_own": 0.0}
    for key in MEASURES:
        acc[key] = 0.0            # at the awarded cap
        acc[key + "_vbar"] = 0.0  # winner evaluated at Vbar
    for prof in itertools.product(range(m), repeat=n):
        Q = [j for j in prof if vstar[j] is not None]
        if not Q:
            continue
        bids = sorted(vstar[j] for j in Q)
        cap = bids[1] if len(Q) >= 2 else VBAR
        winners = [j for j in Q if vstar[j] == bids[0]]
        w_p = p_prof / len(winners)
        acc["p_award"] += p_prof
        acc["p_single"] += p_prof * (len(Q) == 1)
        acc["p_cap_zero"] += p_prof * (cap == 0.0)
        for w in winners:
            acc["win_zero"] += w_p * (cat[w] == "zero")
            acc["win_pos"] += w_p * (cat[w] == "positive")
            acc["ES_own"] += w_p * tab[(w, vstar[w])]["E_expenditure"]
            for key in MEASURES:
                acc[key] += w_p * m_at(tab, w, cap, key)
                acc[key + "_vbar"] += w_p * m_at(tab, w, VBAR, key)
    pa = acc["p_award"]
    out = dict(shock=ts["shock"], W=ts["W"], L=ts["L"], n=n, p_award=pa)
    for key in MEASURES:
        out[f"{key}_per_opportunity"] = acc[key]
    for key in MEASURES + ("ES_own", "p_single", "p_cap_zero", "win_zero", "win_pos"):
        out[f"{key}_given_award"] = acc[key] / pa if pa > 0 else None
    for key in MEASURES:
        out[f"{key}_vbar_given_award"] = acc[key + "_vbar"] / pa if pa > 0 else None
    return out


def decomposition_rows(posted, auction):
    """Selection and cap terms of posted minus auction, conditional on award, for each measure."""
    rows = []
    for key in MEASURES:
        mp = posted[f"{key}_given_award"]
        ma = auction[f"{key}_given_award"]
        mav = auction[f"{key}_vbar_given_award"]
        rows.append(dict(shock=auction["shock"], W=auction["W"], L=auction["L"], n=auction["n"],
                         measure=key, posted=mp, auction=ma, difference=mp - ma,
                         selection_at_vbar=mp - mav, cap_term=mav - ma))
    return rows


def cap_monotonicity_rows(ts):
    """For each participating type: monotonicity of outcomes across the caps the auction can award."""
    rows = []
    caps = sorted(ts["caps"])
    for j, (c, rho) in enumerate(TYPES):
        if ts["vstar"][j] is None:
            continue
        cs = [v for v in caps if v >= ts["vstar"][j]]   # caps the type would accept
        seq = {k: np.array([ts["table"][(j, v)][k] for v in cs])
               for k in ("E_expenditure", "p_target", "p_abandon", "p_expiry", "U")}
        d = {k: np.diff(s) for k, s in seq.items()}
        rows.append(dict(shock=ts["shock"], W=ts["W"], L=ts["L"], c=c, rho=rho, n_caps=len(cs),
                         ES_nondecreasing=bool((d["E_expenditure"] >= -1e-12).all()),
                         target_nondecreasing=bool((d["p_target"] >= -1e-12).all()),
                         exit_nonincreasing=bool((d["p_abandon"] <= 1e-12).all()),
                         expiry_nonincreasing=bool((d["p_expiry"] <= 1e-12).all()),
                         U_nondecreasing=bool((d["U"] >= -1e-12).all()),
                         max_fall_ES=float(max(0.0, -d["E_expenditure"].min(initial=0.0))),
                         max_fall_target=float(max(0.0, -d["p_target"].min(initial=0.0))),
                         max_rise_exit=float(max(0.0, d["p_abandon"].max(initial=0.0))),
                         max_rise_expiry=float(max(0.0, d["p_expiry"].max(initial=0.0))),
                         ES_vbar_minus_own=float(seq["E_expenditure"][-1] - seq["E_expenditure"][0]),
                         target_vbar_minus_own=float(seq["p_target"][-1] - seq["p_target"][0]),
                         exit_vbar_minus_own=float(seq["p_abandon"][-1] - seq["p_abandon"][0])))
    return rows


def load_saved_stage(path):
    st = json.load(open(path))
    out = {}
    for ts in st:
        tab = {(int(k.split("|")[0]), float(k.split("|")[1])): v for k, v in ts["table"].items()}
        out[(ts["shock"], ts["W"], ts["L"])] = dict(
            vstar={int(k): v for k, v in ts["vstar"].items()},
            cat={int(k): v for k, v in ts["cat"].items()}, table=tab)
    return out


def check_against_c3(stages, rows):
    """Recomputed type stage equals the saved one; n = 2, 3 rows equal results_c3/c3_auction.csv;
    the n = 1 rows equal c3_selection.auction_stage with a single bidder."""
    saved = load_saved_stage("results_c3/c3_type_stage.json")
    max_dev = 0.0
    for ts in stages:
        sv = saved[(ts["shock"], ts["W"], ts["L"])]
        assert sv["vstar"] == ts["vstar"] and sv["cat"] == ts["cat"]
        assert set(sv["table"]) == set(ts["table"])
        for key, o in ts["table"].items():
            for k2, val in o.items():
                max_dev = max(max_dev, abs(val - sv["table"][key][k2]))
    c3 = {(r["shock"], float(r["W"]), float(r["L"]), int(r["n"])): r
          for r in csv.DictReader(open("results_c3/c3_auction.csv"))}
    pairs = dict(p_award="p_award", cap_given_award="cap_given_award",
                 ES_given_award="ES_cap_given_award", ES_own_given_award="ES_own_given_award",
                 tgt_given_award="tgt_cap_given_award", ext_given_award="ext_cap_given_award",
                 exp_given_award="exp_cap_given_award", per_given_award="per_cap_given_award",
                 p_single_given_award="p_single_given_award", ES_per_opportunity="ES_per_opportunity")
    max_c3 = 0.0
    for r in rows:
        if r["n"] == 1:
            ts = next(t for t in stages if (t["shock"], t["W"], t["L"]) == (r["shock"], r["W"], r["L"]))
            a1 = auction_stage(ts, 1)
            for mine, theirs in pairs.items():
                max_c3 = max(max_c3, abs(r[mine] - a1[theirs]))
            continue
        ref = c3[(r["shock"], r["W"], r["L"], r["n"])]
        for mine, theirs in pairs.items():
            max_c3 = max(max_c3, abs(r[mine] - float(ref[theirs])))
    return max_dev, max_c3


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
    out_dir = "results_c4"
    os.makedirs(out_dir, exist_ok=True)
    jobs = [(s, W, L) for L in LS for s in SHOCKS for W in WS]
    with Pool(2) as pool:
        stages = pool.map(type_stage, jobs)
    rows, drows, mrows = [], [], []
    for ts in stages:
        by_n = {n: c4_stage(ts, n) for n in NS_C4}
        rows += [by_n[n] for n in NS_C4]
        for n in NS_C4[1:]:
            drows += decomposition_rows(by_n[1], by_n[n])
        mrows += cap_monotonicity_rows(ts)
    max_dev, max_c3 = check_against_c3(stages, rows)
    print(f"type stage vs saved C3: max abs deviation {max_dev:.3e}; C4 vs C3 auction rows: {max_c3:.3e}")
    assert max_dev == 0.0 and max_c3 < 1e-12
    for d in drows:
        assert abs(d["difference"] - d["selection_at_vbar"] - d["cap_term"]) < 1e-12
    write_csv(f"{out_dir}/c4_comparison.csv", rows)
    write_csv(f"{out_dir}/c4_decomposition.csv", drows)
    write_csv(f"{out_dir}/c4_cap_monotonicity.csv", mrows)
    manifest = dict(
        run_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        python=sys.version.split()[0], numpy=np.__version__, platform=platform.platform(),
        code_sha256_16={f: sha(f) for f in ("lpvs_core.py", "c3_selection.py", "c4_posted_offer.py")},
        inputs_sha256_16={"results_c3/c3_type_stage.json": sha("results_c3/c3_type_stage.json"),
                          "results_c3/c3_auction.csv": sha("results_c3/c3_auction.csv")},
        checks=dict(type_stage_max_abs_deviation_vs_saved=max_dev,
                    max_abs_deviation_vs_c3_auction=max_c3,
                    decomposition_identity="holds to 1e-12 for every row"),
        assumptions=dict(BASE=BASE, I=I, VBAR=VBAR, R_C=R_C, TYPES=TYPES, SHOCKS=SHOCKS, WS=WS, LS=LS,
                         NS=NS_C4, omega=OMEGA, Lam=0.0, type_prior="uniform, independent draws",
                         posted_offer="Vbar offered to one sponsor drawn from the type distribution; "
                                      "accepted if V* <= Vbar (C2 rule with n = 1)",
                         bidding="each sponsor bids its minimum acceptable cap (threshold bid); weakly dominant under the C2 second-price rule given assumption A6 (payoff at a positive threshold equals the outside option), which holds in the baseline with L = Lam = 0 (working paper, Remark 1); for L = -2 the results describe allocations under threshold bids, without an equilibrium claim"),
        random_numbers="none (exact enumeration and exact tree computation)",
        outputs={f: sha(f"{out_dir}/{f}") for f in sorted(os.listdir(out_dir)) if f.endswith(".csv")},
    )
    json.dump(manifest, open(f"{out_dir}/manifest.json", "w"), indent=2, default=str)
    print("done", len(rows), len(drows), len(mrows))
