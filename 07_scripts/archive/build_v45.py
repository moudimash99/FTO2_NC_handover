"""Re-run classify() of parser v4.5 on the 2,740 FTO2 defects, apply the cable tracker,
check nothing but the new columns moved, write fto2_parsed_defects_v4_5.csv."""
import sys, pandas as pd
sys.path.insert(0, '/home/claude/pack')
import nc_defect_parser as P

old = pd.read_csv('/mnt/user-data/outputs/fto2_parsed_defects_v4_4.csv', dtype={'notification_number': str})
nz = lambda v: None if pd.isna(v) or v == '' else v
rows = []
for _, r in old.iterrows():
    d = P.Defect(seq=int(r['seq']), code=nz(r['code']), fin=nz(r['fin']), text=('' if pd.isna(r['text']) else r['text']), source_format=r['source_format'])
    d.sub_code = nz(r['sub_code']); d.sap_type = nz(r['sap_type'])
    P.classify(d)
    rows.append({'notification_number': r['notification_number'], **{k: getattr(d, k) for k in
                 ['type_reporting', 'mode_erreur', 'confidence', 'resolved_by', 'provenance', 'provenance_force', 'etat_cable',
                  'defaut_cable', 'cable_preuve', 'categorie', 'famille', 'groupe', 'sous_groupe', 'text']}})
new = pd.DataFrame(rows)
tr = pd.read_csv('/mnt/user-data/uploads/Suivi_NCs_-_A30_-_NC_câbles_et_analyses.csv', dtype=str)
new = P.apply_cable_tracker(new, tr)

check = ['type_reporting', 'mode_erreur', 'categorie', 'famille', 'provenance', 'etat_cable', 'defaut_cable', 'tracker_imputation']
bad = {c: int((old[c].fillna('').astype(str) != new[c].fillna('').astype(str)).sum()) for c in check}
print('differences vs v4.4:', bad)
assert not any(bad.values()), 'classification moved'

out = old.copy()
pos = list(out.columns).index('famille')
out.insert(pos, 'sous_groupe', new['sous_groupe'].values)
out.insert(pos, 'groupe', new['groupe'].values)
out.to_csv('/mnt/user-data/outputs/fto2_parsed_defects_v4_5.csv', index=False)
print(out.groupe.value_counts().to_string())
print(out.groupby(['groupe', 'sous_groupe']).size().to_string())
