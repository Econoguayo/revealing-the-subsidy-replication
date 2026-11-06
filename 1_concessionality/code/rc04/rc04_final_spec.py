"""RC-04 reruns of the concessionality exhibit under official fragility codings.

Written 2026-11-02. New code, not recovered. It re-implements the Table 1 computation of
recovered/build_table1_concessionality.py (same filters, regressors, sponsor groups and
cross-validation) and the Appendix E rates of recovered/appendix_e_disclosure_rates.py, then
reruns both with the registry's fragility field replaced by codings built from the official
World Bank FCS lists (rc04_fragility_by_transaction.csv, from rc04_fragility_audit.py).

Before any alternative coding is run, the script requires the registry coding to reproduce
the published figures; it stops if it does not.

Usage:
  python3 -I rc04_final_spec.py BUNDLE_DIR RC04_CSV OUT_DIR
    BUNDLE_DIR  the frozen extraction of October 7, 2026 (data/frozen_2026-10-07/ in the replication package)
    RC04_CSV    rc04_fragility_by_transaction.csv
    OUT_DIR     where results are written

Codings (fragility is a binary FCS / non-FCS label in every case):
  registry        the registry field FCS/FCV in the October 7 snapshot (published basis)
  labelled_M*     single-country transactions take the list labelled for the Board fiscal year
  in_force_M*     single-country transactions take the list in force at Board approval
                  (FY2019 list for FY2020 approvals; Jones et al. 2024, p. 12, fn. 4)
  multi-country transactions (D-4b):
    M1  keep the registry value
    M2  FCS if any named country is on the relevant list, otherwise non-FCS
    M3  exclude multi-country transactions from the sample
"""
import json, math, re, os, sys
import numpy as np, pandas as pd, statsmodels.formula.api as smf

BUNDLE, RC04, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
REG = BUNDLE + '/raw/psw_data.json' if os.path.exists(BUNDLE + '/raw/psw_data.json') else BUNDLE + '/psw_data.json'
reg = json.load(open(REG))
ifc = json.load(open(BUNDLE + '/final_dataset.json'))
comb = json.load(open(BUNDLE + '/combined_dataset.json'))
mig = {}
for r in json.load(open(BUNDLE + '/miga_results.json')):
    mig[(r['ProjName'], r.get('ReplenishmentCode'), r.get('url'))] = r
assert len(reg) == len(ifc) == len(comb) == 204, (len(reg), len(ifc), len(comb))

# ---------- one row per registry transaction, registry order ----------
base = []
for i, r in enumerate(reg):
    c = comb[i]
    assert c['ProjName'] == r['ProjName'], (i, c['ProjName'], r['ProjName'])
    m = mig.get((r['ProjName'], r['ReplenishmentCode'], r.get('MIGADisclosure1')))
    base.append({
        'i': i, 'ProjName': r['ProjName'], 'ReplenishmentCode': r['ReplenishmentCode'],
        'Country': r['Country'], 'BoardDate_oct7': r.get('BoardDate'), 'fcs_oct7': r['FCS/FCV'],
        'any_page': (ifc[i].get('page') == 'fetched') or (bool(m) and m.get('page') == 'fetched'),
        'fig': c.get('concessionality_pct') is not None,
        'agency': c.get('agency'), 'conc': c.get('concessionality_pct'),
        'denominator_type': c.get('denominator_type'), 'Facility': c.get('Facility'),
        'Industry': c.get('Industry'), 'cost': c.get('project_cost_musd')})
B = pd.DataFrame(base)
B['in92'] = B.fig & (B.denominator_type == 'total project cost') & (B.agency == 'IFC')

