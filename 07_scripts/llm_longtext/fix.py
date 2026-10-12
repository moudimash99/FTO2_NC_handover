import json, glob
fix={('218129758',1),('218128823',1),('217114961',6),('217219203',26),('216570343',26)}
n=0
for f in sorted(glob.glob('out/*.jsonl')):
    L=[json.loads(l) for l in open(f) if l.strip()]; ch=False
    for r in L:
        if (str(r['notification_number']),int(r['seq'])) in fix:
            r['symptome']=r.get('symptome') or ('gaine pincée' if 'Gainage' in r['sous_categorie'] else 'harnais non maintenu / pincé')
            r['sous_categorie']='Frettage / colliers – pose'; r['sous_code']='Q05-004'
            r['raison']=(r['raison']+' | revue cohérence: cause = pose du collier/maintien').strip(); n+=1; ch=True
    if ch: open(f,'w').write(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in L))
print('fixed',n)
