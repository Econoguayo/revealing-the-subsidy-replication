import json,os,re,sys,hashlib,csv,statistics as st,collections
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(BASE,'scripts')); import extract as E
ANCH=re.compile(r'level\s*of\s*concession\w*',re.I)
DEN=re.compile(r'(?:%|percent|per cent)\s*(?:\]\s*)?(?:of|for|as a percentage of)\s+(?:the\s+)?([A-Za-z’\'’ ]{3,60})',re.I)
def classify(t):
    if not t: return 'unstated'
    s=t.lower()
    if 'project' in s and 'cost' in s: return 'total project cost'
    if 'facility size' in s or 'facility' in s: return 'facility size'
    if 'fund size' in s or 'fund' in s: return 'fund size'
    if 'issuance' in s: return 'issuance amount'
    if 'investment cost' in s or 'investment' in s: return 'investment cost'
    if 'trade activity' in s: return 'trade activity'
    if 'cost' in s: return 'component cost'
    return 'other'
d=json.load(open(os.path.join(BASE,'full_results.json')))
rows=[]
for r in d:
    rec=dict(r); rec.pop('bf_text',None)
    if r.get('concessionality_pct') is not None:
        p=os.path.join(BASE,'pages',hashlib.sha1(r['url'].encode()).hexdigest()[:16]+'.html')
        full=E.clean(open(p,encoding='utf-8',errors='replace').read())
        m=ANCH.search(full); seg=full[m.start():m.start()+420] if m else ''
        rec['sentence']=re.sub(r'\s+',' ',seg.split('This estimate')[0].strip())[:360]
        dm=DEN.search(seg); dt=dm.group(1).strip() if dm else ''
        rec['denominator_text']=dt; rec['denominator_type']=classify(dt)
    rows.append(rec)
json.dump(rows,open(os.path.join(BASE,'final_dataset.json'),'w'),indent=1)
cols=['ProjName','Country','Region','FCS/FCV','ReplenishmentCode','Facility','Instrument','Industry','Sector','BoardDate','ProjType','PSWSupport','RMF','BFF','MGF','LCF','concessionality_pct','conc_low','conc_high','is_range','denominator_type','denominator_text','project_cost_musd','page','url','sentence']
with open(os.path.join(BASE,'psw_concessionality_dataset.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader()
    for r in sorted(rows,key=lambda z:(z['ReplenishmentCode'],z['ProjName'])): w.writerow(r)
ok=[r for r in rows if r.get('concessionality_pct') is not None]
print('OBS',len(ok),'of',len(rows),'registry projects')
print('denominator types:',dict(collections.Counter(r['denominator_type'] for r in ok)))
tpc=[r for r in ok if r['denominator_type']=='total project cost']
def s(v): return f'n={len(v)} median={st.median(v):.2f} mean={st.mean(v):.2f}'
print('\nALL obs      ',s([r['concessionality_pct'] for r in ok]))
print('total-proj-cost only',s([r['concessionality_pct'] for r in tpc]))
print('\nBy facility (total project cost denominator only):')
for fac in ['BFF','LCF','MGF','RMF']:
    v=[r['concessionality_pct'] for r in tpc if r['Facility']==fac]
    if v: print(f'  {fac}: {s(v)}')
print('\nBy FCS (total project cost only):')
for g in ['FCS','non-FCS']:
    v=[r['concessionality_pct'] for r in tpc if r['FCS/FCV']==g]
    print(f'  {g}: {s(v)}')
print('\nBy cycle (total project cost only):')
for c in ['ID18','ID19','ID20']:
    v=[r['concessionality_pct'] for r in tpc if r['ReplenishmentCode']==c]
    if v: print(f'  {c}: {s(v)}')
