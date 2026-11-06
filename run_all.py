"""Reproduce every generated exhibit of "Revealing the Subsidy" and compare the results with the
outputs shipped in this package.

Usage (from the package root):
    python run_all.py                  full run: reruns the model exercises (about 13 minutes on two cores)
    python run_all.py --quick          skips the model exercises and formats the tables from the shipped results
                                       (about 1.5 minutes)
    python run_all.py --paper PATH     also compares every generated table and traced statement with the paper source

The shipped outputs are never overwritten. Every regenerated file is written under _rerun/, and
_rerun/SUMMARY.txt lists each comparison. The script stops at the first failing step.
"""
import argparse, filecmp, hashlib, json, os, platform, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(ROOT, "_rerun")
PY = sys.executable
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONHASHSEED="0")
LOG, SUMMARY, PAPER_LINES = None, [], []

MODEL_CODE = ["lpvs_core.py", "run_tractability.py", "probe_assumptions.py", "c3_selection.py", "c3_exit_diagnostic.py",
              "c4_posted_offer.py", "c4_sequential.py", "make_tables.py", "c3_tables.py", "c4_tables.py",
              "test_lpvs_core.py", "test_c4.py", "test_c4_sequential.py"]
MODEL_RESULTS = ["results_L0", "results_Lm2", "results_c3", "results_c4", "results_probes.json"]
MODEL_TABLES = ["tables_numerical.tex", "c3_tables_main.tex", "c3_tables_appendix.tex", "c4_tables_main.tex", "c4_tables_appendix.tex"]
RUN_FIELDS = {"run_utc", "python", "numpy", "platform", "outputs"}   # fields of a run manifest that record the run, not the computation


def p(*parts):
    return os.path.join(ROOT, *parts)


def say(msg):
    print(msg, flush=True)
    LOG.write(msg + "\n")
    LOG.flush()


def run(args, cwd, env=None, stdout_file=None):
    say(f"  $ {' '.join(os.path.relpath(a, ROOT) if os.path.isabs(a) and a.startswith(ROOT) else a for a in args)}   [in {os.path.relpath(cwd, ROOT)}]")
    t0 = time.time()
    with open(stdout_file, "w", encoding="utf-8") if stdout_file else open(os.devnull, "w") as fh:
        r = subprocess.run([PY] + args, cwd=cwd, env=env or ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                           encoding="utf-8", errors="replace")
        fh.write(r.stdout)
    LOG.write(r.stdout)
    say(f"    exit {r.returncode}, {time.time() - t0:.0f} s")
    if r.returncode != 0:
        print(r.stdout[-3000:])
        sys.exit(f"step failed: {args}")
    return r.stdout


def norm_bytes(path):
    return open(path, "rb").read().replace(b"\r\n", b"\n")


def compare_file(new, ref, label):
    if not os.path.exists(new):
        verdict = "MISSING in rerun"
    elif open(new, "rb").read() == open(ref, "rb").read():
        verdict = "identical"
    elif norm_bytes(new) == norm_bytes(ref):
        verdict = "identical after line-ending normalization"
    elif ref.endswith(".json") and os.path.basename(ref).startswith("manifest"):
        a, b = json.load(open(new, encoding="utf-8")), json.load(open(ref, encoding="utf-8"))
        core_a = {k: v for k, v in a.items() if k not in RUN_FIELDS}
        core_b = {k: v for k, v in b.items() if k not in RUN_FIELDS}
        common = set(a.get("outputs", {})) & set(b.get("outputs", {}))
        same_out = all(a["outputs"][k] == b["outputs"][k] for k in common)
        verdict = ("run manifest: code hashes, assumptions and checks identical; output hashes identical for "
                   f"{len(common)} common files (run time, interpreter and platform fields differ)") if core_a == core_b and same_out \
            else "DIFFERS (run manifest content)"
    else:
        verdict = "DIFFERS"
    SUMMARY.append(f"{verdict:<45} {label}")
    return not verdict.startswith(("DIFFERS", "MISSING"))