# ---------- join the official codings ----------
A = pd.read_csv(RC04)
J = B.merge(A, on=['ProjName', 'ReplenishmentCode'], how='left', indicator=True, suffixes=('', '_oct27'))
unmatched = J[J._merge != 'both']
with open(OUT + '/join_report.txt', 'w') as f:
    f.write(f'registry rows (Oct 7 snapshot): {len(B)}; matched to rc04 on name and cycle: {(J._merge=="both").sum()}\n')
    for _, r in unmatched.iterrows():
        f.write(f'  UNMATCHED: {r.ProjName} | {r.ReplenishmentCode} | {r.Country}\n')
    d = J[(J._merge == 'both') & (J.fcs_oct7 != J['FCS/FCV'])]
    f.write(f'fragility field differs between Oct 7 snapshot and Oct 27 export: {len(d)}\n')
    for _, r in d.iterrows():
        f.write(f'  {r.ProjName} | {r.Country} | Oct 7: {r.fcs_oct7} | Oct 27: {r["FCS/FCV"]}\n')
    d7 = pd.to_datetime(J.BoardDate_oct7, errors='coerce').dt.date; d27 = pd.to_datetime(J.board_date, errors='coerce').dt.date
    bd = J[(J._merge == 'both') & (d7 != d27)]
    f.write(f'Board date differs between snapshots: {len(bd)}\n')
    for _, r in bd.iterrows():
        f.write(f'  {r.ProjName} | Oct 7: {r.BoardDate_oct7} | Oct 27: {r.board_date}\n')
if len(unmatched):
    print(open(OUT + '/join_report.txt').read())
    sys.exit('Stopping: every registry transaction must match before codings are compared.')

lab = lambda x: 'FCS' if x == 1 else 'non-FCS'
CODINGS = {'registry': J.fcs_oct7.copy()}
for basis, single_col, multi_col in [('labelled', 'labelled_fy_fcs', 'any_listed_labelled'),
                                     ('in_force', 'in_force_fcs', 'any_listed_in_force')]:
    sc = J.single_country == 1
    single = J[single_col].map(lambda v: lab(int(v)) if pd.notna(v) else None)
    m1 = np.where(sc, single, J.fcs_oct7)
    m2 = np.where(sc, single, J[multi_col].map(lambda v: lab(int(v))))
    m3 = np.where(sc, single, None)
    CODINGS[f'{basis}_M1'] = pd.Series(m1, index=J.index)
    CODINGS[f'{basis}_M2'] = pd.Series(m2, index=J.index)
    CODINGS[f'{basis}_M3'] = pd.Series(m3, index=J.index)

for basis, single_col in [('labelled', 'labelled_fy_fcs'), ('in_force', 'in_force_fcs')]:
    sc = J.single_country == 1
    single = J[single_col].map(lambda v: lab(int(v)) if pd.notna(v) else None)
    CODINGS[f'{basis}_3cat'] = pd.Series(np.where(sc, single, 'multi-country'), index=J.index)

# ---------- Table 1, same computation as build_table1_concessionality.py ----------
SPON = [('nmb', 'NMB Tanzania', 'Tanzania'), ('kicb', 'KICB Kyrgyz', 'Kyrgyz'), ('sonatel', 'Sonatel group', None),
        ('acep', 'ACEP', None), ('orange', 'Sonatel group', None)]
def grp(r):
    n = r['name'].lower()
    for tok, lb, cty in SPON:
        if re.search(r'\b' + tok, n) and (cty is None or cty.lower() in r['cty'].lower()): return lb
    return 'solo::' + r['name']
def cv(sub, f, by):
    e = []; dropped = 0
    for k in sub[by].unique():
        tr = sub[sub[by] != k]; te = sub[sub[by] == k]
        try: p = smf.ols(f, data=tr).fit().predict(te)
        except Exception:
            dropped += len(te); continue
        for a, b in zip(te.lc.values, p.values):
            if not np.isnan(b): e.append(a - b)
            else: dropped += 1
    return math.sqrt(np.mean(np.array(e) ** 2)), dropped
SPECS = [('None (unconditional)', 'lc ~ 1'), ('Facility', 'lc ~ C(fac2)'), ('Facility, industry', 'lc ~ C(fac2)+C(ind2)'),
         ('Facility, industry, cycle', 'lc ~ C(fac2)+C(ind2)+C(cycle)'),
         ('Facility, industry, cycle, fragility', 'lc ~ C(fac2)+C(ind2)+C(cycle)+C(fcs)')]
