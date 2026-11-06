# Recovered 2026-11-02 from the record of the working session of October 7, 2026 (turn 128, 2026-10-07 ~15:00 ET; the record is not public).
# Comment lines revised 2026-11-05 for the replication package; the code is unchanged.
# Originally run inline as `python3 -I - << 'PYEOF'` and never saved as a file.
# This is the merge that produced the corrected 204-row combined_dataset.json and
# psw_concessionality_combined.csv. An earlier script of October 7, build_table16.py (not included), keyed the merge on
# project name and yielded 203 rows (the Tulu Moye defect).
# Body copied verbatim. Lines marked ADAPTED change input/output paths only.
import json,os,csv,collections
import sys                                                             # ADAPTED
P=sys.argv[1]                                                          # ADAPTED: was the 2026-10-07 session scratchpad path
OUT=sys.argv[2] if len(sys.argv)>2 else P                              # ADAPTED: write outputs elsewhere so they can be diffed
REG=P+'/raw/psw_data.json' if os.path.exists(P+'/raw/psw_data.json') else P+'/psw_data.json'  # ADAPTED: bundle stores the registry at top level
os.makedirs(OUT,exist_ok=True)                                         # ADAPTED
reg=json.load(open(REG))                                               # ADAPTED (was P+'/raw/psw_data.json')
ifc=json.load(open(P+'/final_dataset.json'))
mig=json.load(open(P+'/miga_results.json'))
for r in ifc: r['agency']='IFC'
# key on (ProjName, cycle, MIGA url) — registry order is preserved in both lists
migmap={}
for r in mig:
    migmap[(r['ProjName'],r.get('ReplenishmentCode'),r.get('url'))]=r
merged=[]
for i,r in enumerate(ifc):
    reg_row=reg[i]
    k=(r['ProjName'],r.get('ReplenishmentCode'),reg_row.get('MIGADisclosure1'))
    m=migmap.get(k)
    if m is not None and m.get('concessionality_pct') is not None and r.get('concessionality_pct') is None:
        mm=dict(m); mm['agency']='MIGA'; merged.append(mm)
    else:
        merged.append(r)
assert len(merged)==len(reg), (len(merged),len(reg))
json.dump(merged,open(OUT+'/combined_dataset.json','w'),indent=1)   # ADAPTED: OUT
cols=['agency','ProjName','Country','Region','FCS/FCV','ReplenishmentCode','Facility','Instrument','Industry','Sector','BoardDate','PSWSupport','RMF','BFF','MGF','LCF','concessionality_pct','conc_low','conc_high','is_range','is_upper_bound','guarantee_years','denominator_type','denominator_text','project_cost_musd','page','url','sentence']
with open(OUT+'/psw_concessionality_combined.csv','w',newline='') as f:  # ADAPTED: OUT
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader()
    for r in sorted(merged,key=lambda z:(z.get('ReplenishmentCode') or '',z['ProjName'])): w.writerow(r)
ok=[r for r in merged if r.get('concessionality_pct') is not None]
print('rows',len(merged),'| with figure',len(ok),'| IFC',sum(1 for r in ok if r['agency']=='IFC'),'MIGA',sum(1 for r in ok if r['agency']=='MIGA'))
tpc=[r for r in ok if r.get('denominator_type')=='total project cost']
print('tpc',len(tpc),'| IFC tpc',sum(1 for r in tpc if r['agency']=='IFC'))
print()
print('=== FCS reconciliation (correct denominators) ===')
regf=collections.Counter(r['FCS/FCV'] for r in reg)
print('registry:',dict(regf))
# denominator restricted to transactions with a retrievable disclosure page
elig=[r for r in merged if r.get('page')=='fetched']
print('with a retrieved disclosure page:',dict(collections.Counter(r['FCS/FCV'] for r in elig)))
okf=collections.Counter(r['FCS/FCV'] for r in ok)
print('with a figure:',dict(okf))
for g in ['FCS','non-FCS']:
    n_e=sum(1 for r in elig if r['FCS/FCV']==g); n_o=okf[g]
    print(f'  {g}: {n_o}/{n_e} of retrieved pages = {100*n_o/n_e:.0f}% ; {n_o}/{regf[g]} of registry = {100*n_o/regf[g]:.0f}%')
print()
print('=== facility composition of the 92 IFC tpc observations ===')
itpc=[r for r in tpc if r['agency']=='IFC']
print(dict(collections.Counter(r['Facility'] for r in itpc)))
print('single-facility BFF+LCF =',sum(1 for r in itpc if r['Facility'] in ('BFF','LCF')),'| mixed =',sum(1 for r in itpc if r['Facility'] not in ('BFF','LCF')))
# NOTE (2026-11-02): the "retrieved disclosure page" counts printed above use the merged row's
# page field and were superseded in turn 130 (they miss MIGA-retrieved transactions whose
# merged row kept the IFC record). Appendix E's 182 comes from appendix_e_disclosure_rates.py.
