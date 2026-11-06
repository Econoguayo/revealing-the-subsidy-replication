"""Arithmetic of the worked example (Section 4) and of the counterexample with recovery (Appendix A).

Usage: python check_worked_examples.py OUT_CSV

Both examples are deterministic and use the values stated in the text; the computation uses exact
fractions. The ledger of the Section 4 example is also checked against the contract implementation by
3_model/test_lpvs_core.py (support of 4.8 a year in years seven to nine; 9.754 discounted).
"""
import csv, sys
from fractions import Fraction as F

out = []


def chk(cid, where, claim, computed, verdict):
    out.append(dict(id=cid, location=where, claim=claim, computed=computed, verdict="match" if verdict else "differs"))


# ---------------- Section 4 ----------------
d = F(1) / F(105, 100)                        # DFI discount factor at 5 percent
pv3 = d ** 7 + d ** 8 + d ** 9                # years seven to nine
s = F(8, 10) * (26 - 20)
chk("W1", "Sec. 4", "support 0.8 x (26 - 20) = 4.8 a year", f"{float(s):.1f}", s == F(48, 10))
chk("W2", "Sec. 4", "three years of support cost about 9.8 in present value at 5 percent", f"{float(s * pv3):.3f}", round(float(s * pv3), 1) == 9.8)
full = F(8, 10) * 26
chk("W3", "Sec. 4", "complete nonpayment: 20.8 a year, about 42.3 in present value, exhausting the cap of 42",
    f"{float(full):.1f} a year; {float(full * pv3):.3f}", full == F(208, 10) and round(float(full * pv3), 1) == 42.3 and full * pv3 > 42)

# ---------------- Appendix A, counterexample with recovery ----------------
dl = F(1) / F(105, 100)                       # sponsor discount factor, rho = 0.05
# U(V) - U(V') = a - b L, with
#   U(V)  = 30 dl^2 + 20.8 dl^3 + 30 dl^4 + L dl^3   (lower cap V = 0: completion in period 3, arrears collected in period 4)
#   U(V') = 20.8 dl + 30 dl^2 + 9.2 dl^4 + L dl^2    (higher cap: completion in period 2, DFI recovers 20.8 in period 4)
a = 30 * dl ** 2 + F(208, 10) * dl ** 3 + 30 * dl ** 4 - (F(208, 10) * dl + 30 * dl ** 2 + F(92, 10) * dl ** 4)
b = dl ** 2 - dl ** 3
chk("A1", "App. A", "U(V) - U(V') = 15.27 - 0.0432 L", f"{float(a):.5f} - {float(b):.8f} L",
    round(float(a), 2) == 15.27 and round(float(b), 4) == 0.0432)
chk("A2", "App. A", "positive for any L below about 354", f"root {float(a / b):.2f}", round(float(a / b)) == 354)
# Exit yields L at the exit date, recovery entitlements unchanged. Largest L at which continuation weakly
# dominates exit, at each decision date (values discounted to that date):
lim = {
    "V, end of period 1": (30 * dl + F(208, 10) * dl ** 2 + 30 * dl ** 3 - 30 * dl ** 3) / (1 - dl ** 2),
    "V, end of period 2": (F(208, 10) * dl + 30 * dl ** 2 - 30 * dl ** 2) / (1 - dl),
    "V', end of period 1": (30 * dl + F(92, 10) * dl ** 3 - F(92, 10) * dl ** 3) / (1 - dl),
}
binding = min(lim, key=lim.get)
chk("A3", "App. A", "continuation dominates exit whenever L is below 416; binding comparison: continuation under V at the end of period 2",
    "; ".join(f"{k}: {float(v):.1f}" for k, v in lim.items()) + f"; binding: {binding}",
    binding == "V, end of period 2" and lim[binding] == 416)

with open(sys.argv[1], "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "location", "claim", "computed", "verdict"])
    w.writeheader()
    w.writerows(out)
for o in out:
    print(o["id"], o["verdict"], o["computed"])
