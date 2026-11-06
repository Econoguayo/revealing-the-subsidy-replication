"""Build LaTeX tables for the C1 note from the exercise CSVs."""
import csv, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "results_L0"
SENS = sys.argv[2] if len(sys.argv) > 2 else "results_Lm2"


def load(path):
    return list(csv.DictReader(open(path)))


def f(x, nd=2):
    return f"{float(x):.{nd}f}"


def table_A(rows):
    out = []
    rcs = ["0.06", "0.08", "0.1", "0.12"]
    out.append(r"\begin{table}[htbp]\centering\small")
    out.append(r"\caption{Smallest compensation target, as a multiple of $I$, at which the reference path meets the outside option}\label{tab:A}")
    out.append(r"\begin{threeparttable}\begin{tabular}{llcccc}\toprule")
    out.append(r" & & \multicolumn{4}{c}{Contractual rate $r_c$}\\\cmidrule(l){3-6}")
    out.append(r"Operating cost $c$ & Discount rate $\rho$ & 0.06 & 0.08 & 0.10 & 0.12\\\midrule")
    for c in ("24.0", "25.0", "26.0"):
        for rho in ("0.1", "0.12", "0.15", "0.2"):
            cells = []
            for rc in rcs:
                r = [x for x in rows if x["c"] == c and x["rho"] == rho and x["r_c"] == rc][0]
                v = r["W_over_I_min"]
                cells.append("n.a." if v in ("", "None") else f(v))
            out.append(f"{float(c):.0f} & {float(rho):.2f} & " + " & ".join(cells) + r"\\")
        if c != "26.0":
            out.append(r"\addlinespace")
    out.append(r"\bottomrule\end{tabular}")
    out.append(r"\begin{tablenotes}\footnotesize\item \textit{Notes:} Reference path: normal payment in every period, revenue 30, no support paid. $I = 20$, $\bar T = 20$, $\Lambda_W = \Lambda_{\bar T} = 0$, $\omega = 0$. n.a.: the reference payoff is negative even if the concession runs to $\bar T$, so no target suffices. Where $\rho = r_c$ the multiple is 1.00, and where $\rho > r_c$ it exceeds 1, as Corollary~\ref{cor:WI} requires. Source: \texttt{run\_tractability.py}, exercise A.\end{tablenotes}")
    out.append(r"\end{threeparttable}\end{table}")
    return "\n".join(out)


def cell_B(r):
    if r["status"] == "empty":
        return "--"
    if r["status"] == "no support needed":
        return "0"
    return f(r["Vstar"], 1)


def table_B(rows, label, caption_extra):
    out = []
    cols = [(s, W) for s in ("p05", "p10") for W in ("20.0", "27.0", "30.0", "34.0")]
    out.append(r"\begin{table}[htbp]\centering\small")
    out.append(r"\caption{Minimum acceptable cap $V^*$ by sponsor type, compensation target and shock process" + caption_extra + r"}\label{" + label + "}")
    out.append(r"\begin{threeparttable}\begin{tabular}{llcccccccc}\toprule")
    out.append(r" & & \multicolumn{4}{c}{Arrears entry 5 percent a year} & \multicolumn{4}{c}{Arrears entry 10 percent a year}\\\cmidrule(lr){3-6}\cmidrule(l){7-10}")
    out.append(r"$c$ & $\rho$ & $W{=}20$ & 27 & 30 & 34 & $W{=}20$ & 27 & 30 & 34\\\midrule")
    for c in ("24.0", "25.0", "26.0"):
        for rho in ("0.1", "0.12", "0.15", "0.2"):
            cells = []
            for s, W in cols:
                r = [x for x in rows if x["shock"] == s and x["W"] == W and x["c"] == c and x["rho"] == rho][0]
                cells.append(cell_B(r))
            out.append(f"{float(c):.0f} & {float(rho):.2f} & " + " & ".join(cells) + r"\\")
        if c != "26.0":
            out.append(r"\addlinespace")
    out.append(r"\bottomrule\end{tabular}")
    return out


def table_B_close(out, note):
    out.append(r"\begin{tablenotes}\footnotesize\item \textit{Notes:} " + note + r"\end{tablenotes}")
    out.append(r"\end{threeparttable}\end{table}")
    return "\n".join(out)


