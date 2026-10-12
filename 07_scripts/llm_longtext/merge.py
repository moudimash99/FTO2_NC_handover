import pandas as pd, json, glob, sys
sys.path.insert(0,'/home/user/FTO2_NC_handover/01_parser')
R='/home/user/FTO2_NC_handover/'
import importlib.util
spec=importlib.util.spec_from_file_location('p',R+'01_parser/nc_defect_parser.py'); P=importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
SC=P.SOUS_CATEGORIES
v=pd.read_csv(R+'05_outputs/fto2_parsed_defects_v4_8.csv',low_memory=False,dtype={'notification_number':str})
o=pd.DataFrame([json.loads(l) for f in sorted(glob.glob('out/*.jsonl')) for l in open(f) if l.strip()])
o['notification_number']=o.notification_number.astype(str); o['seq']=o.seq.astype(int)
o=o.add_prefix('llm_').rename(columns={'llm_notification_number':'notification_number','llm_seq':'seq'})
o['llm_categorie']=o.llm_sous_categorie.map(lambda s: SC.get(s,('Autre',))[0])
o['llm_rca']=o.llm_sous_categorie.map(lambda s: SC.get(s,(None,'AUTRE'))[1])
o['llm_mineur']=o.llm_sous_categorie.map(P.est_mineur)
m=v.merge(o,on=['notification_number','seq'],how='left')
old=pd.read_csv(R+'05_outputs/fto2_defects_souscodes_llm.csv',dtype={'notification_number':str})[['notification_number','seq','text','sous_categorie']]
m['n_def_nc']=m.groupby('notification_number').seq.transform('size')
print('labelled',m.llm_sous_categorie.notna().sum(),'/',len(m))
m.to_csv('merged.csv',index=False)
