"""Recompute the Scaling Solar figures stated in Section 2 and in the note to Table 2 from the table's
entries (2_scaling_solar/table2_scaling_solar.csv). The entries themselves are a compilation from the
sources cited in the table note; this script checks only the arithmetic that the text derives from them.

Usage: python check_scaling_solar.py TABLE2_CSV OUT_CSV
"""
import csv, sys
from decimal import Decimal, ROUND_HALF_UP

T = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
row = {(r["country"], r["entry"]): r for r in T}
pct = lambda a, b: str((Decimal(100 * a) / Decimal(b)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
out = []


def chk(cid, where, claim, computed, expected):
    out.append(dict(id=cid, location=where, claim=claim, computed=str(computed),
                    verdict="match" if str(computed) == str(expected) else "differs"))


z, s = row[("Zambia", "Round 1")], row[("Senegal", "Round 1")]
chk("S1", "Sec. 2", "Zambia Round 1: seven final proposals from eleven prequalified firms", f"{z['final_bidders']} of {z['prequalified']}", "7 of 11")
chk("S2", "Sec. 2", "Senegal: proposals from eight of thirteen firms", f"{s['final_bidders']} of {s['prequalified']}", "8 of 13")
fb, pq = int(z["final_bidders"]) + int(s["final_bidders"]), int(z["prequalified"]) + int(s["prequalified"])
chk("S3", "Sec. 2; Table 2 note", "the two tenders: 15 of 24 prequalified bidder opportunities, or 62.5 percent", f"{fb} of {pq}, {pct(fb, pq)}", "15 of 24, 62.5")
chk("S4", "Sec. 2 footnote", "tender-level conversion 63.6 percent in Zambia Round 1 and 61.5 percent in Senegal",
    f"{pct(int(z['final_bidders']), int(z['prequalified']))} and {pct(int(s['final_bidders']), int(s['prequalified']))}", "63.6 and 61.5")
fin = [int(r["final_bidders"]) for r in T if r["final_bidders"] != "n.r."]
chk("S5", "Sec. 2", "final bidders reported for five opportunities, 5 to 8 per opportunity", f"{len(fin)} entries, {min(fin)} to {max(fin)}", "5 entries, 5 to 8")
chk("S6", "Table 2 note", "eight recovered procurement entries", len(T), 8)
with open(sys.argv[2], "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "location", "claim", "computed", "verdict"])
    w.writeheader()
    w.writerows(out)
for o in out:
    print(o["id"], o["verdict"], o["computed"])