def compare_tree(new_dir, ref_dir, label):
    ok = True
    for dp, _, fs in os.walk(ref_dir):
        for f in sorted(fs):
            ref = os.path.join(dp, f)
            rel = os.path.relpath(ref, ref_dir)
            ok &= compare_file(os.path.join(new_dir, rel), ref, f"{label}/{rel}".replace("\\", "/"))
    return ok


def environment():
    lines = [f"python {platform.python_version()}", f"platform {platform.platform()}"]
    for mod in ("numpy", "scipy", "pandas", "statsmodels", "patsy", "pytest"):
        try:
            lines.append(f"{mod} {__import__(mod).__version__}")
        except ImportError:
            lines.append(f"{mod} not installed")
    return "\n".join(lines)


def concessionality():
    say("\n[1] Concessionality exhibit: Table 1, Section 2 and Appendix E")
    D, C, O = p("1_concessionality", "data"), p("1_concessionality", "code"), os.path.join(RUN, "1_concessionality")
    frozen = os.path.join(D, "frozen_2026-10-07")
    for sub in ("merge", "table1", "classification", "rc04_final_spec"):
        os.makedirs(os.path.join(O, sub), exist_ok=True)   # rc04_fragility_audit.py does not create its output folder
    run(["-I", os.path.join(C, "recovered", "merge_combined_corrected.py"), frozen, os.path.join(O, "merge")], O,
        stdout_file=os.path.join(O, "merge_log.txt"))
    for f in ("combined_dataset.json", "psw_concessionality_combined.csv"):
        compare_file(os.path.join(O, "merge", f), os.path.join(frozen, f), f"1_concessionality/data/frozen_2026-10-07/{f} (rebuilt by merge)")
    run(["-I", os.path.join(C, "recovered", "build_table1_concessionality.py"), frozen, os.path.join(O, "table1")], O,
        stdout_file=os.path.join(O, "table1_log.txt"))
    run(["-I", os.path.join(C, "recovered", "appendix_e_disclosure_rates.py"), frozen], O,
        stdout_file=os.path.join(O, "appendix_e_disclosure_rates.txt"))
    run(["-I", os.path.join(C, "rc04", "rc04_fragility_audit.py"), os.path.join(D, "registry_export_2026-10-27.csv"),
         os.path.join(D, "fcs_lists", "FY18-FY25"), os.path.join(O, "classification")], O,
        stdout_file=os.path.join(O, "classification_log.txt"))
    run(["-I", os.path.join(C, "rc04", "rc04_final_spec.py"), frozen,
         os.path.join(O, "classification", "rc04_fragility_by_transaction.csv"), os.path.join(O, "rc04_final_spec")], O,
        stdout_file=os.path.join(O, "rc04_final_spec_log.txt"))
    for sub in ("table1", "classification", "rc04_final_spec"):
        compare_tree(os.path.join(O, sub), p("1_concessionality", "output", sub), f"1_concessionality/output/{sub}")
    compare_file(os.path.join(O, "appendix_e_disclosure_rates.txt"), p("1_concessionality", "output", "appendix_e_disclosure_rates.txt"),
                 "1_concessionality/output/appendix_e_disclosure_rates.txt")


