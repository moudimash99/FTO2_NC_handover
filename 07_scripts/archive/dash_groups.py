"""Rebuild the Pareto, drill-down, client and supplier data with the v4.5 groups.
First reproduces the current family numbers from the same SAP rows, so the scope is proven identical."""
import sys, json, shutil, pandas as pd
sys.path.insert(0, '/home/claude/pack'); import nc_defect_parser as P
SP = '/tmp/claude-0/-home-claude/5232bea3-af63-5fca-a79e-ac15321b67d6/scratchpad'
D = json.load(open(f'{SP}/dash_data.json'))
shutil.copy(f'{SP}/dash_data.json', f'{SP}/dash_data_v44.json')

m = pd.read_pickle(f'{SP}/m_sap.pkl')
m['categorie'] = [P.categorie_of(t, c, x) for t, c, x in zip(m.type_reporting, m.defaut_cable, m.text.fillna(''))]
m['famille'] = m.categorie.map(P.famille_of)
m['groupe'] = [P.groupe_of(t, c) for t, c in zip(m.type_reporting, m.categorie)]
m['sous_groupe'] = [P.sous_groupe_of(t, c, x) for t, c, x in zip(m.type_reporting, m.categorie, m.text.fillna(''))]
alive = m.status_open_closed != 'deleted'
supplier = m.liability_description.fillna('').str.contains('SUPPLIER')
main = m[alive & ~supplier]

# 1. scope check against the published family Pareto
for prog in ['All', 'A330', 'A350']:
    s = main if prog == 'All' else main[main.programme == prog]
    got = s.famille.value_counts().to_dict()
    want = dict((k, v) for k, v in D['pareto'][prog])
    assert got == want, (prog, got, want)
want_cl = dict((k, v) for k, v in D['client']['cats']); got_cl = m[alive & (m.plant != 'FTO2')].famille.value_counts().to_dict()
want_su = dict((k, v) for k, v in D['supplier']['cats']); got_su = m[alive & supplier].famille.value_counts().to_dict()
assert got_cl == want_cl, (got_cl, want_cl); assert got_su == want_su, (got_su, want_su)
print('scope check: family numbers reproduced for All/A330/A350, client, supplier')

ASIDE = ['Amont', 'FOD', 'Dossier', 'Non classé']
def ordered(counts):
    head = sorted([(g, n) for g, n in counts.items() if g not in ASIDE], key=lambda r: (-r[1], r[0]))
    tail = [(g, counts[g]) for g in ASIDE if counts.get(g)]
    return [[g, int(n)] for g, n in head + tail]

def detail(s):
    out = {}
    for g, sub in s.groupby('groupe'):
        rows = sorted(sub.sous_groupe.value_counts().items(), key=lambda r: (-r[1], r[0]))
        if len(rows) > 8:
            small = [r for r in rows if r[1] <= 3]
            if len(small) > 1:
                rows = [r for r in rows if r[1] > 3] + [(f'Autres ({len(small)} types)', sum(n for _, n in small))]
        out[g] = [[k, int(v)] for k, v in rows]
    return out

D['pareto'], D['pareto_detail'] = {}, {}
for prog in ['All', 'A330', 'A350']:
    s = main if prog == 'All' else main[main.programme == prog]
    D['pareto'][prog] = ordered(s.groupe.value_counts().to_dict())
    D['pareto_detail'][prog] = detail(s)
D['pareto_aside'] = ASIDE
D['client']['cats'] = ordered(m[alive & (m.plant != 'FTO2')].groupe.value_counts().to_dict())
D['supplier']['cats'] = ordered(m[alive & supplier].groupe.value_counts().to_dict())
json.dump(D, open(f'{SP}/dash_data.json', 'w'), ensure_ascii=False)
for prog in ['All', 'A330', 'A350']:
    print(prog, D['pareto'][prog])
print('detail All', json.dumps(D['pareto_detail']['All'], ensure_ascii=False))
print('client', D['client']['cats']); print('supplier', D['supplier']['cats'])
