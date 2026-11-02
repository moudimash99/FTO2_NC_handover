"""REC tagging by NC writer department: reproduces the numbers in HANDOVER.md (section 7, 20 Oct update).

Usage:  python3 -I rec_dept_rule.py <repo>/06_input_data <nc2025_dir>
<nc2025_dir> holds split_part_nc_*.csv from work_orders_disruptions_nc2025.rar (2025 FTO2 NCs).
"""
import glob, re, sys, pandas as pd

I, N = sys.argv[1], sys.argv[2]
rd = lambda f: pd.read_csv(f, dtype=str, low_memory=False).fillna('')
R = rd(f'{I}/nc-rec.csv'); R['src'] = 'rec'
D = pd.concat([rd(f'{I}/fto2_dashboard_data_12.csv'), rd(f'{I}/fto2_dashboard_data_missing_ids_3.csv')]); D['src'] = 'dash'
Y = pd.concat([pd.read_csv(f, dtype=str, encoding='utf-8-sig', keep_default_na=False) for f in sorted(glob.glob(f'{N}/split_part_nc_*.csv'))]); Y['src'] = 'nc2025'
A = pd.concat([R, D, Y], ignore_index=True).fillna('').drop_duplicates('notification_no_leading_zeros').reset_index(drop=True)
A = A[A.system.isin(['PEA', ''])]                                    # TOF / 51 systems have no user_department

T = pd.read_csv(f'{I}/REC_tracker_NC_redigees_par_le_REC.csv', dtype=str).fillna('')
T.columns = [c.strip() for c in T.columns]
T['nc'] = T[[c for c in T.columns if 'déclaratif' in c][0]].str.extract(r'(\d{9,10})', expand=False)
T.loc[T.nc == '2181014667', 'nc'] = '218014667'                      # assumed typo
trk = set(T.nc.dropna()) - {'217022710'}                             # tracker: "non rédigé par le REC"
A['pos'] = A.notification_no_leading_zeros.isin(trk)

REC_DEPTS = ['QRT/DERICHEBOURG AERONAUTICS', 'QR/DERICHEBOURG AERONAUTICS', 'OSOOM/DERICHEBOURG AERONAUTICS',
             'QLOT/DERICHEBOURG AERONAUTICS', 'QLOT1/AIRBUS OPERATIONS SAS']
writer = A.user_department.isin(REC_DEPTS)
rec_wf = A.workflow_list.str.match(r'REC-|A30-REJ-PVU|RJ-PVU-REC') & ~A.work_ctr.str.startswith('IEVB')
A['new'] = writer & ((A.plant != 'FTO2') | rec_wf)

AUTH = re.compile(r'\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\(\s*(\S+)\s+[A-Z0-9]+\s*/')
A['au'] = A.description_long_text.map(lambda t: AUTH.search(t).group(1) if AUTH.search(t) else '')
REC6 = {'ST32873', 'GALIZ81C', 'RGAGTM5M', 'PMAR3D30', 'CLOP5B4I', 'TO74350'}
rules = {
    'station 42RC': A.station.str.contains('42RC'),
    'work_ctr RECX/SUBR': A.work_ctr.str.match(r'^(RECX|SUBR)'),
    'author IDs (7)': A.au.isin(REC6 | {'MCROIP8V'}),
    'current workflow regex': A.workflow_list.str.contains(r'\bREC\b|-CRE|-PNC|A30-REJ-PVU2', case=False),
    'writer department': A.new,
}
print(f'NCs: {len(A)} | REC-written per tracker: {A.pos.sum()}')
for k, m in rules.items():
    h = A[m]
    print(f'  {k:24} tracker {h.pos.sum():3}/{A.pos.sum()} | other hits {(~h.pos).sum():3}'
          f' | written outside REC depts {(~h.pos & ~h.user_department.isin(REC_DEPTS)).sum():3}')
x = A[A.new & ~A.pos]
print('Writer rule, hits not in tracker:', len(x), '| by REC inspector IDs:', x.au.isin(REC6).sum(),
      '| A330 VU follow-up workflows:', x.workflow_list.str.match(r'A30-REJ-PVU|RJ-PVU-REC').sum())

B = D.drop_duplicates('notification_no_leading_zeros')
new = B.notification_no_leading_zeros.isin(A.notification_no_leading_zeros[A.new])
cur, gps = B.Programme_auto == 'REC', B.GPS_Type_NC.str.strip() != ''          # GPS = SERIE-only register
print('Dashboard files:', len(B), '| REC today', cur.sum(), f'({(cur & gps).sum()} in GPS)',
      '| writer rule', new.sum(), f'({(new & gps).sum()} in GPS, {(new & ~cur).sum()} not REC today)')

c = A[(A.plant != 'FTO2') & writer & (A.creation_time.str[:10] >= '2026-01-01')]
odd = c[~c.station.str.contains('42RC') & ~c.workflow_list.str.startswith('REC-')]
print('Expected in Skywise check (plant != FTO2, REC depts, since 2026-01-01): at least', len(c),
      f'({(c.status_open_closed == "deleted").sum()} deleted) | not at 42RC and no REC- workflow:', len(odd))
