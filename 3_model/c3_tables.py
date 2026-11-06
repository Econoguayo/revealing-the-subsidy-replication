"""LaTeX tables for the C3 note, from results_c3/."""
import csv

D = "results_c3"
T = list(csv.DictReader(open(f"{D}/c3_types.csv")))
A = list(csv.DictReader(open(f"{D}/c3_auction.csv")))
S = list(csv.DictReader(open(f"{D}/c3_design_summary.csv")))


def f(x, nd=2):
    return "--" if x in ("", "None") else f"{float(x):.{nd}f}"


def sh(s):
    return "0.05" if s == "p05" else "0.10"


def tab_design(L="0.0"):
    import collections
    eo = {(r["shock"], r["W"], r["L"]): r for r in csv.DictReader(open(f"{D}/c3_exit_ordering.csv"))}
    g = collections.defaultdict(list)
    for r in T:
        if r["L"] == L and r["vbar_E_expenditure"] not in ("", "None"):
            g[(r["shock"], r["W"], r["c"])].append(float(r["vbar_E_expenditure"]))
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Sponsor pool by design: participation categories and expected disbursement at the common cap by operating cost}\label{tab:c3design}",
         r"\begin{threeparttable}\resizebox{\textwidth}{!}{\begin{tabular}{ccccccccccc}\toprule",
         r" & & \multicolumn{3}{c}{Number of types} & \multicolumn{3}{c}{$E[S]$ at $\bar V$ by operating cost} & \multicolumn{3}{c}{Pairs of types at $\bar V$}\\\cmidrule(lr){3-5}\cmidrule(lr){6-8}\cmidrule(l){9-11}",
         r"Arrears entry & $W$ & No support & Positive $V^*$ & Abstain & $c = 24$ & $c = 25$ & $c = 26$ & Pairs & Exit order holds & $E[S]$ ordered\\\midrule"]
    for r in S:
        if r["L"] != L:
            continue
        cells = []
        for c in ("24.0", "25.0", "26.0"):
            v = g.get((r["shock"], r["W"], c))
            cells.append("--" if not v else f"{sum(v)/len(v):.2f}")
        e = eo[(r["shock"], r["W"], r["L"])]
        cells += [e["pairs_vbar"], e["pairs_vbar_condition_holds"], e["pairs_vbar_ES_ordered"]]
        o.append(f"{sh(r['shock'])} & {f(r['W'],0)} & {r['n_zero']} & {r['n_positive']} & {r['n_abstain']} & " + " & ".join(cells) + "\\\\")
    o += [r"\bottomrule\end{tabular}}",
          r"\begin{tablenotes}\footnotesize\item \textit{Notes:} Twelve types, $c \in \{24, 25, 26\}$ by $\rho \in \{0.10, 0.12, 0.15, 0.20\}$. No support: the sponsor participates at a cap of zero. Abstain: no cap up to $\bar V = 25$ meets the outside option. $E[S]$ at $\bar V$: expected discounted disbursement at the common cap, averaged over the participating types with that operating cost; across discount rates within a cost group it varies by less than 0.0003 in every design. Pairs: pairs of participating types with different operating costs. Exit order holds: pairs for which, on every one of the $2^{20}$ revenue histories, the higher-cost type does not exit before the lower-cost type's concession ends, the condition of Proposition~\ref{prop:c3}. $E[S]$ ordered: pairs in which the higher-cost type's expected disbursement at $\bar V$ is at least that of the lower-cost type. Baseline: costless exit. Source: \texttt{c3\_selection.py}.\end{tablenotes}",
          r"\end{threeparttable}\end{table}"]
    return "\n".join(o)


