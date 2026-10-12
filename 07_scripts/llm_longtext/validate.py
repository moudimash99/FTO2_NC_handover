import json, re, sys
S='/tmp/claude-0/-home-user-FTO2-NC-handover/3e9a7317-eb66-5172-89e1-6e435294d804/scratchpad/'
labels=set(re.findall(r'^- \*\*(.+?)\*\*', open(S+'guide.md').read().split('## Taxonomy')[1], re.M))
b, o = sys.argv[1], sys.argv[2]
want=[(c['notification_number'],d['seq']) for c in json.load(open(b)) for d in c['defects']]
got={}; errs=[]
for i,l in enumerate(open(o),1):
    if not l.strip(): continue
    try: r=json.loads(l)
    except Exception as e: errs.append(f'line {i}: bad JSON'); continue
    k=(str(r.get('notification_number')),int(r.get('seq',-1)))
    if r.get('sous_categorie') not in labels: errs.append(f'line {i}: bad label {r.get("sous_categorie")!r}')
    if r.get('confiance') not in ('high','medium','low'): errs.append(f'line {i}: bad confiance')
    if 'symptome' not in r: errs.append(f'line {i}: missing symptome key (see ROOT CAUSE FIRST in guide.md)')
    if k in got: errs.append(f'line {i}: duplicate {k}')
    got[k]=r
miss=[k for k in want if k not in got]; extra=[k for k in got if k not in set(want)]
print(f'expected {len(want)}, got {len(got)}, missing {len(miss)}, extra {len(extra)}, errors {len(errs)}')
for x in (errs+[f'missing {m}' for m in miss]+[f'extra {e}' for e in extra])[:30]: print(x)
print('OK' if not (errs or miss or extra) else 'FIX NEEDED')
