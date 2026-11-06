"""C4, matched access: sequential posted offers to n sponsors against the auction with n bidders.

Sequential offers: the development finance institution offers Vbar to up to n sponsors drawn
independently from the type distribution, one after another, and awards the contract to the first
sponsor that accepts (V* <= Vbar). With abstention probability a, an award occurs with probability
1 - a^n, the auction's award probability; the type of the first sponsor to accept has the
distribution of a single sponsor conditional on acceptance, so outcomes conditional on award equal
those of the single posted offer. Per-opportunity measures are therefore (1 - a^n) times the
single posted offer's measures conditional on award. No solver call is needed: the script works
from results_c4/c4_comparison.csv, and it cross-checks the sequential rows by direct enumeration
(first acceptor among n draws) from the saved type stage results_c3/c3_type_stage.json.

Per opportunity, the difference between the auction and the single posted offer divides into
    auction - single = (sequential - single)  [access to n sponsors]
                     + (auction - sequential)  [the auction's selection and cap-setting rules].
The split is an accounting identity.
"""
import csv, hashlib, itertools, json, os, sys, datetime, platform

TYPES = [(c, rho) for c in (24.0, 25.0, 26.0) for rho in (0.10, 0.12, 0.15, 0.20)]
VBAR = 25.0
MEASURES = ("cap", "ES", "surplus", "tgt", "ext", "exp", "per")
SRC = dict(ES="E_expenditure", surplus="U", tgt="p_target", ext="p_abandon", exp="p_expiry",
           per="E_periods")


def read_rows(path="results_c4/c4_comparison.csv"):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        for k, v in r.items():
            if k not in ("shock",):
                r[k] = float(v) if v not in ("", "None") else None
        r["n"] = int(r["n"])
    return rows


def sequential_rows(rows):
    """Sequential-offer rows from the single posted offer (n = 1) rows, for n = 2, 3."""
    single = {(r["shock"], r["W"], r["L"]): r for r in rows if r["n"] == 1}
    out = []
    for r in rows:
        if r["n"] == 1:
            continue
        s = single[(r["shock"], r["W"], r["L"])]
        a = 1.0 - s["p_award"]
        pa = 1.0 - a ** r["n"]
        q = dict(shock=r["shock"], W=r["W"], L=r["L"], n=r["n"], procedure="sequential", p_award=pa)
        for key in MEASURES:
            q[f"{key}_given_award"] = s[f"{key}_given_award"]
            q[f"{key}_per_opportunity"] = pa * s[f"{key}_given_award"]
        out.append(q)
    return out


def enumerate_sequential(ts, n):
    """Direct enumeration: first sponsor (in draw order) with V* <= Vbar receives Vbar."""
    vstar = {int(k): v for k, v in ts["vstar"].items()}
    m = len(TYPES)
    p = (1.0 / m) ** n
    acc = {k: 0.0 for k in MEASURES}
    pa = 0.0
    for prof in itertools.product(range(m), repeat=n):
        first = next((j for j in prof if vstar[j] is not None and vstar[j] <= VBAR), None)
        if first is None:
            continue
        pa += p
        o = ts["table"][f"{first}|{VBAR}"]
        for key in MEASURES:
            acc[key] += p * (VBAR if key == "cap" else o[SRC[key]])
    return pa, acc


def access_rules_rows(rows, seq):
    """Per-opportunity split of auction minus single offer into access and rules terms."""
    single = {(r["shock"], r["W"], r["L"]): r for r in rows if r["n"] == 1}
    auction = {(r["shock"], r["W"], r["L"], r["n"]): r for r in rows if r["n"] > 1}
    out = []
    for q in seq:
        s = single[(q["shock"], q["W"], q["L"])]
        a = auction[(q["shock"], q["W"], q["L"], q["n"])]
        for key in MEASURES:
            k = f"{key}_per_opportunity"
            out.append(dict(shock=q["shock"], W=q["W"], L=q["L"], n=q["n"], measure=key,
                            single=s[k], sequential=q[k], auction=a[k],
                            total=a[k] - s[k], access=q[k] - s[k], rules=a[k] - q[k]))
    return out


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
    rows = read_rows()
    seq = sequential_rows(rows)
    # award probability equals the auction's
    auction = {(r["shock"], r["W"], r["L"], r["n"]): r for r in rows if r["n"] > 1}
    dev_award = max(abs(q["p_award"] - auction[(q["shock"], q["W"], q["L"], q["n"])]["p_award"]) for q in seq)
    # direct enumeration from the saved type stage
    stages = {(t["shock"], t["W"], t["L"]): t for t in json.load(open("results_c3/c3_type_stage.json"))}
    dev_enum = 0.0
    for q in seq:
        pa, acc = enumerate_sequential(stages[(q["shock"], q["W"], q["L"])], q["n"])
        dev_enum = max(dev_enum, abs(pa - q["p_award"]))
        for key in MEASURES:
            dev_enum = max(dev_enum, abs(acc[key] - q[f"{key}_per_opportunity"]))
    print(f"sequential vs auction award probability: {dev_award:.2e}; formula vs enumeration: {dev_enum:.2e}")
    assert dev_award < 1e-12 and dev_enum < 1e-12
    split = access_rules_rows(rows, seq)
    for d in split:
        assert abs(d["total"] - d["access"] - d["rules"]) < 1e-12
    write_csv("results_c4/c4_sequential.csv", seq)
    write_csv("results_c4/c4_access_rules.csv", split)
    manifest = dict(
        run_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        python=sys.version.split()[0], platform=platform.platform(),
        code_sha256_16={"c4_sequential.py": sha("c4_sequential.py")},
        inputs_sha256_16={f: sha(f) for f in ("results_c4/c4_comparison.csv", "results_c3/c3_type_stage.json")},
        checks=dict(max_abs_deviation_award_vs_auction=dev_award,
                    max_abs_deviation_formula_vs_enumeration=dev_enum,
                    access_rules_identity="holds to 1e-12 for every row"),
        definition="sequential offers of Vbar to up to n independently drawn sponsors; award to the first that accepts",
        random_numbers="none",
        outputs={f: sha(f"results_c4/{f}") for f in ("c4_sequential.csv", "c4_access_rules.csv")},
    )
    json.dump(manifest, open("results_c4/manifest_sequential.json", "w"), indent=2, default=str)
    print("done", len(seq), len(split))
