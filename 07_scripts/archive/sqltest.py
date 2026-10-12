"""Run every Slate query on the test Postgres for each program (and each group for the
drill-down) and compare with the same numbers computed in pandas from the same tables."""
import subprocess, io, glob, os, pandas as pd
Q = '/home/claude/pack/skywise_nc_dashboard/3_slate_queries'
PGB = sorted(glob.glob('/usr/lib/postgresql/*/bin'))[0]
SP = '/tmp/claude-0/-home-claude/5232bea3-af63-5fca-a79e-ac15321b67d6/scratchpad'


def run(fn, prog='All', group=''):
    sql = open(f'{Q}/{fn}').read().replace('{{w_program.selectedValue}}', prog).replace('{{w_group.selectedValue}}', group)
    open('/tmp/pgtest/q.sql', 'w').write(sql); os.chmod('/tmp/pgtest/q.sql', 0o644)
    out = subprocess.run(['su', 'postgres', '-c', f'{PGB}/psql -h /tmp/pgtest -p 5499 -d postgres --csv -f /tmp/pgtest/q.sql'],
                         capture_output=True, text=True)
    assert out.returncode == 0 and 'ERROR' not in out.stderr, (fn, out.stderr)
    return pd.read_csv(io.StringIO(out.stdout))


d = pd.read_csv(f'{SP}/nc_defects_test_v45.csv', dtype=str)
n = pd.read_csv(f'{SP}/sap_nc_test.csv', dtype=str)
n['nc_id'] = n.notification_number.str.lstrip('0'); d['nc_id2'] = d.notification_number.str.lstrip('0')
j = d.merge(n, left_on='nc_id2', right_on='nc_id', how='inner')
j['created'] = pd.to_datetime(j.creation_time).dt.date.astype(str)
alive = j.status_open_closed.fillna('') != 'deleted'
sup = j.liability_description.fillna('').str.upper().str.contains('SUPPLIER')
main = j[alive & ~sup & (j.created >= '2026-01-01')]
ASIDE = {'Amont': 1, 'FOD': 2, 'Dossier': 3, 'Non classé': 4}
fails = 0
for prog in ['All', 'A330', 'A350']:
    s = main if prog == 'All' else main[main.programme == prog]
    want = s.groupe.value_counts()
    order = sorted(want.index, key=lambda g: (ASIDE.get(g, 0), -want[g] if g not in ASIDE else 0, g))
    got = run('02_q_pareto.sql', prog)
    ok = list(got.pareto_group) == order and all(got.set_index('pareto_group').defects[g] == want[g] for g in order)
    ok &= [str(a).lower() in ('t', 'true') for a in got.aside] == [g in ASIDE for g in order] and abs(got.cumulative_pct.iloc[-1] - 100) < 0.05
    print(f'02 {prog}: {"OK" if ok else "FAIL"}', list(zip(got.pareto_group, got.defects, got.cumulative_pct)))
    fails += not ok
    for g in order:
        want2 = s[s.groupe == g].sous_groupe.value_counts().to_dict()
        got2 = run('03_q_pareto_detail.sql', prog, g)
        ok2 = dict(zip(got2.detail, got2.defects)) == want2 and abs(got2.pct_of_group.sum() - 100) < 0.6
        fails += not ok2
        if not ok2 or prog == 'All':
            print(f'   03 {prog} · {g}: {"OK" if ok2 else "FAIL"}', list(zip(got2.detail, got2.defects))[:6])
cl = j[alive & (j.plant.fillna('') != 'FTO2') & (j.created >= '2026-01-01')].groupe.value_counts().to_dict()
got = run('09_q_client_returns.sql'); ok = dict(zip(got.pareto_group, got.defects)) == cl; fails += not ok
print('09 client:', 'OK' if ok else 'FAIL', list(zip(got.pareto_group, got.defects)))
su = j[alive & sup & (j.created >= '2026-01-01')].groupe.value_counts().to_dict()
got = run('10_q_supplier_returns.sql'); ok = dict(zip(got.pareto_group, got.defects)) == su; fails += not ok
print('10 supplier:', 'OK' if ok else 'FAIL', list(zip(got.pareto_group, got.defects)))
for fn in sorted(os.listdir(Q)):
    if fn[:2] in ('01', '04', '05', '06', '07', '08'):
        r = run(fn); print(fn, 'runs,', len(r), 'rows')
got = run('01_q_monthly_topics.sql'); print('01 topics:', sorted(got.topic.unique()), got[got.month == '2026-01'][['topic', 'defects']].values.tolist())
print('FAILS', fails)
