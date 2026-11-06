import json,re,os,hashlib
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(open(P+'/raw/psw_data.json'))
m=[x for x in d if str(x.get('MIGADisclosure1','')).startswith('http')]
SUB=re.compile(r'amount of (?:risk )?subsid\w+\s+is\s+estimated\s+to\s+be\s+(less than\s+)?([0-9]+(?:\.[0-9]+)?)\s*%',re.I)
MULTI=re.compile(r'([0-9]+(?:\.[0-9]+)?)\s*%\s*in\s+([A-Z][A-Za-z ]+?)(?=,|\s+and\b|\s+of the)',re.I)
TENOR=re.compile(r'envisaged\s+([0-9]+)[\s-]*year',re.I)
CO={'sierra leone':'Sierra Leone','liberia':'Liberia','drc':'Congo, Democratic Republic of','congo':'Congo, Democratic Republic of'}
out=[]
for x in m:
    u=x['MIGADisclosure1']; p=P+'/miga_pages/'+hashlib.sha1(u.encode()).hexdigest()[:16]+'.html'
    rec={k:x.get(k) for k in ['ProjName','Country','Region','Facility','Instrument','PSWSupport','FCS/FCV','ReplenishmentCode','Industry','Sector','BoardDate','RMF','BFF','MGF','LCF']}
    rec['url']=u; rec['agency']='MIGA'
    if not os.path.exists(p): rec['page']='fetch_failed'; out.append(rec); continue
    rec['page']='fetched'
    txt=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',open(p,encoding='utf-8',errors='replace').read())).replace('&nbsp;',' ')
    s=SUB.search(txt)
    if s:
        val=float(s.group(2)); rec['is_upper_bound']=bool(s.group(1))
        seg=txt[s.start():s.start()+320]
        pairs=MULTI.findall(seg)
        if pairs:
            rec['multi_country']='; '.join(f'{v}% {c.strip()}' for v,c in pairs)
            for v,c in pairs:
                if CO.get(c.strip().lower(),c.strip()).lower() in str(rec['Country']).lower() or c.strip().lower() in str(rec['Country']).lower():
                    val=float(v); break
        rec['concessionality_pct']=val
        t=TENOR.search(seg); rec['guarantee_years']=int(t.group(1)) if t else None
        rec['denominator_type']='total project cost' if 'total project cost' in seg.lower() else 'other'
        rec['sentence']=seg.split('Env')[0].strip()[:340]
    else:
        rec['concessionality_pct']=None
        i=txt.lower().find('subsid')
        rec['note']=re.sub(r'\s+',' ',txt[max(0,i-100):i+200])[:260] if i>=0 else 'no subsidy mention'
    out.append(rec)
json.dump(out,open(P+'/miga_results.json','w'),indent=1)
ok=[r for r in out if r.get('concessionality_pct') is not None]
print('MIGA projects',len(out),'| extracted',len(ok))
import statistics as st
if ok:
    v=[r['concessionality_pct'] for r in ok]
    print(f'median {st.median(v):.2f} mean {st.mean(v):.2f} min {min(v)} max {max(v)}')
    print('upper-bound phrasing:',sum(1 for r in ok if r.get('is_upper_bound')),'of',len(ok))
print('\nno figure:',len(out)-len(ok))
for r in out:
    if r.get('concessionality_pct') is None: print('  ',r['ProjName'][:32],'|',str(r.get('note'))[:110])