def tab_types(shock="p10", W="30.0", L="0.0"):
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Types in one design: minimum cap, expenditure and operating outcomes at the minimum cap and at the common cap (arrears entry 0.10, $W = 30$, costless exit)}\label{tab:c3types}",
         r"\begin{threeparttable}\begin{tabular}{ccccccccccc}\toprule",
         r" & & & \multicolumn{4}{c}{At own minimum cap} & \multicolumn{4}{c}{At common cap $\bar V = 25$}\\\cmidrule(lr){4-7}\cmidrule(l){8-11}",
         r"$c$ & $\rho$ & $V^*$ & $E[S]$ & Target & Exit & Expiry & $E[S]$ & Target & Exit & Expiry\\\midrule"]
    for r in T:
        if (r["shock"], r["W"], r["L"]) != (shock, W, L):
            continue
        if r["category"] == "abstain":
            o.append(f"{f(r['c'],0)} & {f(r['rho'])} & abstains & & & & & & & & \\\\")
            continue
        o.append(" & ".join([f(r["c"], 0), f(r["rho"]), f(r["Vstar"]),
                             f(r["own_E_expenditure"]), f(r["own_p_target"]), f(r["own_p_abandon"]), f(r["own_p_expiry"]),
                             f(r["vbar_E_expenditure"]), f(r["vbar_p_target"]), f(r["vbar_p_abandon"]), f(r["vbar_p_expiry"])]) + r"\\")
    o += [r"\bottomrule\end{tabular}",
          r"\begin{tablenotes}\footnotesize\item \textit{Notes:} $E[S]$ is expected discounted disbursement. Target, Exit and Expiry are the probabilities that the concession ends by reaching $W$, by the sponsor's exit and at $\bar T$. Source: \texttt{c3\_selection.py}.\end{tablenotes}",
          r"\end{threeparttable}\end{table}"]
    return "\n".join(o)


def tab_auction(L="0.0"):
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Second-price award: exposure and expenditure (costless exit)}\label{tab:c3auction}",
         r"\begin{threeparttable}\resizebox{\textwidth}{!}{\begin{tabular}{cccccccccc}\toprule",
         r"Arrears & $W$ & $n$ & Award & One qualifier & Cap & Own $V^*$ & $E[S]$ at cap & $E[S]$ at own $V^*$ & $E[S]$ per opportunity\\\midrule"]
    for r in A:
        if r["L"] != L:
            continue
        o.append(" & ".join([sh(r["shock"]), f(r["W"], 0), r["n"], f(r["p_award"]), f(r["p_single_given_award"]),
                             f(r["cap_given_award"], 1), f(r["own_v_given_award"], 1), f(r["ES_cap_given_award"]),
                             f(r["ES_own_given_award"]), f(r["ES_per_opportunity"])]) + r"\\")
    o += [r"\bottomrule\end{tabular}}",
          r"\begin{tablenotes}\footnotesize\item \textit{Notes:} $n$ sponsors drawn independently and uniformly from the twelve types; exact expectations over all $12^n$ profiles. Award: probability that at least one sponsor qualifies. One qualifier: probability, given an award, that a single sponsor qualifies and therefore receives $\bar V = 25$. Cap and Own $V^*$: expected awarded cap and expected minimum cap of the winner, given an award. $E[S]$ at cap and at own $V^*$: the winner's expected disbursement under the awarded cap and under its own minimum cap, given an award. $E[S]$ per opportunity counts zero when there is no award. Source: \texttt{c3\_selection.py}.\end{tablenotes}",
          r"\end{threeparttable}\end{table}"]
    return "\n".join(o)


def load_dec():
    return {(r["shock"], r["W"], r["L"], r["n"]): r for r in csv.DictReader(open(f"{D}/c3_higher_cost_decomposition.csv"))}


