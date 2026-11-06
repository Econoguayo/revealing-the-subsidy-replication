"""LaTeX tables for the C4 note, from results_c4/.

Revision of November 4, 2026: award probabilities, and the exposures of offers at the fixed cap
Vbar, are printed from their exact formulas rather than from the floating-point results. With k of
the twelve types accepting Vbar in a design, an award occurs with probability 1 - (1 - k/12)^n for
the single offer (n = 1), sequential offers and the auction, and the exposure per opportunity of a
single or sequential offer is that probability times Vbar. The exact values are checked against the
results files to 1e-9 and rounded half up. Floating-point results lying just below a rounding half
(0.9374999999999977 for 15/16, 18.749999999999993 for 75/4) had been printed as 0.937 and 18.7.
"""
import csv
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP, getcontext
from fractions import Fraction

from c3_selection import TYPES, VBAR

D = "results_c4"
C = list(csv.DictReader(open(f"{D}/c4_comparison.csv")))
X = list(csv.DictReader(open(f"{D}/c4_decomposition.csv")))
MONO = list(csv.DictReader(open(f"{D}/c4_cap_monotonicity.csv")))
SEQ = list(csv.DictReader(open(f"{D}/c4_sequential.csv")))
AR = list(csv.DictReader(open(f"{D}/c4_access_rules.csv")))


def f(x, nd=2):
    if x in ("", "None", None):
        return "--"
    out = f"{float(x):.{nd}f}"
    return out[1:] if out.startswith("-") and float(out) == 0 else out   # no negative zero


getcontext().prec = 50
STAGE = {(t["shock"], str(float(t["W"])), str(float(t["L"]))): t
         for t in json.load(open("results_c3/c3_type_stage.json"))}


def n_accept(shock, W, L):
    """Number of types whose minimum acceptable cap does not exceed Vbar (they accept Vbar)."""
    cat = STAGE[(shock, str(float(W)), str(float(L)))]["cat"]
    return sum(c in ("zero", "positive") for c in cat.values())


def p_award_exact(shock, W, L, n):
    return 1 - (1 - Fraction(n_accept(shock, W, L), len(TYPES))) ** int(n)


def fx(exact, reported, nd):
    """Format an exact Fraction, rounded half up, after checking it against the reported result."""
    if abs(float(exact) - float(reported)) > 1e-9:
        raise ValueError(f"exact value {float(exact)} differs from reported {reported}")
    q = Decimal(1).scaleb(-nd)
    return str((Decimal(exact.numerator) / Decimal(exact.denominator)).quantize(q, rounding=ROUND_HALF_UP))


def sh(s):
    return "0.05" if s == "p05" else "0.10"


def offer(n):
    return "Single offer" if n == "1" else f"Auction, $n = {n}$"


def bids_note(L, first=False):
    """Bid qualification for the termination-penalty tables (no text for the baseline)."""
    if L == "0.0":
        return ""
    if first:
        return (" Bids are minimum acceptable caps. The sensitivity exercise reports allocations under threshold bids,"
                " without establishing an equilibrium.")
    return (r" Bids as in Table~\ref{tab:c4opppen}: allocations under threshold bids, without an established"
            " equilibrium.")


def lab(L):
    return "costless exit" if L == "0.0" else "termination penalty"


def resized(body, caption, label, notes):
    return "\n".join([r"\begin{table}[htbp]\centering\small", rf"\caption{{{caption}}}\label{{{label}}}",
                      r"\resizebox{\textwidth}{!}{" + body + "}",
                      r"\par\smallskip\begin{minipage}{\textwidth}\footnotesize\textit{Notes:} " + notes + r"\end{minipage}",
                      r"\end{table}"])


