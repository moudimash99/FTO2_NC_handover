import sys, importlib, pandas as pd
sys.path.insert(0,'/home/claude'); import nc_defect_parser as v41
SP='/tmp/claude-0/-home-claude/5232bea3-af63-5fca-a79e-ac15321b67d6/scratchpad'
base = pd.read_pickle(f'{SP}/p_oldnew.pkl')
rows=[]
for _, r in base.iterrows():
    d = v41.Defect(seq=int(r['seq']), code=(r['code'] or None), fin=(r['fin'] or None), text=r['text'], source_format=r['source_format'])
    d.sap_type = r['sap_type'] or None; v41.classify(d)
    rows.append({'notification_number': r['notification_number'], 'seq': r['seq'], 'text': r['text'], 'old_type': r['old_type'], 'old_mode': r['old_mode'],
                 'type_text': d.type_reporting, 'type_reporting': d.type_reporting, 'mode_erreur': d.mode_erreur, 'confidence': d.confidence,
                 'resolved_by': d.resolved_by, 'provenance': d.provenance, 'provenance_force': d.provenance_force, 'etat_cable': d.etat_cable})
dd = pd.DataFrame(rows)
tr = pd.read_csv('/mnt/user-data/uploads/Suivi_NCs_-_A30_-_NC_câbles_et_analyses.csv', dtype=str)
en = v41.apply_cable_tracker(dd, tr); en['nn']=en['notification_number'].str.lstrip('0')
t = pd.read_pickle(f'{SP}/t5.pkl'); tn=set(t['NC'].dropna()); en['in_tracker']=en['nn'].isin(tn)
ch_text = en[en['old_type']!=en['type_text']]
print(f"TEXT-ONLY regression: {len(ch_text)} changed | outside tracker {(~ch_text['in_tracker']).sum()}")
for _,r in ch_text[~ch_text['in_tracker']].iterrows(): print(f"   {r['nn']} | {r['old_type'][:22]:22s} -> {r['type_text'][:24]:24s} | {r['text'][:80]}")
print(f"ENRICHMENT touched outside tracker: {(~en['in_tracker'] & (en['type_text']!=en['type_reporting'])).sum()} | provenance_source {en['provenance_source'].value_counts().to_dict()} | conflicts {int(en['provenance_conflict'].sum())}")
tm = t[['NC','Motifs','Imputation']].dropna(subset=['NC'])
m = en.merge(tm, left_on='nn', right_on='NC', how='inner')
def ref(r):
    mo, im = r['Motifs'], str(r['Imputation']); up = im.startswith('Salle'); line = im.startswith('Production')
    if mo=='Câble court' or (mo=='Câble coupé' and 'COURT' in r['text'].upper()):
        return 'AMONT_IMPRESSION' if up else ('MEO_CHEMINEMENT' if line else None)
    if mo in ('Câble abimé','Câble coupé'): return 'AMONT_IMPRESSION' if up else ('DOMMAGE_CABLE' if line else None)
    if mo=='Câble manquant': return 'MANQUANT_CABLE_ELEMENT'
    if mo=='Câble non conforme' and up: return 'AMONT_IMPRESSION'
    return None
m['ref']=m.apply(ref,axis=1); e=m[m['ref'].notna()]
print(f"Agreement with tracker (n={len(e)}): v4 {(e['old_type']==e['ref']).mean():.0%} | v4.1 text-only {(e['type_text']==e['ref']).mean():.0%} | v4.1 + tracker {(e['type_reporting']==e['ref']).mean():.0%}")
w=e[e['type_reporting']!=e['ref']]; print(f"remaining: {len(w)}")
for _,r in w.iterrows(): print(f"   {r['nn']} | {r['Motifs']:18s} | ours={r['type_reporting'][:22]:22s} | {r['text'][:70]}")
print("\nMode shares on all 2,740 defects: old v4 vs v4.1+tracker")
print(pd.concat([en['old_mode'].value_counts().rename('v4'), en['mode_erreur'].value_counts().rename('v4.1')],axis=1).fillna(0).astype(int).to_string())
en.to_pickle(f'{SP}/enriched.pkl')
