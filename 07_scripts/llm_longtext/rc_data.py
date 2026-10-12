import pandas as pd, json, re
R='/home/user/FTO2_NC_handover/'
S='/tmp/claude-0/-home-user-FTO2-NC-handover/3e9a7317-eb66-5172-89e1-6e435294d804/scratchpad/'
m=pd.read_csv(R+'05_outputs/fto2_defects_llm_longtext.csv',dtype={'notification_number':str},low_memory=False)
d=pd.concat([pd.read_csv(R+f'06_input_data/{f}',low_memory=False,dtype={'notification_number':str}) for f in ['fto2_dashboard_data_12.csv','fto2_dashboard_data_missing_ids_3.csv']]).drop_duplicates('notification_number')
lt={c['notification_number']:c for i in range(1,35) for c in json.load(open(S+f'batches/b{i:02d}.json'))}
r=m[m.perimetre=='Retour client'].merge(d[['notification_number','plant','liability','GPS_Type_NC','description_short']],on='notification_number')
def s(x): return '' if pd.isna(x) else str(x)
rows=[]
for x in r.itertuples():
    L=lt[x.notification_number]['long_text']
    det=re.search(r'Moment of Detection\s*:\s*([^\n]+)',L); det=det.group(1).strip() if det else ''
    nat=''
    if x.llm_categorie=='Élément Endommagé':
        if re.search(r'During the unpacking|lors de la r[ée]ception|à r[ée]ception',L,re.I) and x.llm_sous_categorie!='Composant HS': nat='recu'
        elif x.llm_sous_categorie=='Composant HS': nat='hs'
        elif x.llm_sous_categorie=='Composant – cause non écrite': nat='nc'
        else: nat='phys'
    rows.append({'nc':x.notification_number,'seq':int(x.seq),'date':s(x.date_creation),'line':s(x.ligne),'plant':s(x.plant),
      'liab':s(x.liability),'scope':int('FTO2' in s(x.liability)),'gps':s(x.GPS_Type_NC),'title':s(x.description_short),
      'cat':x.llm_categorie,'rca':s(x.llm_rca_nom),'sub':x.llm_sous_categorie,'code':s(x.llm_sous_code),
      'why':s(x.llm_raison).split(' | revue')[0],'sym':s(x.llm_symptome),'conf':x.llm_confiance,'pcat':x.parser_categorie,
      'snip':s(x.snippet)[:600],'lt':L[:2200],'det':det,'nat':nat})
rows.sort(key=lambda z:(z['date'],z['nc'],z['seq']),reverse=True)
f=[z for z in rows if z['scope']]
from collections import Counter
print(len(rows),len(f),Counter(z['nat'] for z in f if z['nat']),Counter(z['nat'] for z in rows if z['nat']))
print(min(z['date'] for z in rows),max(z['date'] for z in rows))
json.dump({'rows':rows,'meta':{'from':'2026-01-01','to':max(z['date'] for z in rows)}},open(S+'rc_data.json','w'),ensure_ascii=False)
