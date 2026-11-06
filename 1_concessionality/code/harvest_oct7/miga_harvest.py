import json,urllib.request,time,re,hashlib,os
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(open(P+'/raw/psw_data.json'))
m=[x for x in d if str(x.get('MIGADisclosure1','')).startswith('http')]
res=[]
for i,x in enumerate(m,1):
    u=x['MIGADisclosure1']; p=P+'/miga_pages/'+hashlib.sha1(u.encode()).hexdigest()[:16]+'.html'
    if os.path.exists(p) and os.path.getsize(p)>5000:
        h=open(p,encoding='utf-8',errors='replace').read()
    else:
        try:
            req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (academic research; CGD working paper)'})
            h=urllib.request.urlopen(req,timeout=40).read().decode('utf-8',errors='replace')
            open(p,'w',encoding='utf-8').write(h); time.sleep(1.2)
        except Exception as e:
            res.append({'ProjName':x['ProjName'],'err':str(e)[:60]}); print(i,'ERR',x['ProjName'][:28],flush=True); continue
    txt=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',h))
    anchor=re.search(r'level\s*of\s*concession\w*',txt,re.I)
    pct=re.search(r'concession\w*[^.]{0,200}?([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent)',txt,re.I)
    res.append({'ProjName':x['ProjName'],'Facility':x['Facility'],'FCS':x['FCS/FCV'],'cycle':x['ReplenishmentCode'],
                'anchor':bool(anchor),'pct':pct.group(1) if pct else None,
                'ctx':re.sub(r'\s+',' ',txt[max(0,pct.start()-120):pct.start()+160]) if pct else ''})
    print(i,'anchor' if anchor else '-','pct='+str(res[-1]['pct']),x['ProjName'][:30],flush=True)
json.dump(res,open(P+'/miga_scan.json','w'),indent=1)
print('scanned',len(res))
