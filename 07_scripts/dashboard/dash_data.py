import pickle, json, pandas as pd, numpy as np, sys
R='/home/user/FTO2_NC_handover/'
sys.path.insert(0,R+'02_dashboard_pack/skywise_nc_dashboard_v48/1_pipeline')
import importlib.util
sp=importlib.util.spec_from_file_location('P',R+'01_parser/nc_defect_parser.py'); P=importlib.util.module_from_spec(sp); sp.loader.exec_module(P)
out=pickle.load(open('cnq_out.pkl','rb'))
nP,dP=out['parser']; nL,dL=out['llm']
m=pd.read_csv(R+'05_outputs/fto2_defects_llm_longtext.csv',dtype={'notification_number':str},low_memory=False)
x=pd.concat([pd.read_csv(R+'06_input_data/'+f,low_memory=False,dtype={'notification_number':str}) for f in ['fto2_dashboard_data_12.csv','fto2_dashboard_data_missing_ids_3.csv']]).drop_duplicates('notification_number').set_index('notification_number')
rca_nom=pd.read_csv(R+'04_reference/sous_categories.csv',encoding='utf-8-sig').set_index('sous_categorie').rca_nom.to_dict()
rca_nom['Non classé']='Non classé'
cat=lambda s: P.SOUS_CATEGORIES.get(s,('Autre',))[0]
perim=nP.set_index('notification_number').perimetre
date=pd.to_datetime(x.creation_time,utc=True).dt.tz_localize(None)
def wk(ts):
    i=ts.isocalendar(); return f"{i[0]}-W{i[1]:02d}"
ncdate={k:v for k,v in date.items()}
aP=dP.set_index(['notification_number','seq']).alloc; aL=dL.set_index(['notification_number','seq']).alloc
S=lambda v: '' if pd.isna(v) else str(v)
defs=[]
for r in m.itertuples():
    k=(r.notification_number,int(r.seq)); per=perim.get(r.notification_number,'')
    if per not in ('FTO2','Retour client'): 
        # still keep for CNQ allocation if on AEC
        pass
    dt=ncdate[r.notification_number]
    defs.append([r.notification_number,int(r.seq),dt.strftime('%Y-%m-%d'),wk(dt),S(r.ligne),per,
      cat(r.parser_sous_categorie),rca_nom.get(r.parser_sous_categorie,''),r.parser_sous_categorie,int(P.est_mineur(r.parser_sous_categorie)),int(bool(r.parser_defaut_cable)),
      r.llm_categorie,rca_nom.get(r.llm_sous_categorie,''),r.llm_sous_categorie,int(bool(r.llm_mineur)),int(bool(r.llm_defaut_cable)),
      round(float(aP.get(k,0)),2),round(float(aL.get(k,0)),2),S(r.snippet)[:220],S(r.llm_raison).split(' | revue')[0][:160]])
cabP=set(dP[dP.cable].notification_number); cabL=set(dL[dL.cable].notification_number)
nl=nL.set_index('notification_number')
ncs=[]
for r in nP.itertuples():
    n=r.notification_number; dt=ncdate.get(n)
    if dt is None or pd.isna(dt): continue
    l=nl.loc[n]
    ncs.append([n,dt.strftime('%Y-%m-%d'),wk(dt),S(x.loc[n,'programme']) and L_line(x.loc[n,'programme']) if False else '',r.perimetre,int(r.cnq_on_aec),r.cnq_rule,r.cnq_decision_label,r.cnq_where_found,
      round(r.cnq_cost_airbus,2),round(r.cnq_cost_global,2),round(r.cnq_cost_total,2),round(float(l.cnq_cost_total),2),
      round(r.cnq_cost_admin,2),round(r.cnq_cost_work,2),round(float(l.cnq_cost_work),2),round(r.cnq_cost_material,2),round(float(l.cnq_cost_material),2),round(r.cnq_cost_engineering,2),
      int(n in cabP),int(n in cabL),int(r.cnq_defect_lines),S(x.loc[n,'description_short'])[:80]])
# line per NC via programme
import re
LINES=[("A350", r"350"), ("A330", r"330"), ("A400M", r"400|^MT$"), ("A320", r"32\d")]
def line(p):
    p=S(p)
    for nm,pat in LINES:
        if re.search(pat,p): return nm
    return 'Autre'
for row in ncs: row[3]=line(x.loc[row[0],'programme'])
for row in defs:
    if not row[4]: row[4]=line(x.loc[row[0],'programme'])
dirP=dP.set_index(['notification_number','seq']).cnq_cost_direct; dirL=dL.set_index(['notification_number','seq']).cnq_cost_direct
direct={f'{a}|{b}':[round(float(dirP.get((a,b),0)),2),round(float(dirL.get((a,b),0)),2)] for (a,b) in dP.set_index(['notification_number','seq']).index}
D={'defects':defs,'ncs':ncs,'direct':direct,'meta':{'from':'2026-01-01','to':max(r[1] for r in ncs)}}
json.dump(D,open('dash_data.json','w'),ensure_ascii=False,separators=(',',':'))
import os; print(len(defs),len(ncs),os.path.getsize('dash_data.json'))
fto2=[d for d in defs if d[5]=='FTO2']; print('FTO2 defects',len(fto2),'RC',sum(d[5]=='Retour client' for d in defs))
aec=[n for n in ncs if n[5]]; print('AEC',len(aec), round(sum(n[11] for n in aec)), round(sum(n[12] for n in aec)))
from collections import Counter; print(sorted(Counter(d[3] for d in fto2).items())[-6:]); print(Counter(n[3] for n in ncs))
