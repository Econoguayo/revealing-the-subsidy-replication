import json, re, os, sys, hashlib
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES=os.path.join(BASE,'pages')
def clean(s):
    s=re.sub(r'<[^>]+>',' ',s)
    for a,b in [('&nbsp;',' '),('&amp;','&'),('&#xa0;',' '),('&quot;','"'),('&#39;',"'"),('&rsquo;','’'),('&ldquo;','“'),('&rdquo;','”')]: s=s.replace(a,b)
    return re.sub(r'\s+',' ',s).strip()
def bf_panel(html):
    """Return the text of the accordion panel titled 'Blended Finance'."""
    out=[]
    for m in re.finditer(r'cmp-accordion__title">\s*Blended Finance\s*</span>',html,re.I):
        seg=html[m.end():m.end()+40000]
        p=re.search(r'cmp-accordion__panel[^>]*>(.*?)(?=<div class="accordion |<h3 class="cmp-accordion__header"|</main)',seg,re.S)
        if p: out.append(clean(p.group(1)))
    return max(out,key=len) if out else ''
# strict: only the official concessionality sentence
NUM=r'[0-9]+(?:\.[0-9]+)?'
CONC=re.compile(
    r'level\s*of\s*concession\w*\b.{0,320}?\b(?:estimated|expected)\s*to\s*be\s*'
    r'(?:approximately|about|around|up\s*to)?\s*'
    r'\[?\s*(' + NUM + r')\s*(?:%|percent|per cent)?'
    r'(?:\s*(?:-|\u2013|to)\s*(' + NUM + r')\s*(?:%|percent|per cent)?)?'
    r'\s*\]?\s*(?:%|percent|per cent)?',
    re.I|re.S)
DENOM=re.compile(r'of the\s+((?:total\s+)?(?:first phase\s+)?[Pp]roject cost|total project size|IFC investment|total financing)',re.I)
COST=re.compile(r'(?:total\s+)?(?:cost of the [Pp]roject|[Pp]roject cost)\s*(?:of|is)?\s*(?:up to\s*)?(?:US\$|\$|EUR|XOF|\u20ac)?\s*([0-9][0-9,.]*)\s*(million|billion)?',re.I)
def parse(html):
    bf=bf_panel(html)
    full=clean(html)
    r={'bf_found':bool(bf),'bf_len':len(bf),'bf_text':bf[:2000]}
    m=CONC.search(bf) or CONC.search(full)
    r['found_outside_bf']=bool(m) and not CONC.search(bf)
    src=bf if CONC.search(bf) else full
    if m:
        lo=float(m.group(1)); hi=float(m.group(2)) if m.group(2) else None
        r['concessionality_pct']=(lo+hi)/2 if hi is not None else lo
        r['conc_low']=lo; r['conc_high']=hi; r['is_range']=hi is not None
        r['raw_match']=re.sub(r'\s+',' ',m.group(0))[-90:]
    else:
        r['concessionality_pct']=None
    if m:
        tail=src[m.start():m.start()+400]
        d=DENOM.search(tail); r['denominator']=d.group(1).lower() if d else None
        c=COST.search(tail)
        if c:
            v=float(c.group(1).replace(',','')); u=(c.group(2) or '').lower()
            r['project_cost_musd']=v*1000 if u=='billion' else v
    mj=re.search(r'\{"PSW_Id".{0,8000}?\}\s*\]\s*\}',html,re.S)
    if mj:
        try:
            j=json.loads(mj.group(0))
            r['json_total_project_cost']=j.get('Total_Project_Cost')
            r['json_facilities']={f['Facility_Details']['PSW_Facility_Name']:f.get('Board_Approval_Amount') for f in j.get('Facilities',[]) if f.get('Is_Checked')}
        except Exception as e: r['json_err']=str(e)[:60]
    return r
if __name__=='__main__':
    d=json.load(open(os.path.join(BASE,'pilot_results.json')))
    out=[]
    for x in d:
        h=hashlib.sha1(x['url'].encode()).hexdigest()[:16]; p=os.path.join(PAGES,h+'.html')
        rec={k:x.get(k) for k in ['ProjName','Country','Facility','PSWSupport','FCS/FCV','ReplenishmentCode','Industry','Sector','BoardDate','url']}
        if os.path.exists(p): rec.update(parse(open(p,encoding='utf-8',errors='replace').read()))
        else: rec['bf_found']=False; rec['note']='no page'
        out.append(rec)
    json.dump(out,open(os.path.join(BASE,'pilot_clean.json'),'w'),indent=1)
    ok=[r for r in out if r.get('concessionality_pct') is not None]
    print('pages',len(out),'| BF section found',sum(1 for r in out if r.get('bf_found')),'| concessionality parsed',len(ok))
    print('denominators',{})
    import collections
    print('denominator field:',dict(collections.Counter(r.get('denominator') for r in ok)))
    for r in sorted(ok,key=lambda z:z['concessionality_pct']):
        print(f"  {r['concessionality_pct']:6.2f}  {r['FCS/FCV']:8s} {r['ReplenishmentCode']} {r['ProjName'][:34]:34s} cost={r.get('project_cost_musd')}")