def table1(fcs):
    S = J[J.in92].copy(); S['fcs'] = fcs[S.index]; S = S[S.fcs.notna()].copy()
    df = pd.DataFrame({'conc': S.conc.astype(float), 'fac': S.Facility, 'ind': S.Industry, 'cycle': S.ReplenishmentCode,
                       'fcs': S.fcs, 'cost': pd.to_numeric(S.cost), 'name': S.ProjName, 'cty': S.Country}).reset_index(drop=True)
    df['fac2'] = df.fac.apply(lambda s: 'BFF' if s == 'BFF' else ('LCF' if s == 'LCF' else 'mixed'))
    df['ind2'] = df.ind.str.split('/').str[0].str.strip().str[:22]; df['lc'] = np.log(df.conc); df['rowid'] = range(len(df))
    df['grp'] = df.apply(grp, axis=1)
    out = []; b1 = None
    for lb, f in SPECS:
        m = smf.ols(f, data=df).fit(); (r1, d1), (r2, d2) = cv(df, f, 'rowid'), cv(df, f, 'grp')
        if b1 is None: b1 = r1
        fc = [k for k in m.params.index if k.startswith('C(fcs)')]; jt = (m.f_test(' , '.join(f'{k} = 0' for k in fc)).pvalue if fc else np.nan); allc = '; '.join(f'{k.split(chr(91))[1][:-1]}={m.params[k]:.3f} (p={m.pvalues[k]:.2f})' for k in fc)
        out.append(dict(row=lb, n=int(m.nobs), r2=m.rsquared, adj_r2=m.rsquared_adj, resid_factor=math.exp(np.sqrt(m.mse_resid)),
                        pe_txn=math.exp(r1), pe_sponsor=math.exp(r2), reduction=100 * (1 - r1 / b1),
                        loo_dropped_txn=d1, loo_dropped_sponsor=d2, n_fcs=int((df.fcs == 'FCS').sum()),
                        fcs_coef=(m.params[fc[0]] if fc else np.nan), fcs_term=(fc[0] if fc else ''),
                        fcs_p=(m.pvalues[fc[0]] if fc else np.nan), joint_p=float(jt), all_terms=allc, n_multi=int((df.fcs=='multi-country').sum())))
    sub = df.dropna(subset=['cost']).copy(); sub['lcost'] = np.log(sub.cost)
    f = 'lc ~ C(fac2)+C(ind2)+C(cycle)+C(fcs)+lcost'
    m = smf.ols(f, data=sub).fit(); (r1, d1), (r2, d2) = cv(sub, f, 'rowid'), cv(sub, f, 'grp'); rb, _ = cv(sub, 'lc ~ 1', 'rowid')
    fc = [k for k in m.params.index if k.startswith('C(fcs)')]; jt = (m.f_test(' , '.join(f'{k} = 0' for k in fc)).pvalue if fc else np.nan); allc = '; '.join(f'{k.split(chr(91))[1][:-1]}={m.params[k]:.3f} (p={m.pvalues[k]:.2f})' for k in fc)
    out.append(dict(row='Adding log project cost', n=int(m.nobs), r2=m.rsquared, adj_r2=m.rsquared_adj,
                    resid_factor=math.exp(np.sqrt(m.mse_resid)), pe_txn=math.exp(r1), pe_sponsor=math.exp(r2),
                    reduction=100 * (1 - r1 / rb), loo_dropped_txn=d1, loo_dropped_sponsor=d2, n_fcs=int((sub.fcs == 'FCS').sum()),
                    fcs_coef=(m.params[fc[0]] if fc else np.nan), fcs_term=(fc[0] if fc else ''),
                    fcs_p=(m.pvalues[fc[0]] if fc else np.nan), joint_p=float(jt), all_terms=allc, n_multi=int((df.fcs=='multi-country').sum()), benchmark=math.exp(rb)))
    return pd.DataFrame(out)
