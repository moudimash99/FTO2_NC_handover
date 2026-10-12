import sys, re, pandas as pd
sys.path.insert(0, '/home/claude/pack')
import importlib, nc_defect_parser as P
old = pd.read_csv('/mnt/user-data/outputs/fto2_parsed_defects_v4_5.csv', dtype={'notification_number': str})
nz = lambda v: None if pd.isna(v) or v == '' else v
rows = []
for _, r in old.iterrows():
    d = P.Defect(seq=int(r['seq']), code=nz(r['code']), fin=nz(r['fin']), text=('' if pd.isna(r['text']) else r['text']), source_format=r['source_format'])
    d.sub_code = nz(r['sub_code']); d.sap_type = nz(r['sap_type'])
    P.classify(d)
    rows.append({'notification_number': r['notification_number'], 'code': d.code, 'sub_code': d.sub_code, **{k: getattr(d, k) for k in
                 ['type_reporting', 'mode_erreur', 'confidence', 'resolved_by', 'provenance', 'provenance_force', 'etat_cable',
                  'defaut_cable', 'cable_preuve', 'categorie', 'famille', 'groupe', 'sous_groupe', 'souscat_source', 'rca_type', 'rca_mode', 'text']}})
new = pd.DataFrame(rows)
tr = pd.read_csv('/mnt/user-data/uploads/Suivi_NCs_-_A30_-_NC_câbles_et_analyses.csv', dtype=str)
new = P.apply_cable_tracker(new, tr)
check = ['type_reporting', 'mode_erreur', 'categorie', 'famille', 'provenance', 'etat_cable', 'defaut_cable', 'tracker_imputation']
bad = {c: int((old[c].fillna('').astype(str) != new[c].fillna('').astype(str)).sum()) for c in check}
print('old columns unchanged:', bad); assert not any(bad.values())
out = old.copy()
out['groupe_v45'], out['sous_groupe_v45'] = old['groupe'], old['sous_groupe']
for c in ['groupe', 'sous_groupe', 'souscat_source', 'rca_type', 'rca_mode']:
    out[c] = new[c].values
out.to_csv(f'v46.csv', index=False)
# check 1: written code always wins
head = out.code.fillna('').astype(str).str.upper().str.extract(r'^([QT]\d{2})')[0]
w = head.notna()
ok = [lab in P.HEAD_SOUSCATS.get(h, []) for h, lab in zip(head[w], out.sous_groupe[w])]
print(f'written code respected: {sum(ok)} / {w.sum()}')
print(out.souscat_source.value_counts().to_string())
print('\nGROUPS  v4.5 -> v4.6'); print(pd.concat([out.groupe_v45.value_counts().rename('v4.5'), out.groupe.value_counts().rename('v4.6')], axis=1).fillna(0).astype(int).to_string())
print('\nSUB-CATEGORIES'); print(out.groupby(['groupe', 'sous_groupe']).size().to_string())
