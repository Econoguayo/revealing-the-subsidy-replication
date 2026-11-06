# Verification record, package version 1.0.0 (November 5, 2026)

## Paper version

The package was verified against the LaTeX source of the working paper dated November 4, 2026 (`revealing_the_subsidy.tex`, MD5 `7b4aa5abc8d903c179967a46396570bf`). A later revision of the paper requires the comparison of section 4 below to be repeated with `python run_all.py --paper PATH`.

## 1. Environment

Python 3.13.18, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, statsmodels 0.15.0, patsy 1.0.3 and pytest 9.1.1, on Linux with two processor cores. `_rerun/environment.txt` records the environment of each run.

## 2. Integrity

- Every file matches its SHA-256 checksum in `MANIFEST.sha256` (`tools/verify_manifest.py`).
- The 41 files of `3_model/` other than its manifest match the checksums recorded in `3_model/manifest_all.json`, the manifest of the frozen archive `lpvs_tractability_2026-11-04a.zip` (SHA-256 `f978159c69434146fd94a986ec6f8cba90cba1ce643a809fbb98226f2954012d`). Fifteen files of the archive are not included: the working notes on the participation, selection and posted-offer exercises (`c1_note`, `c3_note` and `c4_note`, in TeX and PDF), the first versions of `c3_note` and `c4_note` (TeX and PDF), a change note on `c3_note`, a draft of the numerical section, and the superseded table files `c3_tables_v1.tex`, `c4_tables_main_v1.tex` and `c4_tables_appendix_v1.tex`.

## 3. Reproduction

**Concessionality component.** From the frozen inputs of October 7, 2026, the scripts reproduce byte for byte the merged dataset (`combined_dataset.json` and `psw_concessionality_combined.csv`), Table 1 with its robustness panel, the Appendix E disclosure rates, the fiscal-year classification and every output of `rc04_final_spec.py`. The registry coding reproduces the published figures before any alternative coding is run (`baseline_check.txt`: PASS).

**Model component.** All 44 tests pass (31 in `test_lpvs_core.py`, 9 in `test_c4.py` and 4 in `test_c4_sequential.py`). Two full reruns of the exercises in clean copies, the first with the rerun script of November 4 and the second with `run_all.py` (13 minutes in all, of which about 12 for the exercises, on two cores), reproduced byte for byte every results file (the CSV files of `results_L0/`, `results_Lm2/`, `results_c3/` and `results_c4/`, `c3_type_stage.json` and `results_probes.json`) and every table file. The run manifests differ from the shipped ones only in the run time, the interpreter version, the platform string and, for `results_c3/manifest.json` and `results_c4/manifest.json`, in the list of other files present in the folder when the script ran; the code hashes, assumptions and checks are identical. The internal checks of the scripts passed: the type stage of `c4_posted_offer.py` matched the saved one and its auction rows matched those of `c3_selection.py` (maximum deviation 0); sequential and auction award probabilities agreed to 1.9e-14; the formula for sequential offers matched enumeration to 3.4e-13.

## 4. Comparison with the paper

The full run of `run_all.py --paper` compared 46 regenerated files with the shipped outputs (0 differing) and gave the results below; the outputs of the comparison are in `4_paper_tables/output/comparison_with_paper/`. After `paper_tables.py` was revised to write the paper's labels, a quick run repeated the comparison with the same result.

| Check | Result |
|---|---|
| Generated tables against the tables of the same label (`check_paper_tables.py`): Tables 1, 4, 5, 6 and D1 to D18 | 22 of 22 match; signs compared |
| Tables 4, 5 and D1 to D18, token by token (`reconcile.py`) | 2,872 tokens, 0 differing |
| Table 6 against the corresponding cells of Table D10 as written by `c4_tables.py` (`table6.py`) | 108 cells, 0 differing |
| Section 2, note to Table 1 and Appendix E (`trace_concessionality_text.py`) | 28 statements: 27 match; 1 wording point (E17, below) |
| Model statements in Sections 5.3, 6.3, 6.4 and 8.1 and Appendices A and C (`trace_text.py`) | 86 statements, 86 match |
| Section 6.4 cells and Appendix C shares, recomputed from the results; presence of the seven example values of the introduction and Section 6.2 in the paper's Table 5 (`trace_text2.py`) | 9 statements, 9 match |
| Scaling Solar arithmetic, Section 2 and note to Table 2 (`check_scaling_solar.py`) | 6 statements, 6 match |
| Worked example of Section 4 and counterexample with recovery in Appendix A (`check_worked_examples.py`) | 6 statements, 6 match |

E17. Appendix E states that one disclosure provides a range. The extracted data hold three estimates reported as ranges: CRRH II (3.3 to 4.5 percent) and Robust Nigeria (1.9 to 5.3 percent), both inside square brackets, and Bank of Bhutan (7.0 to 7.9 percent). The sentence is accurate if the two bracketed ranges are counted among the bracketed values described in the preceding sentence.

Two statements of `trace_text.py` were adjusted for this package: E15b now checks the qualified wording of the November 4 paper ("expected disbursement under the awarded cap changes by at most 0.04"; largest change 0.038), and F10b compares each end of the range "0.0002 to 0.011" at its own printed precision.

## 5. Not checked

- The entries of Table 2 against their sources. The package records the entries and the sources named in the table note and checks only the arithmetic that the text derives from them.
- A repeat harvest of the disclosure pages for this version. The harvest of November 3, 2026, run with the unmodified scripts of October 7, reproduced the extracted dataset.
- Runs on Windows or macOS.
- The terms of use of the IDA, IFC, MIGA and World Bank pages from which data were taken.
- The proofs of Appendix A, which involve no computation, and Tables 3 and 7, which contain no data.
