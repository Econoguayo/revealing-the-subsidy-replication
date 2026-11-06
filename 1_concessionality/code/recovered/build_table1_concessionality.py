# Recovered 2026-11-02 from the record of the working session of October 7, 2026 (turn 130, 2026-10-07 ~15:10 ET; the record is not public).
# Comment lines revised 2026-11-05 for the replication package; the code is unchanged.
# Originally run inline as `python3 -I - << 'PYEOF'` (tool description: "Rebuild the dispersion
# table with grouped validation, corrected terminology and exact MSE figure"); never saved as a
# file. Its output, tab_concessionality_dispersion.tex, is the source of the numbers in Table 1
# (tab:concessionality) of the working paper (versions of October 20 and November 4, 2026). Panel B is not in the paper;
# its "All transactions" p90/p10 of 9.1 is the figure quoted in Appendix E. The table notes were
# later rewritten in the manuscript; the numbers were not.
# Body copied verbatim (heredoc delimiters removed). Lines marked ADAPTED change paths only.
import json,math,re,os
import numpy as np, pandas as pd, statsmodels.formula.api as smf
import sys                                                             # ADAPTED
P=sys.argv[1]                                                          # ADAPTED: was the 2026-10-07 session scratchpad path
OUT=sys.argv[2] if len(sys.argv)>2 else P                              # ADAPTED
os.makedirs(OUT,exist_ok=True)                                         # ADAPTED
d=json.load(open(P+'/combined_dataset.json'))
ok=[r for r in d if r.get('concessionality_pct') is not None and r.get('denominator_type')=='total project cost' and r['agency']=='IFC']
df=pd.DataFrame([{'conc':r['concessionality_pct'],'fac':r['Facility'],'ind':r['Industry'],'cycle':r['ReplenishmentCode'],
 'fcs':r['FCS/FCV'],'cost':r.get('project_cost_musd'),'name':r['ProjName'],'cty':r['Country']} for r in ok])
df['fac2']=df.fac.apply(lambda s:'BFF' if s=='BFF' else('LCF' if s=='LCF' else 'mixed'))
df['ind2']=df.ind.str.split('/').str[0].str.strip().str[:22]; df['lc']=np.log(df.conc); df['rowid']=range(len(df))
SPON=[('nmb','NMB Tanzania','Tanzania'),('kicb','KICB Kyrgyz','Kyrgyz'),('sonatel','Sonatel group',None),('acep','ACEP',None),('orange','Sonatel group',None)]
def grp(r):
    n=r['name'].lower()
    for tok,lab,cty in SPON:
        if re.search(r'\b'+tok,n) and (cty is None or cty.lower() in r['cty'].lower()): return lab
    return 'solo::'+r['name']
df['grp']=df.apply(grp,axis=1)
def cv(sub,f,by):
    e=[]
    for k in sub[by].unique():
        tr=sub[sub[by]!=k]; te=sub[sub[by]==k]
        try: p=smf.ols(f,data=tr).fit().predict(te)
        except Exception: continue
        for a,b in zip(te.lc.values,p.values):
            if not np.isnan(b): e.append(a-b)
    return math.sqrt(np.mean(np.array(e)**2))
specs=[('None (unconditional)','lc ~ 1'),('Facility','lc ~ C(fac2)'),('Facility, industry','lc ~ C(fac2)+C(ind2)'),
 ('Facility, industry, cycle','lc ~ C(fac2)+C(ind2)+C(cycle)'),('Facility, industry, cycle, fragility','lc ~ C(fac2)+C(ind2)+C(cycle)+C(fcs)')]
b1=b2=None; rows=[]
for lab,f in specs:
    m=smf.ols(f,data=df).fit(); r1=cv(df,f,'rowid'); r2=cv(df,f,'grp')
    if b1 is None: b1,b2=r1,r2
    rows.append(f"{lab} & {int(m.nobs)} & {m.rsquared:.3f} & {m.rsquared_adj:.3f} & {math.exp(np.sqrt(m.mse_resid)):.2f} & {math.exp(r1):.2f} & {math.exp(r2):.2f} & {100*(1-r1/b1):.1f} \\\\")