def tab_given_award(L="0.0"):
    o = [r"\begin{tabular}{cccccccccccc}\toprule",
         r" & & & & & Exposure & \multicolumn{2}{c}{Expenditure} & & \multicolumn{3}{c}{Operating outcomes}\\\cmidrule(lr){6-6}\cmidrule(lr){7-8}\cmidrule(l){10-12}",
         r"Arrears entry & $W$ & Offer & Award & One qualifier & Cap & $E[S]$ & $E[S]$ at own $V^*$ & Surplus & Target & Exit & Expiry\\\midrule"]
    prev = None
    for r in C:
        if r["L"] != L:
            continue
        if prev is not None and (r["shock"], r["W"]) != prev:
            o.append(r"\addlinespace")
        prev = (r["shock"], r["W"])
        o.append(" & ".join([sh(r["shock"]), f(r["W"], 0), offer(r["n"]),
                             fx(p_award_exact(r["shock"], r["W"], r["L"], r["n"]), r["p_award"], 3),
                             f(r["p_single_given_award"]), f(r["cap_given_award"], 1),
                             f(r["ES_given_award"]), f(r["ES_own_given_award"]), f(r["surplus_given_award"]),
                             f(r["tgt_given_award"]), f(r["ext_given_award"]), f(r["exp_given_award"])]) + r"\\")
    o.append(r"\bottomrule\end{tabular}")
    notes = (r"Single offer: one sponsor, drawn from the twelve types, is offered $\bar V = 25$ and accepts if its minimum acceptable cap does not exceed $\bar V$. "
             r"Auction: $n$ sponsors under the second-price award of C2 with the same $\bar V$. Award: probability of an award per procurement opportunity. "
             r"All other columns are conditional on award; sequential offers to $n$ sponsors have the outcomes of the posted offer conditional on award. Cap: expected awarded cap (committed exposure). One qualifier: probability that a single sponsor qualifies and receives $\bar V$. "
             r"$E[S]$: expected discounted disbursement under the awarded cap; at own $V^*$: under the recipient's own minimum cap, for reference. Surplus: sponsor surplus $U - \omega$ of the recipient at the awarded cap, with $\omega = 0$, in present value at the recipient's own discount rate. "
             r"Target, Exit and Expiry: probabilities that the concession ends by reaching $W$, by the sponsor's exit and at $\bar T$ before reaching $W$. "
             rf"Exact expectations over all $12^n$ profiles; {lab(L)}.{bids_note(L)} Source: \texttt{{c4\_posted\_offer.py}}.")
    return resized("\n".join(o), rf"Posted offers and auction: outcomes conditional on award ({lab(L)})",
                   "tab:c4award" + ("" if L == "0.0" else "pen"), notes)