def table_C(rows):
    out = []
    out.append(r"\begin{table}[htbp]\centering\small")
    out.append(r"\caption{Exposure, expenditure and stopping outcomes at the minimum acceptable cap (interior cases, baseline: costless exit)}\label{tab:C}")
    out.append(r"\begin{threeparttable}\begin{tabular}{lcccccccccc}\toprule")
    out.append(r"Arrears & $W$ & $c$ & $\rho$ & $V^*$ & $E[S_{T^*}]$ & Target & Exit & Expiry & Periods & Cap used\\\midrule")
    sel = [r for r in rows if r["status"] == "threshold found"]
    sel.sort(key=lambda r: (r["shock"], float(r["W"]), float(r["c"]), float(r["rho"])))
    for r in sel:
        sh = "5\\%" if r["shock"] == "p05" else "10\\%"
        out.append(" & ".join([sh, f(r["W"], 0), f(r["c"], 0), f(r["rho"]), f(r["Vstar"], 1),
                               f(r["at_Vstar_E_expenditure"], 1), f(r["at_Vstar_p_target"]),
                               f(r["at_Vstar_p_abandon"]), f(r["at_Vstar_p_expiry"]),
                               f(r["at_Vstar_E_periods"], 1), f(r["at_Vstar_p_cap_exhausted"])]) + r"\\")
    out.append(r"\bottomrule\end{tabular}")
    out.append(r"\begin{tablenotes}\footnotesize\item \textit{Notes:} $V^*$ is the committed exposure if the sponsor receives its own minimum cap. $E[S_{T^*}]$ is expected discounted disbursement, already discounted at $r_f$. Target, Exit and Expiry are the probabilities that the concession ends by reaching $W$, by the sponsor's exit, and at $\bar T$; Periods is the expected number of operating periods under the sponsor; Cap used is the probability that disbursement reaches $V^*$. Reaching $W$ or $\bar T$ ends the concession and says nothing about service afterward. Source: \texttt{run\_tractability.py}, exercise B, baseline.\end{tablenotes}")
    out.append(r"\end{threeparttable}\end{table}")
    return "\n".join(out), sel


if __name__ == "__main__":
    A = load(f"{BASE}/exercise_A_reference_viability.csv")
    B = load(f"{BASE}/exercise_B_participation_map.csv")
    B0 = load(f"{SENS}/exercise_B_participation_map.csv")
    tA = table_A(A)
    oB = table_B(B, "tab:B", " (baseline: costless exit)")
    tB = table_B_close(oB, r"Entries: 0, the sponsor participates without support; a number, the interior minimum acceptable cap $V^*$, in the same units as $I = 20$; --, the participation set is empty for every cap. $r_c = 0.08$, $R = (30, 20)$, $R^* = 26$, $\kappa = 0.8$, $\bar s = 10$, $r_f = 0.05$, $\bar T = 20$, arrears persistence $2/3$, $\Lambda_W = \Lambda_{\bar T} = 0$, exit value $L = 0$, $\omega = 0$. The column $W = 20$ is the manuscript's $W = I$. Every interior case passed the grid diagnostic before the threshold search. Source: \texttt{run\_tractability.py}, exercise B.")
    oB0 = table_B(B0, "tab:B0", " (sensitivity: termination penalty, $L = -2$)")
    tB0 = table_B_close(oB0, r"As in Table~\ref{tab:B}, except that exit carries a termination penalty of 2 ($L = -2$). Source: \texttt{run\_tractability.py}, exercise B, run with \texttt{L\_EXIT=-2}.")
    tC, sel = table_C(B)
    open("tables_numerical.tex", "w").write("\n\n".join([tA, tB, tC, tB0]))
    # summary counts
    for name, rows in (("baseline", B), ("penalty", B0)):
        cnt = {}
        for r in rows:
            cnt[(r["shock"], r["W"], r["status"])] = cnt.get((r["shock"], r["W"], r["status"]), 0) + 1
        print(name, sorted(cnt.items()))
        bad = [r for r in rows if r["status"] == "threshold found" and r["grid_monotone"] != "True"]
        print(name, "interior cases", sum(r["status"] == "threshold found" for r in rows), "non-monotone", len(bad))
