import json, os, sys, hashlib, csv, re
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(BASE,'scripts'))
import extract as E
d=json.load(open(os.path.join(BASE,'raw','psw_data.json')))
out=[]
for x in d:
    rec={k:x.get(k) for k in ['ProjName','ProjType','Country','Region','Facility','Instrument','PSWSupport','PSWSize','FCS/FCV','ReplenishmentCode','Industry','Sector','BoardDate','RMF','BFF','MGF','LCF']}
    url=str(x.get('IFCDisclosure1') or '')
    rec['url']=url; rec['miga']=bool(x.get('MIGADisclosure1'))
    if url.startswith('http'):
        p=os.path.join(BASE,'pages',hashlib.sha1(url.encode()).hexdigest()[:16]+'.html')
        if os.path.exists(p):
            rec.update(E.parse(open(p,encoding='utf-8',errors='replace').read()))
            rec['page']='fetched'
        else: rec['page']='fetch_failed'
    else: rec['page']='no_ifc_link'
    out.append(rec)
json.dump(out,open(os.path.join(BASE,'full_results.json'),'w'),indent=1)
ok=[r for r in out if r.get('concessionality_pct') is not None]
print('registry',len(out),'| pages fetched',sum(1 for r in out if r.get('page')=='fetched'),'| concessionality extracted',len(ok))
