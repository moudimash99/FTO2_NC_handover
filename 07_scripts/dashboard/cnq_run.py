import sys, pandas as pd, numpy as np, json
R="/home/user/FTO2_NC_handover/"
sys.path.insert(0,R+'cnq_handoever')
from cnq.cnq_core import compute_cnq
import importlib.util
sp=importlib.util.spec_from_file_location('L',R+'02_dashboard_pack/skywise_nc_dashboard_v48/1_pipeline/fto2_logic.py')
sys.path.insert(0,R+'02_dashboard_pack/skywise_nc_dashboard_v48/1_pipeline'); L=importlib.util.module_from_spec(sp); sp.loader.exec_module(L)
x=pd.concat([pd.read_csv(R+'06_input_data/'+f,low_memory=False,dtype={'notification_number':str}) for f in ['fto2_dashboard_data_12.csv','fto2_dashboard_data_missing_ids_3.csv']]).drop_duplicates('notification_number')
x['notification_number']=x.notification_number.astype(str).str.strip()
nc=pd.DataFrame({'notification_number':x.notification_number,'statut':x.status_open_closed,'decision_status':x.decision_status,
 'liability':x.liability,'date_creation':x.creation_time,'type_nc':x.GPS_Type_NC.where(x.GPS_Type_NC.notna(),x.Type_NC_auto),
 'produit':x.Produit_auto,'responsabilite':x.liability_description,'programme':x.programme,'plant':x.plant})
nc['perimetre']=[L._perimetre(s,p,r,l) for s,p,r,l in zip(nc.statut,nc.plant,nc.responsabilite,nc.liability)]
m=pd.read_csv(R+'05_outputs/fto2_defects_llm_longtext.csv',dtype={'notification_number':str},low_memory=False)
v=pd.read_csv(R+'05_outputs/fto2_parsed_defects_v4_8.csv',dtype={'notification_number':str},low_memory=False)[['notification_number','seq','qty']]
m=m.merge(v,on=['notification_number','seq'],how='left')
out={}
for lab,col,cab in [('parser','parser_sous_categorie','parser_defaut_cable'),('llm','llm_sous_categorie','llm_defaut_cable')]:
    d=m[['notification_number','seq','qty']].copy(); d['sous_groupe']=m[col]; d['cable']=m[cab].astype(bool)
    n2,d2=compute_cnq(nc,d)
    a=n2[n2.cnq_on_aec==1]
    tot=a.cnq_cost_total.sum()
    # allocation: NC cost minus direct lines, split equally across its lines; plus each line's direct cost
    d2=d2[d2.cnq_on_aec==1].copy()
    nlines=d2.groupby('notification_number').seq.transform('size')
    direct_sum=d2.groupby('notification_number').cnq_cost_direct.transform('sum')
    nccost=d2.notification_number.map(a.set_index('notification_number').cnq_cost_total)
    d2['alloc']=d2.cnq_cost_direct+(nccost-direct_sum)/nlines
    cab_alloc=d2[d2.cable].alloc.sum(); cab_direct=d2[d2.cable].cnq_cost_direct.sum()
    nc_cab=set(d2[d2.cable].notification_number); cab_nc=a[a.notification_number.isin(nc_cab)].cnq_cost_total.sum()
    print(f"[{lab}] AEC NCs {len(a)} total level3 {tot:,.0f} EUR | lvl1 {a.cnq_cost_airbus.sum():,.0f} lvl2 {a.cnq_cost_global.sum():,.0f}")
    print(f"   cable defects {d2.cable.sum()} in {len(nc_cab)} NCs | allocated {cab_alloc:,.0f} = {cab_alloc/tot:.1%} | direct only {cab_direct:,.0f} = {cab_direct/tot:.1%} | NCs with a cable defect {cab_nc:,.0f} = {cab_nc/tot:.1%}")
    print('   alloc check', round(d2.alloc.sum()), 'vs cost of AEC NCs with lines', round(a[a.notification_number.isin(set(d2.notification_number))].cnq_cost_total.sum()), ' NCs without lines', round(a[~a.notification_number.isin(set(d2.notification_number))].cnq_cost_total.sum()))
    # by category allocated
    d2['cat']=d2.sous_groupe.map(lambda s: L.SOUS_CATEGORIES.get(s,('Autre',))[0] if hasattr(L,'SOUS_CATEGORIES') else '')
    out[lab]=(n2,d2)
import pickle; pickle.dump(out,open('cnq_out.pkl','wb'))
