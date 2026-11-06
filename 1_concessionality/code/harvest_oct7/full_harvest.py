import json, os, time, hashlib, urllib.request, sys
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW=os.path.join(BASE,'raw'); PAGES=os.path.join(BASE,'pages')
d=json.load(open(os.path.join(RAW,'psw_data.json')))
targets=[x for x in d if str(x.get('IFCDisclosure1','')).startswith('http')]
log=open(os.path.join(BASE,'fetch_log.txt'),'a')
def say(s):
    print(s,flush=True); log.write(s+'\n'); log.flush()
say(f'START {time.strftime("%H:%M:%S")} targets={len(targets)}')
ok=err=cached=0
for i,x in enumerate(targets,1):
    url=x['IFCDisclosure1']; h=hashlib.sha1(url.encode()).hexdigest()[:16]
    p=os.path.join(PAGES,h+'.html')
    if os.path.exists(p) and os.path.getsize(p)>5000:
        cached+=1; continue
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (academic research; CGD working paper)'})
    try:
        with urllib.request.urlopen(req,timeout=45) as r: t=r.read().decode('utf-8',errors='replace')
        open(p,'w',encoding='utf-8').write(t); ok+=1
    except Exception as e:
        err+=1; say(f'  ERR {i} {x["ProjName"][:30]} {str(e)[:70]}')
    time.sleep(1.2)
    if i%20==0: say(f'  {i}/{len(targets)} fetched={ok} cached={cached} err={err}')
say(f'DONE fetched={ok} cached={cached} err={err} total={len(targets)}')
