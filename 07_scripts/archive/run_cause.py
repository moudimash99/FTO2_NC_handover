import sys, pandas as pd
sys.path.insert(0, '/home/claude/pack'); import nc_defect_parser as P
SP = '/tmp/claude-0/-home-claude/5232bea3-af63-5fca-a79e-ac15321b67d6/scratchpad'
ns = dict(vars(P)); exec(open(f'{SP}/cause_rules.py').read(), ns)
d = pd.read_csv('/mnt/user-data/outputs/fto2_parsed_defects_v4_4.csv')
r = d.apply(lambda r: ns['cause_of'](r.categorie, r.type_reporting, r.defaut_cable, r.provenance, r.etat_cable, r.text,
                                     r.tracker_imputation if pd.notna(r.tracker_imputation) else None), axis=1)
d['cause_n1'] = [a for a, b, c in r]; d['niveau'] = [b for a, b, c in r]; d['cause_source'] = [c for a, b, c in r]
d['groupe'] = d.cause_n1.map(lambda c: ns['CAUSES'][c][0])
d.to_pickle(f'{SP}/cause_v1.pkl')
if __name__ == '__main__':
    print(d.niveau.value_counts().to_string())
    print(d.groupby(['groupe', 'cause_n1']).size().sort_values(ascending=False).to_string())
    print(d.cause_source.value_counts().to_string())
    pd.set_option('display.width', 250)
    print(pd.crosstab(d.cause_n1, d.famille).to_string())
