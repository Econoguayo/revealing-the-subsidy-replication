# Recovered 2026-11-02 from the record of the working session of October 7, 2026 (turn 130, 2026-10-07 ~15:10 ET; the record is not public).
# Comment lines revised 2026-11-05 for the replication package; the code is unchanged.
# Originally run inline as `python3 -I -c "..."` (tool description: "Produce the corrected
# coverage table with an explicit unit and inclusion rule"); never saved as a file.
# Source of the Appendix E figures: 182 transactions with a retrieved disclosure;
# FCS 39/67 = 58 percent, non-FCS 80/115 = 70 percent; registry 39/70 = 56, 80/134 = 60.
# Body copied verbatim (shell escaping removed). Lines marked ADAPTED change paths only.
import json,collections
import os,sys                                                          # ADAPTED
P=sys.argv[1]                                                          # ADAPTED: was the 2026-10-07 session scratchpad path
REG=P+'/raw/psw_data.json' if os.path.exists(P+'/raw/psw_data.json') else P+'/psw_data.json'  # ADAPTED
reg=json.load(open(REG))                                               # ADAPTED (was '$P/raw/psw_data.json')
ifc=json.load(open(P+'/final_dataset.json'))
mig={}
for r in json.load(open(P+'/miga_results.json')): mig[(r['ProjName'],r.get('ReplenishmentCode'),r.get('url'))]=r
comb=json.load(open(P+'/combined_dataset.json'))
rows=[]
for i,r in enumerate(reg):
    m=mig.get((r['ProjName'],r['ReplenishmentCode'],r.get('MIGADisclosure1')))
    rows.append({'fcs':r['FCS/FCV'],'any':(ifc[i].get('page')=='fetched') or (bool(m) and m.get('page')=='fetched'),
                 'fig':comb[i].get('concessionality_pct') is not None})
print('Disclosure rate, conditional on at least one disclosure page being retrieved')
print(f"{'group':10s} {'figure':>7s} {'pages':>7s} {'rate':>7s} {'registry':>9s} {'reg rate':>9s}")
for g in ['FCS','non-FCS']:
    fig=sum(1 for x in rows if x['fcs']==g and x['fig']); pg=sum(1 for x in rows if x['fcs']==g and x['any']); tot=sum(1 for x in rows if x['fcs']==g)
    print(f'{g:10s} {fig:7d} {pg:7d} {100*fig/pg:6.0f}% {tot:9d} {100*fig/tot:8.0f}%')
fig=sum(1 for x in rows if x['fig']); pg=sum(1 for x in rows if x['any'])
print(f"{'All':10s} {fig:7d} {pg:7d} {100*fig/pg:6.0f}% {len(rows):9d} {100*fig/len(rows):8.0f}%")