sub=df.dropna(subset=['cost']).copy(); sub['lcost']=np.log(sub.cost)
f='lc ~ C(fac2)+C(ind2)+C(cycle)+C(fcs)+lcost'
m=smf.ols(f,data=sub).fit(); r1=cv(sub,f,'rowid'); r2=cv(sub,f,'grp'); rb=cv(sub,'lc ~ 1','rowid')
rows.append(f"Adding log project cost & {int(m.nobs)} & {m.rsquared:.3f} & {m.rsquared_adj:.3f} & {math.exp(np.sqrt(m.mse_resid)):.2f} & {math.exp(r1):.2f} & {math.exp(r2):.2f} & {100*(1-r1/rb):.1f} \\\\")
pan=[]
for lab,s2,f in [('All transactions',df,'lc ~ C(fac2)+C(ind2)+C(cycle)'),
                 ('Blended Finance Facility only',df[df.fac2=='BFF'],'lc ~ C(ind2)+C(cycle)'),
                 ('Local Currency Facility only',df[df.fac2=='LCF'],'lc ~ C(ind2)+C(cycle)'),
                 ('Fragile and conflict-affected only',df[df.fcs=='FCS'],'lc ~ C(fac2)+C(ind2)+C(cycle)'),
                 ('Excluding estimates above 30 percent',df[df.conc<=30],'lc ~ C(fac2)+C(ind2)+C(cycle)')]:
    s=s2.copy(); m=smf.ols(f,data=s).fit(); r1=cv(s,f,'rowid'); rb=cv(s,'lc ~ 1','rowid'); q=s.conc.quantile([.1,.9])
    pan.append(f"{lab} & {len(s)} & {q[.9]/q[.1]:.1f} & {m.rsquared_adj:.3f} & {math.exp(r1):.2f} & {math.exp(rb):.2f} & {100*(1-r1/rb):.1f} \\\\")
tex=r"""\begin{table}[htbp]
\centering
\caption{Predictability of Disclosed Concessionality from Recorded Project Characteristics}
\label{tab:concessionality-dispersion}
\small
\textit{Panel A. Variation accounted for by recorded characteristics}\\[2pt]
\begin{tabular}{lccccccc}
\toprule
 & & & & Residual & \multicolumn{2}{c}{Prediction error} & Reduction \\
\cmidrule(lr){6-7}
Conditioning set & $n$ & $R^2$ & Adj.\ $R^2$ & factor & Transaction & Sponsor & (percent) \\
\midrule
"""+"\n".join(rows)+r"""
\bottomrule
\end{tabular}

\vspace{8pt}
\textit{Panel B. Robustness}\\[2pt]
\begin{tabular}{lcccccc}
\toprule
Sample & $n$ & p90/p10 & Adj.\ $R^2$ & Prediction & Unconditional & Reduction \\
\midrule
"""+"\n".join(pan)+r"""
\bottomrule
\end{tabular}
\begin{tablenotes}
\small
\item \textit{Notes:} The dependent variable is the natural logarithm of the concessionality estimate disclosed at approval, expressed as a share of total project cost, for the 92 IFC transactions in the IDA18 through IDA20 Private Sector Window registry whose disclosure states that denominator. The residual factor is the exponentiated residual standard deviation of the fitted regression. The prediction-error columns report a multiplicative prediction-error measure, the exponentiated root mean squared cross-validated prediction error, $\exp\!\big(\sqrt{n^{-1}\sum_i (y_i-\hat{y}_{-i})^2}\big)$, where $\hat{y}_{-i}$ omits the held-out observation from estimation; a value of 2.0 indicates prediction to within a factor of two. The transaction column holds out one transaction at a time and the sponsor column holds out all transactions of the same sponsor, which affects the 11 transactions belonging to the four sponsors that appear more than once. The reduction column reports the proportional fall in the root mean squared error relative to the unconditional benchmark, measured in log points; for the full conditioning set the corresponding reduction in mean squared error is 28.8 percent. In Panel B the benchmark is recomputed within each subsample.
\item Industry is the IFC industry group, cycle is the IDA replenishment, and fragility follows the registry's designation. The disclosures report neither the reference price and the concessional price separately nor the inputs to the pricing model, so the exercise measures the predictability of the disclosed estimate from recorded characteristics. Residual variation is not evidence about information held by sponsors and unavailable to IFC.
\item \textit{Source:} IFC project disclosures matched to the IDA PSW project registry. Author's compilation.
\end{tablenotes}
\end{table}
"""
open(OUT+'/tab_concessionality_dispersion.tex','w').write(tex)        # ADAPTED: OUT
print("\n".join(rows)); print('---'); print("\n".join(pan))