def tab_per_opportunity(L="0.0"):
    o = [r"\begin{tabular}{cccccccccc}\toprule",
         r"Arrears entry & $W$ & Procedure & Award & Exposure & $E[S]$ & Surplus & Target & Exit & Expiry\\\midrule"]
    auc = {(r["shock"], r["W"], r["n"]): r for r in C if r["L"] == L}
    seq = {(r["shock"], r["W"], r["n"]): r for r in SEQ if r["L"] == L}
    designs = list(dict.fromkeys((r["shock"], r["W"]) for r in C if r["L"] == L))

    def line(r, label, fixed_cap):
        pa = p_award_exact(r["shock"], r["W"], r["L"], r["n"])
        expo = (fx(pa * Fraction(VBAR), r["cap_per_opportunity"], 1) if fixed_cap
                else f(r["cap_per_opportunity"], 1))
        return " & ".join([sh(r["shock"]), f(r["W"], 0), label, fx(pa, r["p_award"], 3), expo,
                           f(r["ES_per_opportunity"]), f(r["surplus_per_opportunity"]), f(r["tgt_per_opportunity"], 3),
                           f(r["ext_per_opportunity"], 3), f(r["exp_per_opportunity"], 3)]) + r"\\"
    for i, (s_, W) in enumerate(designs):
        if i:
            o.append(r"\addlinespace")
        o.append(line(auc[(s_, W, "1")], "Single offer", True))
        for n in ("2", "3"):
            o.append(line(seq[(s_, W, n)], f"Sequential, $n = {n}$", True))
            o.append(line(auc[(s_, W, n)], f"Auction, $n = {n}$", False))
    o.append(r"\bottomrule\end{tabular}")
    notes = (r"Per procurement opportunity: every measure counts zero when there is no award. Single offer: $\bar V = 25$ offered to one sponsor drawn from the twelve types. "
             r"Sequential: $\bar V$ offered to up to $n$ independently drawn sponsors in turn, with the award to the first that accepts; its award probability equals the auction's, and its outcomes conditional on award equal those of the single offer. "
             r"Auction: $n$ sponsors under the second-price award of C2 with the same $\bar V$. Exposure: expected awarded cap. "
             r"Surplus: expected sponsor surplus $U - \omega$ of the recipient at the awarded cap, with $\omega = 0$, in present value at the recipient's own discount rate. "
             r"Target, Exit and Expiry: probabilities that the opportunity ends in a concession that reaches $W$, ends by the sponsor's exit, or reaches $\bar T$ before $W$. "
             rf"{lab(L).capitalize()}.{bids_note(L, first=True)} Source: \texttt{{c4\_posted\_offer.py}}, \texttt{{c4\_sequential.py}}.")
    return resized("\n".join(o), rf"Single offer, sequential offers and auction: outcomes per procurement opportunity ({lab(L)})",
                   "tab:c4opp" + ("" if L == "0.0" else "pen"), notes)


def tab_access_rules(L="0.0"):
    dec = defaultdict(dict)
    for r in AR:
        if r["L"] == L:
            dec[(r["shock"], r["W"], r["n"])][r["measure"]] = r
    o = [r"\begin{tabular}{cccccccccccc}\toprule",
         r" & & & \multicolumn{3}{c}{$E[S]$} & \multicolumn{3}{c}{Target} & \multicolumn{3}{c}{Exit}\\\cmidrule(lr){4-6}\cmidrule(lr){7-9}\cmidrule(l){10-12}",
         r"Arrears entry & $W$ & $n$ & Total & Access & Rules & Total & Access & Rules & Total & Access & Rules\\\midrule"]
    for (s_, W, n), d in dec.items():
        cells = [sh(s_), f(W, 0), n]
        for m in ("ES", "tgt", "ext"):
            nd = 2 if m == "ES" else 3
            cells += [f(d[m]["total"], nd), f(d[m]["access"], nd), f(d[m]["rules"], nd)]
        o.append(" & ".join(cells) + r"\\")
    o.append(r"\bottomrule\end{tabular}")
    notes = (r"Per procurement opportunity. Total: auction with $n$ bidders minus the single offer. Access: sequential offers to $n$ sponsors minus the single offer. "
             r"Rules: auction minus sequential offers, which have the same award probability. The two terms sum to the total by construction. "
             rf"{lab(L).capitalize()}.{bids_note(L)} Source: \texttt{{c4\_sequential.py}}.")
    return resized("\n".join(o), rf"Auction minus single offer, per opportunity: access and rules terms ({lab(L)})",
                   "tab:c4ar" + ("" if L == "0.0" else "pen"), notes)


