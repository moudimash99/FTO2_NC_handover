import json, glob, pandas as pd
m=pd.read_csv('merged.csv',dtype={'notification_number':str},low_memory=False)
sel=m[(m.llm_sous_categorie=='Amont · Câble')&(m.llm_provenance!='RECU')&(m.sous_groupe=='Manquant – câble / shunt / élément')]
keys={(r.notification_number,int(r.seq)) for r in sel.itertuples()}
n=0
for f in sorted(glob.glob('out/*.jsonl')):
    L=[json.loads(l) for l in open(f) if l.strip()]; ch=False
    for r in L:
        if (str(r['notification_number']),int(r['seq'])) in keys:
            r['sous_categorie']='Manquant – câble / shunt / élément'; r['sous_code']='Q03-004'
            r['raison']=r['raison']+' | revue: E4 exige "non fourni / non livré" écrit; demande de fourniture = action, pas cause'; n+=1; ch=True
    if ch: open(f,'w').write(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in L))
print('reverted',n, 'FTO2:',(sel.perimetre=='FTO2').sum())
