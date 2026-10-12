import pandas as pd, re, json
R='/home/user/FTO2_NC_handover/'
S='/tmp/claude-0/-home-user-FTO2-NC-handover/3e9a7317-eb66-5172-89e1-6e435294d804/scratchpad/'
v=pd.read_csv(R+'05_outputs/fto2_parsed_defects_v4_8.csv',low_memory=False,dtype={'notification_number':str})
d=pd.concat([pd.read_csv(R+f'06_input_data/{f}',low_memory=False,dtype={'notification_number':str}) for f in
   ['fto2_dashboard_data_12.csv','fto2_dashboard_data_missing_ids_3.csv']]).drop_duplicates('notification_number').set_index('notification_number')
def clean(t):
    t=str(t or '')
    t=re.sub(r'(?:--\s*){3,}','',t)
    t=re.sub(r'Tél\.\s*[^\n]*','',t)
    t=re.sub(r'#(UID|TEL|PRS)~','',t)
    t=re.sub(r'[ \t]+',' ',t)
    t=re.sub(r'\n\s*\*?\s*\n','\n',t)
    return t.strip()
def s(x): return '' if pd.isna(x) else str(x)
ncs=[]
for nc,g in v.groupby('notification_number',sort=False):
    r=d.loc[nc]
    ncs.append({'notification_number':nc,'programme':s(r.programme),'perimetre':s(g.perimetre.iloc[0]),
      'station':s(r.station)+' '+s(r.station_description),'user_department':s(r.user_department),
      'description_short':s(r.description_short),
      'sap_defect_code':(s(r.defect_code)+' '+s(r.defect_code_description_en)).strip(),
      'sap_cause':(s(r.cause_code_description_en)+' '+s(r.cause_description)).strip(),
      'long_text':clean(r.description_long_text),
      'defects':[{'seq':int(x.seq),'written_code':s(x.code),'fin':s(x.fin),'snippet':s(x.text)} for x in g.itertuples()]})
# batches of ~100 defects, NCs kept whole
batches=[];cur=[];n=0
for c in ncs:
    if n+len(c['defects'])>100 and cur: batches.append(cur);cur=[];n=0
    cur.append(c);n+=len(c['defects'])
batches.append(cur)
for i,b in enumerate(batches,1):
    json.dump(b,open(S+f'batches/b{i:02d}.json','w'),ensure_ascii=False,indent=1)
print(len(batches),[sum(len(c['defects']) for c in b) for b in batches])