def tab_decomposition(L="0.0"):
    dec = defaultdict(dict)
    for r in X:
        if r["L"] == L:
            dec[(r["shock"], r["W"], r["n"])][r["measure"]] = r
    o = [r"\begin{tabular}{cccccccccccc}\toprule",
         r" & & & \multicolumn{3}{c}{$E[S]$} & \multicolumn{3}{c}{Target} & \multicolumn{3}{c}{Exit}\\\cmidrule(lr){4-6}\cmidrule(lr){7-9}\cmidrule(l){10-12}",
         r"Arrears entry & $W$ & $n$ & Difference & Selection & Cap & Difference & Selection & Cap & Difference & Selection & Cap\\\midrule"]
    for (s, W, n), d in dec.items():
        cells = [sh(s), f(W, 0), n]
        for m in ("ES", "tgt", "ext"):
            nd = 2 if m == "ES" else 3
            cells += [f(d[m]["difference"], nd), f(d[m]["selection_at_vbar"], nd), f(d[m]["cap_term"], nd)]
        o.append(" & ".join(cells) + r"\\")
    o.append(r"\bottomrule\end{tabular}")
    body = "\n".join(o)
    notes = (r"Conditional on award, where single and sequential offers have the same outcomes. Difference: posted offer minus auction with $n$ bidders. Selection: the recipient of the posted offer minus the auction winner, both evaluated at $\bar V$. "
             r"Cap: the auction winner at $\bar V$ minus the same winner at the awarded cap. The two terms sum to the difference by construction, and the split assigns no causal weight. "
             rf"{lab(L).capitalize()}.{bids_note(L)} Source: \texttt{{c4\_posted\_offer.py}}.")
    return resized(body, rf"Posted offers minus auction, conditional on award: selection and cap terms ({lab(L)})",
                   "tab:c4dec" + ("" if L == "0.0" else "pen"), notes)


def tab_monotonicity():
    g = defaultdict(lambda: defaultdict(float))
    for r in MONO:
        k = (r["L"], r["shock"], r["W"])
        g[k]["types"] += 1
        for col in ("ES_nondecreasing", "target_nondecreasing", "exit_nonincreasing", "expiry_nonincreasing"):
            g[k][col] += r[col] == "True"
        for col in ("max_fall_target", "max_rise_exit", "max_rise_expiry"):
            g[k][col] = max(g[k][col], float(r[col]))
    o = [r"\begin{tabular}{cccccccccc}\toprule",
         r" & & & & $E[S]$ & \multicolumn{2}{c}{Target} & \multicolumn{2}{c}{Exit} & Expiry\\\cmidrule(lr){6-7}\cmidrule(lr){8-9}",
         r"Exit rule & Arrears entry & $W$ & Types & Nondecreasing & Nondecreasing & Largest fall & Nonincreasing & Largest rise & Nonincreasing\\\midrule"]
    for (L, s, W), d in g.items():
        o.append(" & ".join(["costless" if L == "0.0" else "penalty", sh(s), f(W, 0), str(int(d["types"])),
                             str(int(d["ES_nondecreasing"])), str(int(d["target_nondecreasing"])), f(d["max_fall_target"], 3),
                             str(int(d["exit_nonincreasing"])), f(d["max_rise_exit"], 3),
                             str(int(d["expiry_nonincreasing"]))]) + r"\\")
    o.append(r"\bottomrule\end{tabular}")
    notes = (r"For each participating type, each outcome is evaluated at every cap that the auction can award in the design and that the type would accept, from its own minimum cap to $\bar V$. "
             r"Types: participating types. The count columns give the number of types for which the outcome is monotone across those caps in the stated direction (tolerance $10^{-12}$). "
             r"Largest fall and Largest rise: the largest decrease in the target probability, and the largest increase in the exit probability, between adjacent awardable caps for any type. "
             r"C1 establishes only that the payoff $U$ is weakly increasing in the cap; $U$ is nondecreasing for every type. Source: \texttt{c4\_posted\_offer.py}.")
    return resized("\n".join(o), r"Number of types with outcomes monotone across awardable caps, by design", "tab:c4mono", notes)


if __name__ == "__main__":
    main = [tab_per_opportunity(), tab_given_award(), tab_access_rules(), tab_decomposition()]
    appendix = [tab_per_opportunity("-2.0"), tab_given_award("-2.0"), tab_access_rules("-2.0"),
                tab_decomposition("-2.0"), tab_monotonicity()]
    open("c4_tables_main.tex", "w").write("\n\n".join(main))
    open("c4_tables_appendix.tex", "w").write("\n\n".join(appendix))
    print("ok")
