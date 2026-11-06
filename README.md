# Replication package for "Revealing the Subsidy: Competitive Allocation of Concessional Finance in Fragile States"

Álvaro S. González, Center for Global Development (agonzalez@cgdev.org)

Package version 1.0.0, verified November 5, 2026. CGD Working Paper [NUMBER], [MONTH] 2026.

Repository: https://github.com/Econoguayo/revealing-the-subsidy-replication. Archived copy of version 1.0.0 on Zenodo: https://doi.org/10.5281/zenodo.24013716 (DOI for all versions: https://doi.org/10.5281/zenodo.24013715).

## Overview

The package reproduces every exhibit of the working paper that rests on data or computation: Table 1 and the concessionality figures of Section 2 and Appendix E; Tables 4, 5 and 6 and Appendix Tables D1 to D18; and the numerical statements of the text that derive from these exhibits or from the examples of Section 4 and Appendix A. Table 2 is a compilation from dated public announcements; the package records its entries, its sources and the arithmetic that the text derives from it. Tables 3 and 7 are analytical summaries of the contract and of the model's assumptions and contain no data. The paper has no figures.

The code is in Python and falls into two components. The concessionality component (pandas and statsmodels) estimates the predictability of the concessionality estimates disclosed for IDA Private Sector Window (PSW) transactions from recorded project characteristics. The model component (numpy) implements the Least Present Value of Support (LPVS) contract and computes, exactly and without random numbers, the participation, selection and posted-offer exercises. A single driver, `run_all.py`, reruns both components, writes every result under `_rerun/` and compares each regenerated file with the file shipped in the package. A full run takes about 13 minutes on two processor cores; a quick run, which formats the model tables from the shipped results without rerunning the exercises, takes about one and a half minutes.

## Data availability and provenance statements

### Statement about rights

All data used in the paper come from public web pages of the World Bank Group and from public announcements by the organizations named below. The package redistributes a snapshot of the IDA PSW project list, fields extracted from IFC and MIGA project disclosures together with the sentence in which each concessionality estimate appears, and the text of the World Bank lists of fragile and conflict-affected situations for FY2018 to FY2025. The archived disclosure pages themselves are not redistributed; the package lists their addresses, retrieval times and SHA-256 checksums. The terms of use of each source govern reuse of material drawn from it. The code is licensed under the MIT License (`LICENSE`); the data compiled for this package, its outputs and its documentation are licensed under the Creative Commons Attribution 4.0 International License (`LICENSE-DATA.md`). Material drawn from the third-party sources listed below keeps the terms of its source.

### Summary of availability

- [x] All data are publicly available.
- [ ] Some data cannot be made publicly available.
- [ ] No data can be made publicly available.

### Details on each data source

| Data source | Files in this package | Provided | Citation |
|---|---|---|---|
| IDA PSW project list, IDA18 to IDA20 (204 Board-approved transactions) | `1_concessionality/data/frozen_2026-10-07/psw_data.json`; `1_concessionality/data/registry_export_2026-10-27.csv` | Yes | World Bank, International Development Association, "IDA PSW Projects" |
| IFC Summary of Investment Information pages and MIGA project pages | extracted fields: `1_concessionality/data/frozen_2026-10-07/` (`final_dataset.json`, `miga_results.json`, `combined_dataset.json`, `psw_concessionality_dataset.csv`, `psw_concessionality_combined.csv`); page list: `1_concessionality/data/disclosure_pages_manifest.csv` | Extracted fields and source sentences only | IFC Project Information and Data Portal; MIGA project pages |
| World Bank lists of fragile and conflict-affected situations, FY2018 to FY2025 | `1_concessionality/data/fcs_lists/FY18-FY25/p1.txt` to `p8.txt` (text of pages 1 to 8; p1 is FY2025 and p8 is FY2018) | Yes | World Bank, "FCS Lists from FY06 to FY25" |
| Scaling Solar tenders (Table 2) | `2_scaling_solar/table2_scaling_solar.csv` (entries of the table); `2_scaling_solar/sources.csv` (sources) | Table entries and source list | Sources listed in `2_scaling_solar/sources.csv` and in the note to Table 2 |
| Model parameters | none; the parameters are assumptions stated in Section 5.3 and recorded in the run manifests of `3_model/` | Not applicable | Not applicable |

