r"""Tables of the working paper with the paper's labels, from the outputs of the model component.

Usage: python paper_tables.py MODEL_DIR OUT_DIR
  MODEL_DIR  folder holding results_c4/ and the *.tex tables written by make_tables.py, c3_tables.py
             and c4_tables.py (default: ../3_model)
  OUT_DIR    output folder (default: output/paper_tables)

Writes into OUT_DIR:
  tab_c4_compact.tex   Table 6: per opportunity, two sponsors, single offer, sequential offers
                       and auction, six designs, costless exit (from results_c4/)
  tab_c3_example.tex   Table 5: the two-sponsor example (first table of c3_tables_main.tex)
  tab_c1_B.tex         Table 4: minimum acceptable cap by type (table B of tables_numerical.tex)
  appendix_tables.tex  Tables D1 to D18, in the order of the paper's Appendix D
Every \label and \ref of the model scripts is replaced by the label the paper uses (PAPER_LABEL);
table bodies are copied unchanged.
"""
import csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
MODEL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "3_model")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "output", "paper_tables")
os.makedirs(OUT, exist_ok=True)


def _in(name):
    return open(os.path.join(MODEL, name), encoding="utf-8")


from fmt import f  # shared half-up formatter (fmt.py)




def sh(s):
    return "0.05" if s == "p05" else "0.10"


def compact_c4(L="0.0", n="2"):
    C = list(csv.DictReader(_in("results_c4/c4_comparison.csv")))
    S = list(csv.DictReader(_in("results_c4/c4_sequential.csv")))
    single = {(r["shock"], r["W"]): r for r in C if r["L"] == L and r["n"] == "1"}
    auction = {(r["shock"], r["W"]): r for r in C if r["L"] == L and r["n"] == n}
    seq = {(r["shock"], r["W"]): r for r in S if r["L"] == L and r["n"] == n}
    o = [r"\begin{table}[htbp]\centering\small",
         r"\caption{Single offer, sequential offers and auction with two sponsors: outcomes per procurement opportunity (costless exit)}\label{tab:c4compact}",
         r"\begin{tabular}{ccccccccc}\toprule",
         r" & & & & Exposure & Expenditure & \multicolumn{3}{c}{Operating outcomes}\\\cmidrule(l){7-9}",
         r"Arrears entry & $W$ & Procedure & Award & Cap & $E[S]$ & Target & Exit & Expiry\\\midrule"]
    for i, key in enumerate(single):
        if i:
            o.append(r"\addlinespace")
        for r, label in ((single[key], "Single offer"), (seq[key], "Sequential"), (auction[key], "Auction")):
            o.append(" & ".join([sh(key[0]), f(key[1], 0), label, f(r["p_award"], 3), f(r["cap_per_opportunity"], 1),
                                 f(r["ES_per_opportunity"]), f(r["tgt_per_opportunity"], 3),
                                 f(r["ext_per_opportunity"], 3), f(r["exp_per_opportunity"], 3)]) + r"\\")
    o += [r"\bottomrule\end{tabular}",
          r"\par\smallskip\begin{minipage}{\textwidth}\footnotesize\textit{Notes:} Per procurement opportunity; every measure counts zero when there is no award. "
          r"Single offer: $\bar V = 25$ offered to one sponsor drawn from the twelve types. Sequential: $\bar V$ offered to up to two independently drawn sponsors in turn, with the award to the first that accepts. "
          r"Auction: two sponsors under the second-price award rule with the same $\bar V$. Award: probability of an award. Cap: expected awarded cap. $E[S]$: expected discounted disbursement. "
          r"Target, Exit and Expiry: probabilities that the opportunity ends in a concession that reaches $W$, ends by the sponsor's exit, or reaches $\bar T$ before $W$. "
          r"Three bidders and the termination penalty: Tables~\ref{tab:c4peropp} and~\ref{tab:c4peropp_pen}. Source: \texttt{c4\_posted\_offer.py}, \texttt{c4\_sequential.py}.\end{minipage}",
          r"\end{table}"]
    return "\n".join(o)


# Labels written by the model's table scripts and the labels of the same tables in the paper.
PAPER_LABEL = {"tab:A": "tab:c1A", "tab:B": "tab:c1B", "tab:C": "tab:c1C", "tab:B0": "tab:c1B0",
               "tab:c3auction": "tab:c3award", "tab:c3design": "tab:c3pool", "tab:c3select": "tab:c3select_awarded",
               "tab:c3selectvbar": "tab:c3select_common", "tab:c4opp": "tab:c4peropp", "tab:c4award": "tab:c4cond",
               "tab:c4ar": "tab:c4access", "tab:c4dec": "tab:c4decomp", "tab:c4opppen": "tab:c4peropp_pen",
               "tab:c4awardpen": "tab:c4cond_pen", "tab:c4arpen": "tab:c4access_pen", "tab:c4decpen": "tab:c4decomp_pen",
               "tab:c4mono": "tab:c4monotone"}
# Order of the tables in Appendix D of the paper (Tables D1 to D18).
APPENDIX_ORDER = ["tab:c1A", "tab:c1C", "tab:c1B0", "tab:c3types", "tab:c3award", "tab:c3oper", "tab:c3pool",
                  "tab:c3select_awarded", "tab:c3select_common", "tab:c4peropp", "tab:c4cond", "tab:c4access", "tab:c4decomp",
                  "tab:c4peropp_pen", "tab:c4cond_pen", "tab:c4access_pen", "tab:c4decomp_pen", "tab:c4monotone"]


def relabel(t):
    return re.sub(r"\\(label|ref)\{(tab:[^}]+)\}", lambda m: "\\" + m.group(1) + "{" + PAPER_LABEL.get(m.group(2), m.group(2)) + "}", t)


def label_of(t):
    return re.search(r"\\label\{([^}]+)\}", t).group(1)


def split_tables(text):
    return re.findall(r"\\begin\{table\}.*?\\end\{table\}", text, flags=re.S)


if __name__ == "__main__":
    open(f"{OUT}/tab_c4_compact.tex", "w", encoding="utf-8").write(compact_c4())
    c3main = split_tables(_in("c3_tables_main.tex").read())
    c3app = split_tables(_in("c3_tables_appendix.tex").read())
    c4main = split_tables(_in("c4_tables_main.tex").read())
    c4app = split_tables(_in("c4_tables_appendix.tex").read())
    c1 = split_tables(_in("tables_numerical.tex").read())
    every = {label_of(t): t for t in (relabel(x) for x in c1 + c3main + c3app + c4main + c4app)}
    example = every.pop("tab:c3example")
    open(f"{OUT}/tab_c3_example.tex", "w", encoding="utf-8").write(example)
    b = every.pop("tab:c1B")
    open(f"{OUT}/tab_c1_B.tex", "w", encoding="utf-8").write(b)
    assert sorted(every) == sorted(APPENDIX_ORDER), sorted(set(every) ^ set(APPENDIX_ORDER))
    rest = [every[k] for k in APPENDIX_ORDER]
    open(f"{OUT}/appendix_tables.tex", "w", encoding="utf-8").write("\n\n".join(rest))
    labels = re.findall(r"\\label\{([^}]+)\}", "\n".join([example, b] + rest))
    assert len(labels) == len(set(labels)), "duplicate labels"
    print("ok", len(rest) + 3, "tables")