def tab_selection(L="0.0"):
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Selection at the awarded cap under the second-price award (costless exit)}\label{tab:c3select}",
         r"\begin{threeparttable}\resizebox{\textwidth}{!}{\begin{tabular}{ccccccccccc}\toprule",
         r" & & & \multicolumn{3}{c}{Share} & \multicolumn{5}{c}{Restricted comparison at the awarded cap}\\\cmidrule(lr){4-6}\cmidrule(l){7-11}",
         r"Arrears & $W$ & $n$ & Contested & Cap zero & Restricted & Strictly lowest & Tied & Not lowest & Excess & Exit order holds\\\midrule"]
    for r in A:
        if r["L"] != L:
            continue
        pc = float(r["p_contested_given_award"])
        capzero = float(r["p_cap_zero_given_award"]) / pc
        o.append(" & ".join([sh(r["shock"]), f(r["W"], 0), r["n"], f(r["p_contested_given_award"]), f"{capzero:.2f}",
                             f(r["p_informative_given_contested"]), f(r["inf_strict"]),
                             f(float(r["inf_tie_same"]) + float(r["inf_tie_diff"])), f(r["inf_higher"]),
                             f(r["mean_excess_ES_informative"]),
                             f(r["inf_order"])]) + r"\\")
    o += [r"\bottomrule\end{tabular}}",
          r"\begin{tablenotes}\footnotesize\item \textit{Notes:} Contested: share of awards in which at least two sponsors qualify, so that the winner and the runner-up both accept the awarded cap. Cap zero: share of contested awards with an awarded cap of zero, in which no sponsor would receive support; these awards remain in Table~\ref{tab:c3auction}. Restricted: share of contested awards with a positive awarded cap in which the sponsors that would accept that cap do not all have the same operating cost. The remaining columns refer to the restricted awards, with every sponsor that would accept the cap evaluated at that cap. Strictly lowest: the winner's expected disbursement is below that of every other such sponsor by more than 0.01. Tied: it lies within 0.01 of the lowest among the other sponsors. Not lowest: it exceeds the lowest among the other sponsors by more than 0.01. Excess: mean amount by which the winner's expected disbursement exceeds the lowest among all such sponsors. Exit order holds: share of restricted awards in which the condition of Proposition~\ref{prop:c3} holds on every revenue history for every pair of such sponsors with different operating costs. Source: \texttt{c3\_selection.py}.\end{tablenotes}",
          r"\end{threeparttable}\end{table}"]
    return "\n".join(o)


def tab_selection_vbar(L="0.0"):
    dec = load_dec()
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Selection evaluated at the common cap $\bar V$ in contested awards (costless exit)}\label{tab:c3selectvbar}",
         r"\begin{threeparttable}\resizebox{\textwidth}{!}{\begin{tabular}{ccccccccccc}\toprule",
         r"Arrears & $W$ & $n$ & Strictly lowest & Tied & Not lowest & Excess & Higher cost & Strictly lower $V^*$ & Different costs & Exit order holds\\\midrule"]
    for r in A:
        if r["L"] != L:
            continue
        d = dec[(r["shock"], r["W"], r["L"], r["n"])]
        o.append(" & ".join([sh(r["shock"]), f(r["W"], 0), r["n"], f(r["vb_strict"]),
                             f(float(r["vb_tie_same"]) + float(r["vb_tie_diff"])), f(r["vb_higher"]),
                             f(r["mean_excess_ES_at_vbar"]), f(d["p_higher_cost"]), f(d["p_strictly_lower_Vstar"]),
                             f(r["vb_diffcost_given_contested"]), f(r["vb_order"])]) + r"\\")
    o += [r"\bottomrule\end{tabular}}",
          r"\begin{tablenotes}\footnotesize\item \textit{Notes:} All contested awards; every qualifying sponsor is evaluated at $\bar V = 25$. Strictly lowest, Tied, Not lowest and Excess are defined as in Table~\ref{tab:c3select}, with all qualifying sponsors as the comparison set. Different costs: share of contested awards in which the qualifying sponsors do not all have the same operating cost. Exit order holds: share of those awards in which the condition of Proposition~\ref{prop:c3} holds on every revenue history for every pair of qualifying sponsors with different operating costs. Higher cost: share of contested awards won by a sponsor whose operating cost exceeds the lowest among the qualifiers. Strictly lower $V^*$: share won by such a sponsor with a minimum cap strictly below that of every lower-cost qualifier; the remainder of Higher cost consists of awards decided by a tie at the lowest bid. Source: \texttt{c3\_selection.py}.\end{tablenotes}",
          r"\end{threeparttable}\end{table}"]
    return "\n".join(o)


def tab_operating(L="0.0"):
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Operating outcomes of the winner under the awarded cap and under its own minimum cap (costless exit)}\label{tab:c3oper}",
         r"\begin{threeparttable}\begin{tabular}{ccccccccc}\toprule",
         r" & & & \multicolumn{3}{c}{Under the awarded cap} & \multicolumn{3}{c}{Under own minimum cap}\\\cmidrule(lr){4-6}\cmidrule(l){7-9}",
         r"Arrears & $W$ & $n$ & Target & Exit & Expiry & Target & Exit & Expiry\\\midrule"]
    for r in A:
        if r["L"] != L:
            continue
        o.append(" & ".join([sh(r["shock"]), f(r["W"], 0), r["n"],
                             f(r["tgt_cap_given_award"]), f(r["ext_cap_given_award"]), f(r["exp_cap_given_award"]),
                             f(r["tgt_own_given_award"]), f(r["ext_own_given_award"]), f(r["exp_own_given_award"])]) + r"\\")
    o += [r"\bottomrule\end{tabular}",
          r"\begin{tablenotes}\footnotesize\item \textit{Notes:} Probabilities, given an award, that the winner's concession ends by reaching $W$ (Target), by the sponsor's exit (Exit) and at $\bar T$ before reaching $W$ (Expiry). Reaching $W$ or $\bar T$ ends the concession and says nothing about service afterward. Source: \texttt{c3\_selection.py}.\end{tablenotes}",
          r"\end{threeparttable}\end{table}"]
    return "\n".join(o)