def model(quick):
    say("\n[3] Model component (version 2026-11-04a): tests, exercises and tables")
    M = os.path.join(RUN, "3_model")
    os.makedirs(M, exist_ok=True)
    for f in MODEL_CODE:
        shutil.copy2(p("3_model", f), M)
    run(["-m", "pytest", "-q", "-p", "no:cacheprovider", "test_lpvs_core.py", "test_c4.py", "test_c4_sequential.py"], M,
        stdout_file=os.path.join(M, "pytest_log.txt"))
    if quick:
        say("  --quick: results copied from the shipped files; the exercises are not rerun")
        for r in MODEL_RESULTS:
            src = p("3_model", r)
            (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, os.path.join(M, r))
    else:
        run(["run_tractability.py"], M, env=dict(ENV, OUT_DIR="results_L0", L_EXIT="0.0"), stdout_file=os.path.join(M, "log_run_tractability_L0.txt"))
        run(["run_tractability.py"], M, env=dict(ENV, OUT_DIR="results_Lm2", L_EXIT="-2.0"), stdout_file=os.path.join(M, "log_run_tractability_Lm2.txt"))
        run(["c3_selection.py"], M, stdout_file=os.path.join(M, "log_c3_selection.txt"))
        run(["c3_exit_diagnostic.py"], M, stdout_file=os.path.join(M, "log_c3_exit_diagnostic.txt"))
        run(["c4_posted_offer.py"], M, stdout_file=os.path.join(M, "log_c4_posted_offer.txt"))
        run(["c4_sequential.py"], M, stdout_file=os.path.join(M, "log_c4_sequential.txt"))
        run(["probe_assumptions.py"], M, stdout_file=os.path.join(M, "log_probe_assumptions.txt"))
    run(["make_tables.py", "results_L0", "results_Lm2"], M, stdout_file=os.path.join(M, "log_make_tables.txt"))
    run(["c3_tables.py"], M, stdout_file=os.path.join(M, "log_c3_tables.txt"))
    run(["c4_tables.py"], M, stdout_file=os.path.join(M, "log_c4_tables.txt"))
    if not quick:
        for r in MODEL_RESULTS:
            src = p("3_model", r)
            if os.path.isdir(src):
                compare_tree(os.path.join(M, r), src, f"3_model/{r}")
            else:
                compare_file(os.path.join(M, r), src, f"3_model/{r}")
    for t in MODEL_TABLES:
        compare_file(os.path.join(M, t), p("3_model", t), f"3_model/{t}")


