"""REC tagging checks: reproduces the coverage numbers in HANDOVER.md (section REC).

Usage:  python3 -I rec_checks.py <data_dir>
<data_dir> must hold: dash.csv (fto2_dashboard_data export), missing_ids.csv,
nc_rec.csv (full Skywise records of the tracker NCs), tracker.csv (REC tracker export).
"""
import re, sys, pandas as pd

d = sys.argv[1]
rd = lambda f: pd.read_csv(f'{d}/{f}', dtype=str, low_memory=False).fillna('')
D, M, R = rd('dash.csv'), rd('missing_ids.csv'), rd('nc_rec.csv')
T = pd.read_csv(f'{d}/tracker.csv', dtype=str).fillna('')
T.columns = [c.strip() for c in T.columns]
T['nc'] = T[[c for c in T.columns if 'déclaratif' in c][0]].str.extract(r'(\d{9,10})', expand=False)
T = T[T.nc.notna()].copy()
T.loc[T.nc == '2181014667', 'nc'] = '218014667'                       # assumed typo
T['imp'] = T['Imputation'].str.strip().str.upper()

REC_AUTHORS = {'ST32873', 'GALIZ81C', 'RGAGTM5M', 'PMAR3D30', 'CLOP5B4I', 'TO74350', 'MCROIP8V'}
AUTH = re.compile(r'\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\(\s*(\S+)\s+[A-Z0-9]+\s*/')
def markers(df, trk):
    au = df.description_long_text.map(lambda t: (AUTH.search(t).group(1) if AUTH.search(t) else ''))
    out = pd.DataFrame(index=df.index)
    out['st'] = df.station.str.contains('42RC') | df.work_ctr.str.match(r'^(RECX|SUBR)')
    out['au'] = au.isin(REC_AUTHORS)
    out['trk'] = df.notification_no_leading_zeros.isin(trk)
    out['fto2'] = (df.plant == 'FTO2') | df.liability.str.contains('FTO2') | df.description_long_text.str.contains('FTO2')
    return out

trk = set(T.nc)
A = pd.concat([R, D, M]).drop_duplicates('notification_no_leading_zeros')
A['created'] = pd.to_datetime(A.creation_time.str[:10], errors='coerce')
W = A[A.notification_no_leading_zeros.isin(trk) & (A.created >= '2026-01-20') & (A.created < '2026-09-29')]
m = markers(W, trk)
print('Tracker NCs in window 20 Jan-28 Sep:', len(W))
print('  station/work centre:', m.st.sum(), '| + FTO2 filter:', (m.st | m.fto2).sum(), '| + authors:', (m.st | m.fto2 | m.au).sum())
N = R[R.plant != 'FTO2']; mn = markers(N, trk)
print('Tracker NCs outside plant FTO2:', len(N), '| station/wc:', mn.st.sum(), '| + authors:', (mn.st | mn.au).sum())
B = pd.concat([D, M]).drop_duplicates('notification_no_leading_zeros')
mb = markers(B, trk); rec = mb.st | mb.au | mb.trk; gps = B.GPS_Type_NC.str.strip() != ''
print('Dashboard files: REC today', (B.Programme_auto == 'REC').sum(), '| new rule', rec.sum())
print('  GPS conflicts: today', ((B.Programme_auto == 'REC') & gps).sum(), '| new rule', (rec & gps).sum())
q = B[B.station.str.contains('42RC')]
print('  rows at 42RC:', len(q), '| tagged REC', (q.Programme_auto == 'REC').sum(), '| in tracker', q.notification_no_leading_zeros.isin(trk).sum())