def tab_example(shock="p10", W=30.0, L=0.0, pair=((25.0, 0.10), (24.0, 0.15))):
    """Two-sponsor auction: both sponsors evaluated at the cap the second-price rule awards."""
    import json
    types = [(c, rho) for c in (24.0, 25.0, 26.0) for rho in (0.10, 0.12, 0.15, 0.20)]
    ts = next(t for t in json.load(open(f"{D}/c3_type_stage.json"))
              if (t["shock"], t["W"], t["L"]) == (shock, W, L))
    js = [types.index(p) for p in pair]
    vs = {j: ts["vstar"][str(j)] for j in js}
    assert all(v is not None for v in vs.values()) and len(set(vs.values())) == 2
    order = sorted(js, key=lambda j: vs[j])
    cap = vs[order[1]]                       # second-lowest qualifying bid
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Two-sponsor auction: both sponsors evaluated at the awarded cap (arrears entry 0.10, $W = 30$, costless exit)}\label{tab:c3example}",
         r"\begin{threeparttable}\begin{tabular}{ccccccccc}\toprule",
         r" & & & & \multicolumn{5}{c}{At the awarded cap}\\\cmidrule(l){5-9}",
         r"$c$ & $\rho$ & Bid $V^*$ & Outcome & $E[S]$ & Target & Exit & Expiry & $U - \omega$\\\midrule"]
    for j, role in zip(order, ("wins", "accepts, loses")):
        r = ts["table"][f"{j}|{cap}"]
        o.append(" & ".join([f(types[j][0], 0), f(types[j][1]), f(vs[j], 3), role, f(r["E_expenditure"], 3),
                             f(r["p_target"]), f(r["p_abandon"]), f(r["p_expiry"]), f(r["U"])]) + r"\\")
    o += [r"\bottomrule\end{tabular}",
          r"\begin{tablenotes}\footnotesize\item \textit{Notes:} Second-price award between the two sponsors: the sponsor with the lower bid wins, and the awarded cap equals the other bid, " + f"{cap:.3f}" + r". Both sponsors are evaluated at that cap. $E[S]$ is expected discounted disbursement; Target, Exit and Expiry are the probabilities that the concession ends by reaching $W$, by the sponsor's exit and at $\bar T$; $U - \omega$ is sponsor surplus, with $\omega = 0$. Source: \texttt{c3\_selection.py}, saved type stage \texttt{results\_c3/c3\_type\_stage.json}.\end{tablenotes}",
          r"\end{threeparttable}\end{table}"]
    return "\n".join(o)


def unwrap_resized(t):
    """threeparttable measures the tabular at its natural width, so a resized tabular inside it
    overflows the text block. Resized tables carry their notes in a text-width minipage instead."""
    if r"\resizebox" not in t:
        return t
    t = t.replace(r"\begin{threeparttable}\resizebox", r"\resizebox")
    t = t.replace(r"\begin{tablenotes}\footnotesize\item \textit{Notes:}",
                  r"\par\smallskip\begin{minipage}{\textwidth}\footnotesize\textit{Notes:}")
    t = t.replace(r"\end{tablenotes}", r"\end{minipage}")
    t = t.replace(r"\end{threeparttable}\end{table}", r"\end{table}")
    return t


if __name__ == "__main__":
    main = [tab_example(), tab_types(), tab_auction(), tab_operating()]
    appendix = [tab_design(), tab_selection(), tab_selection_vbar()]
    open("c3_tables_main.tex", "w").write("\n\n".join(unwrap_resized(t) for t in main))
    open("c3_tables_appendix.tex", "w").write("\n\n".join(unwrap_resized(t) for t in appendix))
    print("ok")