def paper_tables(paper):
    say("\n[4] Tables with the paper's labels, and traces of the numbers in the text")
    M, Q, O = os.path.join(RUN, "3_model"), p("4_paper_tables"), os.path.join(RUN, "4_paper_tables")
    os.makedirs(O, exist_ok=True)
    run([os.path.join(Q, "paper_tables.py"), M, os.path.join(O, "paper_tables")], O, stdout_file=os.path.join(O, "paper_tables_log.txt"))
    compare_tree(os.path.join(O, "paper_tables"), os.path.join(Q, "output", "paper_tables"), "4_paper_tables/output/paper_tables")
    run(["-I", os.path.join(Q, "checks", "trace_concessionality_text.py"), p("1_concessionality", "data", "frozen_2026-10-07"),
         os.path.join(O, "trace_concessionality_text.csv")], O)
    compare_file(os.path.join(O, "trace_concessionality_text.csv"), os.path.join(Q, "output", "trace_concessionality_text.csv"),
                 "4_paper_tables/output/trace_concessionality_text.csv")
    run(["-I", os.path.join(Q, "checks", "trace_text.py"), M, os.path.join(O, "trace_model_text.csv")], O)
    compare_file(os.path.join(O, "trace_model_text.csv"), os.path.join(Q, "output", "trace_model_text.csv"),
                 "4_paper_tables/output/trace_model_text.csv")
    run(["-I", os.path.join(Q, "checks", "check_scaling_solar.py"), p("2_scaling_solar", "table2_scaling_solar.csv"),
         os.path.join(O, "trace_scaling_solar_text.csv")], O)
    compare_file(os.path.join(O, "trace_scaling_solar_text.csv"), os.path.join(Q, "output", "trace_scaling_solar_text.csv"),
                 "4_paper_tables/output/trace_scaling_solar_text.csv")
    run(["-I", os.path.join(Q, "checks", "check_worked_examples.py"), os.path.join(O, "trace_worked_examples.csv")], O)
    compare_file(os.path.join(O, "trace_worked_examples.csv"), os.path.join(Q, "output", "trace_worked_examples.csv"),
                 "4_paper_tables/output/trace_worked_examples.csv")
    if paper:
        paper = os.path.abspath(paper)
        say(f"  paper source: {paper} (md5 {hashlib.md5(open(paper, 'rb').read()).hexdigest()})")
        run([os.path.join(Q, "check_paper_tables.py"), paper, os.path.join(O, "paper_tables"), os.path.join(RUN, "1_concessionality", "table1")],
            O, stdout_file=os.path.join(O, "table_comparison_with_paper.txt"))
        run(["-I", os.path.join(Q, "checks", "reconcile.py"), paper, M, os.path.join(O, "reconcile")], O,
            stdout_file=os.path.join(O, "reconcile_log.txt"))
        run(["-I", os.path.join(Q, "checks", "table6.py"), paper, M, os.path.join(O, "table6_differences.csv")], O,
            stdout_file=os.path.join(O, "table6_log.txt"))
        run(["-I", os.path.join(Q, "checks", "trace_text2.py"), M, paper, os.path.join(O, "trace_model_text_2.csv")], O)
        import csv
        PAPER_LINES.append("paper source md5 " + hashlib.md5(open(paper, "rb").read()).hexdigest())
        PAPER_LINES.append("tables: " + open(os.path.join(O, "table_comparison_with_paper.txt"), encoding="utf-8").read().strip().splitlines()[-1])
        rs = list(csv.DictReader(open(os.path.join(O, "reconcile_summary.csv"), encoding="utf-8")))
        PAPER_LINES.append(f"tables 4, 5 and D1 to D18, token by token: {sum(int(r['wp_tokens']) for r in rs)} tokens, "
                           f"{sum(int(r['differing_positions']) for r in rs)} differing")
        PAPER_LINES.append(open(os.path.join(O, "table6_log.txt"), encoding="utf-8").read().strip().splitlines()[0])
        for f in ("trace_concessionality_text.csv", "trace_model_text.csv", "trace_model_text_2.csv", "trace_scaling_solar_text.csv", "trace_worked_examples.csv"):
            v = [r["verdict"] for r in csv.DictReader(open(os.path.join(O, f), encoding="utf-8"))]
            PAPER_LINES.append(f"text statements, {f}: {len(v)} checked; " + ", ".join(f"{v.count(k)} {k}" for k in sorted(set(v))))


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="do not rerun the model exercises")
    ap.add_argument("--paper", help="LaTeX source of the working paper, for the table and text comparison")
    a = ap.parse_args()
    if os.path.exists(RUN):
        shutil.rmtree(RUN)
    os.makedirs(os.path.join(RUN, "1_concessionality"))
    LOG = open(os.path.join(RUN, "run_log.txt"), "w", encoding="utf-8")
    t0 = time.time()
    env = environment()
    open(os.path.join(RUN, "environment.txt"), "w", encoding="utf-8").write(env + "\n")
    say("Environment:\n" + env)
    say("\n[0] Package integrity")
    out = run(["-I", p("tools", "verify_manifest.py"), ROOT], ROOT)
    SUMMARY.append(out.strip().splitlines()[-1])
    concessionality()
    model(a.quick)
    paper_tables(a.paper)
    n_bad = sum(s.startswith(("DIFFERS", "MISSING")) for s in SUMMARY)
    head = [f"run_all.py ({'quick' if a.quick else 'full'} run), {time.strftime('%Y-%m-%d %H:%M:%S')}, {time.time() - t0:.0f} s",
            f"{len(SUMMARY) - 1} files compared with the shipped outputs; {n_bad} differ", ""]
    tail = (["", "Comparison with the paper (--paper):"] + PAPER_LINES) if PAPER_LINES else []
    open(os.path.join(RUN, "SUMMARY.txt"), "w", encoding="utf-8").write("\n".join(head + SUMMARY + tail) + "\n")
    say("\n" + "\n".join(head + SUMMARY + tail))
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