def rates(fcs):
    S = J.copy(); S['fcs'] = fcs; S = S[S.fcs.notna()]
    o = {}
    for g in ['FCS', 'non-FCS', 'multi-country']:
        x = S[S.fcs == g]
        if len(x)==0: continue
        o[g] = dict(fig=int(x.fig.sum()), pages=int(x.any_page.sum()), total=len(x),
                    rate_pages=100 * x.fig.sum() / x.any_page.sum(), rate_registry=100 * x.fig.sum() / len(x))
    return o

# ---------- published targets (October 20, 2026 build) ----------
PUB = [(92, .000, .000, 2.46, 2.47, 2.47, 0.0), (92, .318, .303, 2.12, 2.15, 2.15, 15.6),
       (92, .409, .375, 2.04, 2.10, 2.10, 18.3), (92, .410, .361, 2.05, 2.13, 2.13, 16.6),
       (92, .413, .356, 2.06, 2.15, 2.15, 15.6), (79, .555, .497, 1.95, 2.08, 2.09, 22.3)]
base_t = table1(CODINGS['registry']); base_r = rates(CODINGS['registry'])
fails = []
for (_, r), p in zip(base_t.iterrows(), PUB):
    got = (r.n, round(r.r2, 3), round(r.adj_r2, 3), round(r.resid_factor, 2), round(r.pe_txn, 2), round(r.pe_sponsor, 2), round(r.reduction, 1))
    if got != p: fails.append((r.row, got, p))
for g, (fig, pg, tot, rp, rr) in {'FCS': (39, 67, 70, 58, 56), 'non-FCS': (80, 115, 134, 70, 60)}.items():
    b = base_r[g]
    got = (b['fig'], b['pages'], b['total'], round(b['rate_pages']), round(b['rate_registry']))
    if got != (fig, pg, tot, rp, rr): fails.append(('Appendix E ' + g, got, (fig, pg, tot, rp, rr)))
with open(OUT + '/baseline_check.txt', 'w') as f:
    f.write('Registry coding against the published Table 1 and Appendix E figures\n')
    f.write('PASS\n' if not fails else 'FAIL\n' + '\n'.join(f'  {a}: got {b}, published {c}' for a, b, c in fails) + '\n')
    f.write(base_t.to_string() + '\n')
print(open(OUT + '/baseline_check.txt').read())
if fails: sys.exit('Stopping: the registry coding does not reproduce the published figures.')

# ---------- alternative codings ----------
T = []; R = []
for name, fcs in CODINGS.items():
    t = table1(fcs); t.insert(0, 'coding', name); T.append(t)
    for g, v in rates(fcs).items(): R.append(dict(coding=name, group=g, **v))
T = pd.concat(T); R = pd.DataFrame(R)
T.to_csv(OUT + '/rc04_table1_final_spec.csv', index=False); R.to_csv(OUT + '/rc04_appendixE_final_spec.csv', index=False)

# ---------- which transactions change label, and where they sit ----------
ch = []
for name, fcs in CODINGS.items():
    if name == 'registry': continue
    diff = J[(fcs != J.fcs_oct7) & fcs.notna()]
    for _, r in diff.iterrows():
        ch.append(dict(coding=name, ProjName=r.ProjName, Country=r.Country, board_date=r.board_date,
                       registry=r.fcs_oct7, official=fcs[r.name], single_country=int(r.single_country),
                       in_table1_sample=bool(r.in92), discloses_estimate=bool(r.fig), retrieved_page=bool(r.any_page)))
pd.DataFrame(ch).to_csv(OUT + '/rc04_label_changes_final_spec.csv', index=False)
pd.set_option('display.width', 220)
print(T[T.row.str.contains('fragility|project cost')][['coding','row','n','n_fcs','n_multi','pe_txn','pe_sponsor','reduction','joint_p','all_terms']].round(3).to_string(index=False))
print(R.round(1).to_string(index=False))
