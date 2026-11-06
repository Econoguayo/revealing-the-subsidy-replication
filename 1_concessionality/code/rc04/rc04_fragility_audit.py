"""RC-04: compare the PSW registry's fragility field with the official World Bank lists.

Inputs (passed as arguments):
  1. psw_ida18_20_registry_204.csv  (official IDA PSW registry export, 204 transactions)
  2. directory holding per-page text of FCSList-FY06toFY25 (p1..p8 = FY25..FY18)
  3. output directory
Measures:
  registry      : registry field "FCS/FCV" as published
  labelled_fy   : on the list labelled for the World Bank fiscal year of the Board date (July-June)
  in_force      : as labelled_fy, except Board dates in FY2020 use the FY19 list, the convention
                  World Bank official FY20 financing statistics used because publication of the FY20
                  list was delayed (Jones et al. 2024, p. 12, n. 4). Publication dates of other lists
                  are not established; they are assumed to apply from July 1 of their fiscal year.
"""
import sys, re, pandas as pd
from pathlib import Path
reg, pages, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
FY_PAGE = {2025:1, 2024:2, 2023:3, 2022:4, 2021:5, 2020:6, 2019:7, 2018:8}
text = {}
for fy, p in FY_PAGE.items():
    t = (pages/f'p{p}.txt').read_text(encoding='utf-8')
    head = t.strip().splitlines()[0]
    assert (f'FY{str(fy)[2:]}' in head.replace(' ','')), (fy, head)
    # drop footnotes (lines beginning with a/ b/ c/) so country names come only from the list body
    body = '\n'.join(l for l in t.splitlines() if not re.match(r'\s*[abc]/', l) and 'peace' not in l.lower() and 'sources' not in l.lower())
    text[fy] = body
PAT = {
 'Afghanistan':r'Afghanistan','Bangladesh':r'Bangladesh','Bhutan':r'Bhutan','Burkina Faso':r'Burkina Faso',
 'Burundi':r'Burundi','Cabo Verde':r'Cabo Verde|Cape Verde','Cambodia':r'Cambodia','Cameroon':r'Cameroon',
 'Central African Republic':r'Central African Rep','Chad':r'\bChad\b','Congo/ Democratic Republic of':r'Congo, Dem|Congo, Democratic',
 'Congo/ Republic of':r'Congo, Rep','Cote d\'Ivoire':r'C[ôo]te d.?Ivoire','Djibouti':r'Djibouti','Ethiopia':r'Ethiopia',
 'Fiji':r'Fiji','Ghana':r'Ghana','Guinea':r'(?<!New )(?<!Equatorial )\bGuinea\b(?!-)','Guinea-Bissau':r'Guinea-Bissau',
 'Haiti':r'Haiti','Kenya':r'Kenya','Kosovo':r'Kosovo','Kyrgyz Republic':r'Kyrgyz','Lao People\'s Democratic Republic':r'\bLao\b',
 'Liberia':r'Liberia','Madagascar':r'Madagascar','Malawi':r'Malawi','Mali':r'\bMali\b','Mauritania':r'Mauritania',
 'Mozambique':r'Mozambique','Myanmar':r'Myanmar','Nepal':r'Nepal','Nicaragua':r'Nicaragua','Nigeria':r'Nigeria',
 'Niger':r'\bNiger\b(?!ia)','Pakistan':r'Pakistan','Papua New Guinea':r'Papua New Guinea','Rwanda':r'Rwanda','Senegal':r'Senegal',
 'Sierra Leone':r'Sierra Leone','Solomon Islands':r'Solomon','Somalia':r'Somalia','South Sudan':r'South Sudan',
 'Tajikistan':r'Tajikistan','Tanzania':r'Tanzania','Timor-Leste':r'Timor','Togo':r'\bTogo\b','Uganda':r'Uganda',
 'Yemen/ Republic of':r'Yemen','Zambia':r'Zambia','Benin':r'Benin','Gabon':r'Gabon','Seychelles':r'Seychelles',
 'Comoros':r'Comoros','Sudan':r'(?<!South )\bSudan\b'}
def on_list(country, fy):
    return bool(re.search(PAT[country], text[fy]))
r = pd.read_csv(reg, encoding='utf-8-sig')
r['board_date'] = pd.to_datetime(r.BoardDate.str[:10])
r['board_fy'] = r.board_date.dt.year + (r.board_date.dt.month >= 7).astype(int)
r['in_force_list_fy'] = r.board_fy.where(r.board_fy != 2020, 2019)
r['registry_fcs'] = (r['FCS/FCV'] == 'FCS').astype(int)
rows = []
for i, x in r.iterrows():
    parts = [p.strip() for p in str(x.Country).split(';')]
    known = [p for p in parts if p in PAT]
    unknown = [p for p in parts if p not in PAT]
    single = len(parts) == 1 and not unknown
    lab = [p for p in known if on_list(p, x.board_fy)]
    inf = [p for p in known if on_list(p, x.in_force_list_fy)]
    rows.append(dict(single_country=int(single), n_countries_named=len(parts), unlisted_names=';'.join(unknown),
        labelled_fy_countries=';'.join(lab), in_force_countries=';'.join(inf),
        labelled_fy_fcs=int(single and len(lab)==1) if single else None,
        in_force_fcs=int(single and len(inf)==1) if single else None,
        any_listed_labelled=int(len(lab)>0), any_listed_in_force=int(len(inf)>0)))
r = pd.concat([r, pd.DataFrame(rows)], axis=1)
keep = ['ProjName','Country','board_date','board_fy','in_force_list_fy','ReplenishmentCode','Facility','IFCDisclosure1','MIGADisclosure1',
        'FCS/FCV','registry_fcs','single_country','labelled_fy_fcs','in_force_fcs','any_listed_labelled','any_listed_in_force',
        'labelled_fy_countries','in_force_countries','unlisted_names','n_countries_named']
r[keep].to_csv(out/'rc04_fragility_by_transaction.csv', index=False)
s = r[r.single_country==1]
print('transactions', len(r), 'single-country', len(s), 'multi or regional', len(r)-len(s))
for m in ['labelled_fy_fcs','in_force_fcs']:
    ct = pd.crosstab(s.registry_fcs, s[m]); print('\nregistry (rows) vs', m, '(cols)\n', ct)
d = s[(s.registry_fcs != s.labelled_fy_fcs) | (s.registry_fcs != s.in_force_fcs)]
d[keep].to_csv(out/'rc04_discrepancies.csv', index=False)
print('\nsingle-country discrepancies:', len(d))
print(d[['ProjName','Country','board_date','board_fy','FCS/FCV','labelled_fy_fcs','in_force_fcs']].sort_values(['Country','board_date']).to_string(index=False))
m = r[r.single_country==0]
print('\nmulti/regional: registry FCS', int(m.registry_fcs.sum()), '| containing a listed country (labelled FY):', int(m.any_listed_labelled.sum()), '| (in force):', int(m.any_listed_in_force.sum()))
print(m[['ProjName','Country','board_fy','FCS/FCV','labelled_fy_countries','unlisted_names']].to_string(index=False))