**IDA PSW project list.** The list of PSW projects on the IDA website (https://ida.worldbank.org/en/financing/ida-private-sector-window/private-sector-window-projects) is populated by a public data source; the address of that data source is not recorded in this package. The snapshot used in the paper was retrieved on October 7, 2026 and holds 204 Board-approved transactions under IDA18 to IDA20, each with its Board date, country, region, IFC industry group, sector, instrument, allocation across the four PSW facilities, fragility designation, replenishment cycle and links to IFC and MIGA disclosure pages. A second export, retrieved on October 27, 2026, agrees with the first on the fragility designation and the Board date of all 204 transactions (`1_concessionality/output/rc04_final_spec/join_report.txt`). The text of the page retrieved on November 5, 2026 describes its table as listing Board-approved projects supported by IDA21, so that the IDA18 to IDA20 list may no longer be displayed there; the snapshot in this package is the record of the list used in the paper.

**IFC and MIGA disclosures.** The concessionality estimates were extracted on October 7, 2026 from the disclosure pages linked in the project list (https://disclosures.ifc.org and https://www.miga.org). Of 152 transactions with an IFC link, 151 pages were retrieved; all 34 MIGA pages were retrieved. Each estimate is stored with the sentence of the disclosure in which it appears, its denominator and, where reported, the project cost. A repeat harvest on November 3, 2026, run with the unmodified scripts of October 7, reproduced the extracted dataset exactly; `disclosure_pages_manifest.csv` lists the 178 page requests of that harvest (147 IFC and 30 MIGA pages stored, several pages shared by two or three transactions, one IFC request failed) with the address, retrieval time in UTC, status, size and SHA-256 checksum of each page. The pages may have changed since those dates.

**Lists of fragile and conflict-affected situations.** The text of the annual lists for FY2018 to FY2025 was taken from the World Bank's compilation of the lists from FY2006 to FY2025 (https://thedocs.worldbank.org/en/doc/b7176d1485821af6f7638e63e266c717-0090082025/original/FCSList-FY06toFY25.pdf). The paper's Table 1 codes fragility from the designation in the project list. The lists enter only the classification sensitivity described under "Differences between the package and the paper" below.

**Scaling Solar.** Table 2 audits eight procurement entries compiled from the announcements and reports cited in its note. No dataset underlies the table beyond those sources; `sources.csv` lists each source with its date and address, as recorded in the paper's bibliography. Two sources named in the table note have no bibliography entry: an IFC Scaling Solar presentation (May 2018) and the World Bank Zambia Implementation Completion Report (October 2020).

## Computational requirements

### Software

- Python 3.13. The package was verified with Python 3.13.18 on Linux; the shipped model results were produced with Python 3.13.16.
- Packages, with the versions used for verification, are listed in `requirements.txt`: numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, statsmodels 0.15.0, patsy 1.0.3 and pytest 9.1.1. The model component requires numpy and pytest only.
- No other software is required. The concessionality scripts of October 7, 2026 ran under library versions that were not recorded; the November 2026 reruns with the versions above reproduce their outputs byte for byte.

### Randomness

The model computes expectations exactly, by enumerating all 2^20 histories of the two-state revenue process; its results involve no random numbers. The probe of assumptions A2 and A4 (`probe_assumptions.py`) and several tests draw contract terms and paths at random, with seeds fixed in the code (`numpy.random.default_rng`). The concessionality regressions and their leave-one-out cross-validation are deterministic.

### Hardware and run time

The verification run used a Linux container with two processor cores. The model exercises use two worker processes. A full run of `run_all.py` took about 13 minutes, of which the model exercises took about 12; a quick run took about one and a half minutes. No process used more than about 320 MB of memory. The package occupies about 1.7 MB.

The package was not run on Windows or macOS. `run_all.py` uses only the Python standard library to drive the scripts and sets `PYTHONUTF8=1` for every script, because most scripts open files without naming an encoding; under a locale other than UTF-8, `merge_combined_corrected.py` otherwise fails to read `psw_data.json`. Text files written on Windows carry Windows line endings; the comparison in `run_all.py` reports such files as identical after line-ending normalization. `.gitattributes` keeps Git from converting line endings, so that the checksums of `MANIFEST.sha256` hold after a checkout on any platform.

## Description of the package

| Folder or file | Content |
|---|---|
| `run_all.py` | Driver: reruns every component, writes results under `_rerun/` and compares them with the shipped files |
| `requirements.txt` | Python packages and versions |
| `MANIFEST.sha256` | SHA-256 checksum of every file in the package; `tools/verify_manifest.py` checks it |
| `VERIFICATION.md` | Record of the verification of this version against the paper |
| `1_concessionality/` | Data, code and outputs for Table 1, the concessionality figures of Section 2 and Appendix E |
| `2_scaling_solar/` | Entries and sources of Table 2 |
| `3_model/` | The model component, version 2026-11-04a: contract implementation, exact solver, tests, exercises, results and table scripts |
| `4_paper_tables/` | Tables with the paper's labels and numbering, and the checks of the numbers stated in the text |
| `tools/` | Integrity check |
| `CITATION.cff`, `.zenodo.json` | Citation and deposit metadata |
| `LICENSE`, `LICENSE-DATA.md` | Licenses: MIT for the code; CC BY 4.0 for data, outputs and documentation |

### Concessionality component (`1_concessionality/code/`)

| Script | Role | Inputs | Outputs |
|---|---|---|---|
| `recovered/merge_combined_corrected.py` | Merges the IFC and MIGA extractions with the project list, one row per transaction | `frozen_2026-10-07/` | `combined_dataset.json`, `psw_concessionality_combined.csv` (identical to the frozen files) |
| `recovered/build_table1_concessionality.py` | Table 1 (Panel A) and a robustness panel (Panel B, not in the paper) that includes the ratio of the 90th to the 10th percentile | `frozen_2026-10-07/combined_dataset.json` | `output/table1/tab_concessionality_dispersion.tex` |
| `recovered/appendix_e_disclosure_rates.py` | Disclosure rates by fragility (Appendix E); writes to the screen | `frozen_2026-10-07/` | `output/appendix_e_disclosure_rates.txt` (the screen output) |
| `rc04/rc04_fragility_audit.py` | Codes each transaction from the World Bank list for the fiscal year of its Board approval | `registry_export_2026-10-27.csv`, `fcs_lists/FY18-FY25/` | `output/classification/` |
| `rc04/rc04_final_spec.py` | Reruns Table 1 and the Appendix E rates under the registry coding and under the list-based codings | `frozen_2026-10-07/`, `output/classification/rc04_fragility_by_transaction.csv` | `output/rc04_final_spec/` |
| `harvest_oct7/` | The original retrieval and extraction scripts of October 7, 2026 (IFC: `full_harvest.py`, `extract.py`, `build_full.py`, `finalize.py`; MIGA: `miga_harvest.py`, `miga_extract.py`) | live pages | the frozen extraction |

The three scripts in `recovered/` were recovered from the record of the October 7, 2026 session; the lines marked `ADAPTED` change input and output paths only, and the comment lines at the head of each script were revised for this package. Before any list-based coding is run, `rc04_final_spec.py` requires the registry coding to reproduce the published figures and stops if it does not (`output/rc04_final_spec/baseline_check.txt`). `output/live_harvest_2026-11-03/` holds the logs of the repeat harvest.

Three features of these scripts need to be known to read their outputs:

- **Sponsor groups.** The Sponsor column of Table 1 holds out all transactions of a sponsor together. `build_table1_concessionality.py` defines the groups by tokens in the project names: NMB Tanzania (3 transactions), KICB Kyrgyz (2), ACEP (2) and a Sonatel group of 4 that includes the transactions named Orange (Orange Mali and RSF Orange Bank). Every other transaction forms its own group.
- **Superseded rates in the merge log.** `merge_combined_corrected.py` prints disclosure rates on retrieved pages of 68 and 75 percent. Their denominators read the page field of the merged row, which omits transactions whose MIGA page was retrieved when the merged row kept the IFC record; a note at the end of the script records that they are superseded. The rates of Appendix E (58 and 70 percent) come from `appendix_e_disclosure_rates.py`, whose column headed "pages" counts transactions with at least one retrieved page (182 in all).
- **Table notes.** The notes written by `build_table1_concessionality.py` are those of October 7, 2026; the paper's notes to Table 1 were rewritten later and differ in wording (for example, the paper does not read a prediction-error factor of 2.0 as prediction to within a factor of two). The numbers of Panel A are those of the paper.

### Model component (`3_model/`)

The files in `3_model/` are byte-identical to the corresponding files of the frozen archive `lpvs_tractability_2026-11-04a.zip` (SHA-256 `f978159c69434146fd94a986ec6f8cba90cba1ce643a809fbb98226f2954012d`), whose manifest is `3_model/manifest_all.json`; Appendix B of the paper describes this version. Working notes and superseded table files of the archive are not included; `tools/verify_manifest.py` lists them. `3_model/CHANGES_2026-11-04.md` records the changes from the previous version, none of which alters a computed result; the archive checksum file and the reconciliation record that it cites are not part of the package.

| Script | Role | Outputs |
|---|---|---|
| `lpvs_core.py` | Contract (Section 4, equations 1 to 3) and exact solver: ledger, settlement, stopping rules, optimal exit, payoff and minimum acceptable cap | imported by the other scripts |
| `test_lpvs_core.py`, `test_c4.py`, `test_c4_sequential.py` | 44 tests (31, 9 and 4) | test log |
| `run_tractability.py` | Participation exercises A and B (Section 5.3), run with `L_EXIT=0` (costless exit) and `L_EXIT=-2` (termination penalty) | `results_L0/`, `results_Lm2/` |
| `probe_assumptions.py` | Probe of assumptions A2 and A4 (Appendix B) | `results_probes.json` |
| `c3_selection.py` | Types, second-price award, selection and exit ordering (Sections 6.2 and 6.3, Appendices A and C) | `results_c3/` |
| `c3_exit_diagnostic.py` | Dates of violations of the exit ordering (Appendix A) | `results_c3/c3_exit_violation_dates.csv` |
| `c4_posted_offer.py`, `c4_sequential.py` | Single offer, sequential offers and auction (Section 6.4) | `results_c4/` |
| `make_tables.py`, `c3_tables.py`, `c4_tables.py` | Tables | `tables_numerical.tex`, `c3_tables_main.tex`, `c3_tables_appendix.tex`, `c4_tables_main.tex`, `c4_tables_appendix.tex` |

Each results folder holds a run manifest with the code hashes, software versions and assumptions of the run.

### Paper tables and text checks (`4_paper_tables/`)

`paper_tables.py` writes Tables 4, 5 and 6 and Tables D1 to D18 from the outputs of the model component, with the labels the paper uses and in the order of Appendix D. Table 6 is the two-sponsor subset of Table D10, without its Surplus column. `fmt.py` rounds half up at the printed precision after removing floating-point noise, so that exact halves such as 0.9375 and 18.75 print as 0.938 and 18.8. `check_paper_tables.py` compares the numbers of each generated table, and of Panel A of Table 1, with the table of the same label in the paper's LaTeX source; its map translates the label of Table 1 (`tab:concessionality-dispersion` in the package, `tab:concessionality` in the paper). The scripts in `checks/` recompute the numbers stated in the text:

| Script | Statements checked |
|---|---|
| `checks/trace_concessionality_text.py` | Section 2, the note to Table 1 and Appendix E (28 statements) |
| `checks/check_scaling_solar.py` | Section 2 and the note to Table 2 (6 statements) |
| `checks/check_worked_examples.py` | The worked example of Section 4 and the counterexample with recovery in Appendix A (6 statements) |
| `checks/trace_text.py` | Sections 5.3, 6.3, 6.4 and 8.1, Appendix A and Appendix C, from the model results (86 statements) |
| `checks/trace_text2.py` | The Table 6 cells cited in Section 6.4 and the share comparison of Appendix C, recomputed from the results; and the presence of the seven values of the example of the introduction and Section 6.2 in the paper's Table 5, which `reconcile.py` compares with the package (requires the paper source) |
| `checks/reconcile.py`, `checks/table6.py` | Token-by-token comparison of Tables 4, 5 and D1 to D18 with the tables written by the model scripts, and cell-by-cell comparison of Table 6 with Table D10 (requires the paper source) |

The first four checks read only the package; their claims are written into the scripts as printed in the paper of November 4, 2026. The last three, and `check_paper_tables.py`, read the paper's LaTeX source, which is not part of the package. The shipped results are in `4_paper_tables/output/`: the trace files at its top level and the comparison with the paper of November 4, 2026 (MD5 of the source `7b4aa5abc8d903c179967a46396570bf`) in `4_paper_tables/output/comparison_with_paper/`.

## Instructions to replicators

The commands below use `python`; on systems where Python 3 is installed as `python3`, use that name.

1. Install Python 3.13 and the packages: `python -m pip install -r requirements.txt`.
2. From the package root, run `python run_all.py`. For a run that formats the model tables from the shipped results without rerunning the exercises, run `python run_all.py --quick`.
3. Read `_rerun/SUMMARY.txt`. Its first line after the header reports the integrity check against `MANIFEST.sha256`. Every following line should read "identical", "identical after line-ending normalization" or, for the run manifests of the model, a statement that the code hashes, assumptions and checks are identical; run time, interpreter version and platform differ by construction, and two manifests also list other files present in the folder when the script ran. The script exits with status 0 when no file differs.
4. With the LaTeX source of the paper, `python run_all.py --paper PATH_TO/revealing_the_subsidy.tex` also compares every generated table and the statements traced by `trace_text2.py` with the paper, and adds the results to the end of `SUMMARY.txt`.

**Running the scripts without the driver.** The scripts can be run one by one, from a copy of the package, in the order of `run_all.py`. Four points matter:

- Set the environment variable `PYTHONUTF8=1` (Windows: `set PYTHONUTF8=1`; Linux and macOS: `export PYTHONUTF8=1`).
- Several scripts write to their input folder by default. `merge_combined_corrected.py` and `build_table1_concessionality.py` take an optional second argument for the output folder and otherwise write into `data/frozen_2026-10-07/`; `rc04_fragility_audit.py` and `rc04_final_spec.py` take the output folder as their last argument, and `rc04_fragility_audit.py` requires that folder to exist; `appendix_e_disclosure_rates.py` writes to the screen only.
- The model scripts write into the folder from which they run, so that a run in `3_model/` itself replaces the shipped results. `run_all.py` therefore copies the code to `_rerun/3_model/` and runs it there. `run_tractability.py` reads the environment variables `OUT_DIR` and `L_EXIT` (`OUT_DIR=results_L0 L_EXIT=0.0` and `OUT_DIR=results_Lm2 L_EXIT=-2.0`); `make_tables.py` takes the two results folders as arguments.
- `paper_tables.py` takes the model folder and an output folder as arguments; by default it writes into `4_paper_tables/output/paper_tables/`.

**Repeating the harvest of the disclosure pages (optional).** The scripts in `1_concessionality/code/harvest_oct7/` retrieve the IFC and MIGA pages from the addresses in the project list. They expect a working folder that holds `raw/psw_data.json`, a `scripts/` folder with the six scripts, and the folders `pages/` (IFC) and `miga_pages/` (MIGA), and they run in the order `full_harvest.py`, `build_full.py`, `finalize.py`, `miga_harvest.py`, `miga_extract.py`, followed by `recovered/merge_combined_corrected.py`. The pages may have changed since October and November 2026, so that a new harvest tests the stability of the disclosures as well as the extraction. The repeat harvest was not part of the verification of this version.

## List of tables and programs

Paper labels are those of the LaTeX source; the files in `4_paper_tables/output/paper_tables/` carry them. The table scripts of `3_model/` write the same tables under the labels in the last column.

| Exhibit | Paper label | Program | Output in the package | Label in `3_model/` output |
|---|---|---|---|---|
| Table 1 | `tab:concessionality` | `1_concessionality/code/recovered/build_table1_concessionality.py` | `1_concessionality/output/table1/tab_concessionality_dispersion.tex` (Panel A) | `tab:concessionality-dispersion` |
| Table 2 | `tab:scaling_solar` | none (compilation) | `2_scaling_solar/table2_scaling_solar.csv` | not applicable |
| Table 3 | `tab:lpvr_lpvs_comparison` | none (analytical) | not applicable | not applicable |
| Table 4 | `tab:c1B` | `3_model/run_tractability.py` (`L_EXIT=0`), `make_tables.py` | `paper_tables/tab_c1_B.tex`; `3_model/tables_numerical.tex` | `tab:B` |
| Table 5 | `tab:c3example` | `3_model/c3_selection.py`, `c3_tables.py` | `paper_tables/tab_c3_example.tex`; `3_model/c3_tables_main.tex` | `tab:c3example` |
| Table 6 | `tab:c4compact` | `3_model/c4_posted_offer.py`, `c4_sequential.py`; `4_paper_tables/paper_tables.py` | `paper_tables/tab_c4_compact.tex` | none (subset of `tab:c4opp`) |
| Table 7 | `tab:scope_conditions` | none (analytical) | not applicable | not applicable |
| Table D1 | `tab:c1A` | `run_tractability.py` (`L_EXIT=0`), `make_tables.py` | `paper_tables/appendix_tables.tex`; `3_model/tables_numerical.tex` | `tab:A` |
| Table D2 | `tab:c1C` | `run_tractability.py` (`L_EXIT=0`), `make_tables.py` | same | `tab:C` |
| Table D3 | `tab:c1B0` | `run_tractability.py` (`L_EXIT=-2`), `make_tables.py` | same | `tab:B0` |
| Table D4 | `tab:c3types` | `c3_selection.py`, `c3_tables.py` | `paper_tables/appendix_tables.tex`; `3_model/c3_tables_main.tex` | `tab:c3types` |
| Table D5 | `tab:c3award` | `c3_selection.py`, `c3_tables.py` | same | `tab:c3auction` |
| Table D6 | `tab:c3oper` | `c3_selection.py`, `c3_tables.py` | same | `tab:c3oper` |
| Table D7 | `tab:c3pool` | `c3_selection.py`, `c3_tables.py` | `paper_tables/appendix_tables.tex`; `3_model/c3_tables_appendix.tex` | `tab:c3design` |
| Table D8 | `tab:c3select_awarded` | `c3_selection.py`, `c3_tables.py` | same | `tab:c3select` |
| Table D9 | `tab:c3select_common` | `c3_selection.py`, `c3_tables.py` | same | `tab:c3selectvbar` |
| Table D10 | `tab:c4peropp` | `c4_posted_offer.py`, `c4_sequential.py`, `c4_tables.py` | `paper_tables/appendix_tables.tex`; `3_model/c4_tables_main.tex` | `tab:c4opp` |
| Table D11 | `tab:c4cond` | same | same | `tab:c4award` |
| Table D12 | `tab:c4access` | same | same | `tab:c4ar` |
| Table D13 | `tab:c4decomp` | same | same | `tab:c4dec` |
| Table D14 | `tab:c4peropp_pen` | `c4_posted_offer.py`, `c4_sequential.py`, `c4_tables.py` | `paper_tables/appendix_tables.tex`; `3_model/c4_tables_appendix.tex` | `tab:c4opppen` |
| Table D15 | `tab:c4cond_pen` | same | same | `tab:c4awardpen` |
| Table D16 | `tab:c4access_pen` | same | same | `tab:c4arpen` |
| Table D17 | `tab:c4decomp_pen` | same | same | `tab:c4decpen` |
| Table D18 | `tab:c4monotone` | same | same | `tab:c4mono` |
| Appendix B: tests and probes | | `3_model/test_*.py`; `probe_assumptions.py` | `3_model/results_probes.json` | |
| Appendix A: exit ordering | | `3_model/c3_selection.py`, `c3_exit_diagnostic.py` | `3_model/results_c3/c3_exit_ordering.csv`, `c3_exit_violation_dates.csv` | |
| Appendix E: counts and disclosure rates | | `1_concessionality/code/recovered/merge_combined_corrected.py`, `appendix_e_disclosure_rates.py` | `1_concessionality/output/appendix_e_disclosure_rates.txt`; `4_paper_tables/output/trace_concessionality_text.csv` | |
| Numbers stated in the text | | `4_paper_tables/checks/` | `4_paper_tables/output/trace_*.csv`; `4_paper_tables/output/comparison_with_paper/` | |

In this table, `paper_tables/` stands for `4_paper_tables/output/paper_tables/`. Script names in rows D1 to D18 refer to `3_model/`.

## Differences between the package and the paper

- **Fragility coding of Table 1.** The paper's Table 1 and Appendix E code fragility from the designation in the project list. `rc04_final_spec.py` also reports the regressions and disclosure rates with fragility coded from the World Bank list for the fiscal year of each transaction's Board approval, under several treatments of multi-country transactions (`output/rc04_final_spec/rc04_table1_final_spec.csv`, `rc04_appendixE_final_spec.csv`); the paper does not report them. Where all 92 transactions are kept, these codings leave rows 1 to 4 of Table 1 unchanged and move the reduction in prediction error of row 5 to between 14.3 and 16.0 percent (15.6 percent under the registry coding) and that of row 6 to between 21.0 and 22.3 percent (22.3 percent). Excluding multi-country transactions reduces the sample to 79 transactions in rows 1 to 5.
- **Ranges in the disclosures.** Appendix E states that one disclosure provides a range. Three extracted estimates carry a range; two of them, CRRH II and Robust Nigeria, appear inside square brackets, which Appendix E describes separately as bracketed values (`trace_concessionality_text.csv`, statement E17).
- **Material not included.** The package contains no code or data for analyses that earlier drafts of the paper contained and the present version does not, such as forecast errors of the IMF World Economic Outlook and Monte Carlo comparisons of bilateral and competitive allocation. No exhibit of the paper depends on them.

## References

Bibliographic details of every source cited above are in the paper's reference list.

- International Development Association, World Bank. "IDA PSW Projects." https://ida.worldbank.org/en/financing/ida-private-sector-window/private-sector-window-projects. Snapshot retrieved October 7, 2026; export retrieved October 27, 2026.
- International Finance Corporation. Project Information and Data Portal. https://disclosures.ifc.org. Pages retrieved October 7 and November 3, 2026.
- Multilateral Investment Guarantee Agency. Project pages. https://www.miga.org. Pages retrieved October 7 and November 3, 2026.
- World Bank. "FCS Lists from FY06 to FY25." https://thedocs.worldbank.org/en/doc/b7176d1485821af6f7638e63e266c717-0090082025/original/FCSList-FY06toFY25.pdf.
