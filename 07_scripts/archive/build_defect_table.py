import sys, pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
S, OUT = sys.argv[1], sys.argv[2]
df = pd.read_pickle(f'{S}/defects_v48.pkl')
D = pd.read_csv(f'{S}/rec_data/dash.csv', dtype=str, low_memory=False)
M = pd.read_csv(f'{S}/rec_data/missing_ids.csv', dtype=str, low_memory=False)
A = pd.concat([D, M]).drop_duplicates('notification_no_leading_zeros').fillna('')
A['notification_number'] = A['notification_no_leading_zeros']
df['notification_number'] = df['notification_number'].astype(str)
nd = df.groupby('notification_number').size().rename('n_def')
df = df.join(nd, on='notification_number')
m = df.merge(A, on='notification_number', how='left', suffixes=('', '_nc'))
assert len(m) == len(df)
print('unmatched NC info:', (m['station'].isna()).sum())
m = m.fillna('')
cab = m.defaut_cable.astype(str).str.lower().isin(['true', '1'])
kind = pd.cut(m.n_def, [0, 1, 10, 10**6], labels=['Standalone (1 defect)', 'Short list (2-10)', 'Inspection list (>10)']).astype(str)
yn = lambda s: s.astype(str).str.lower().isin(['true', '1']).map({True: 'Yes', False: 'No'})
out = pd.DataFrame({
    'NC number': m.notification_number,
    'Defect #': pd.to_numeric(m.seq),
    'Defects in NC': m.n_def,
    'NC kind': kind,
    'Perimeter': m.perimetre,
    'NC status': m.statut,
    'Created': pd.to_datetime(m.creation_time, errors='coerce').dt.date,
    'Closed': pd.to_datetime(m.closure_time, errors='coerce').dt.date,
    'Programme': m.ligne.replace('nan', ''),
    'MSN': m.msn,
    'Phase (SERIE/REC/FTI)': m.Programme_auto,
    'NC type': m.Type_NC_auto,
    'Origin': m.Origin_auto,
    'Product': m.Produit_auto,
    'Plant': m['plant'],
    'Station': m.station,
    'Station description': m.station_description,
    'Work centre': m.work_ctr,
    'Trigger': m.trigger,
    'Notification type': m.notification_type,
    'Decision': m.decision_status_description_en,
    'Liability': m.liability_description,
    'Responsible (level 1)': m.responsible_defect_level1_name,
    'Author department': m.user_department,
    'Skywise defect code': m.defect_code_description_en,
    'Skywise cause group': m.cause_group_description_en,
    'FIN': m.fin,
    'Defect text': m.text,
    'Code written': m.code,
    'Sub-code': m.sub_code,
    'Pareto category': m.groupe,
    'Sub-category': m.sous_groupe,
    'RCA': m.rca_nom,
    'Error mode': m.rca_mode,
    'Minor': yn(m.mineur),
    'Cable problem': cab.map({True: 'Yes', False: 'No'}),
    'Cable state': m.etat_cable.map({'LONGUEUR': 'Length', 'DOMMAGE': 'Damage'}).fillna('').where(cab, ''),
    'Cable origin': m.provenance.map({'LIGNE': 'Line', 'RECU': 'Received', 'NON_PRECISE': 'Not stated'}).fillna('').where(cab, ''),
    'Classified from': m.souscat_source.map({'TEXTE': 'Text', 'CODE+TEXTE': 'Code + text', 'CODE': 'Code', 'DEVINE': 'Best guess'}).fillna(m.souscat_source),
    'Parser confidence': m.confidence,
    'GPS type NC': m.GPS_Type_NC,
    'GPS imputation': m.GPS_Imputation,
    'External list': m.Ext_Source,
    'NC short description': m.description_short,
    'NC long text': m.description_long_text.str.slice(0, 32000),
})
out = out.sort_values(['Created', 'NC number', 'Defect #'], ascending=[False, True, True])
f = f'{OUT}/FTO2_defects_detail_v48.xlsx'
with pd.ExcelWriter(f, engine='openpyxl') as w:
    pd.DataFrame().to_excel(w, sheet_name='Summary', index=False)
    out.to_excel(w, sheet_name='Defects', index=False)
    pd.DataFrame().to_excel(w, sheet_name='Read me', index=False)
wb = load_workbook(f)
ws = wb['Defects']
n = ws.max_row
HDR = PatternFill('solid', fgColor='1F3864'); WH = Font(name='Arial', bold=True, color='FFFFFF', size=10)
BODY = Font(name='Arial', size=10)
for c in ws[1]:
    c.fill = HDR; c.font = WH; c.alignment = Alignment(wrap_text=True, vertical='center')
for row in ws.iter_rows(min_row=2):
    for c in row: c.font = BODY
widths = {'Defect text': 60, 'NC long text': 60, 'NC short description': 35, 'Station description': 26, 'Sub-category': 30,
          'RCA': 28, 'Pareto category': 18, 'Responsible (level 1)': 26, 'Author department': 28, 'Skywise defect code': 26,
          'Skywise cause group': 20, 'NC kind': 20, 'Phase (SERIE/REC/FTI)': 12}
cols = {c.value: i + 1 for i, c in enumerate(ws[1])}
for name, i in cols.items():
    ws.column_dimensions[get_column_letter(i)].width = widths.get(name, 13)
for name in ('Created', 'Closed'):
    L = get_column_letter(cols[name])
    for r in range(2, n + 1): ws[f'{L}{r}'].number_format = 'yyyy-mm-dd'
ws.row_dimensions[1].height = 32
ws.freeze_panes = 'C2'
ws.auto_filter.ref = ws.dimensions
# ---- Summary (live formulas on the Defects sheet)
sm = wb['Summary']
col = lambda name: f"Defects!${get_column_letter(cols[name])}$2:${get_column_letter(cols[name])}${n}"
B = Font(name='Arial', bold=True, size=10); T = Font(name='Arial', bold=True, size=13)
sm['A1'] = 'FTO2 defects by Pareto category (parser v4.8)'; sm['A1'].font = T
sm['A2'] = 'Counts are live formulas on the Defects sheet. "FTO2 perimeter" excludes deleted NCs, customer returns and supplier NCs.'; sm['A2'].font = Font(name='Arial', italic=True, size=9, color='555555')
heads = ['Pareto category', 'All defects', 'FTO2 perimeter', 'of which cable problems', 'of which minor',
         'FTO2: standalone NCs', 'FTO2: short lists', 'FTO2: inspection lists']
for j, h in enumerate(heads, 1):
    c = sm.cell(row=4, column=j, value=h); c.fill = HDR; c.font = WH; c.alignment = Alignment(wrap_text=True, vertical='center')
cats = ['MEO Câblage', 'Erreur Branchement', 'Élément Endommagé', 'Élément Manquant', 'Déverrouillage',
        'Grounding/Bonding', 'Kitting Factory', 'FOD', 'Autre']
cat, per, cb, mn, kd = col('Pareto category'), col('Perimeter'), col('Cable problem'), col('Minor'), col('NC kind')
for i, k in enumerate(cats):
    r = 5 + i
    sm.cell(row=r, column=1, value=k)
    sm.cell(row=r, column=2, value=f'=COUNTIFS({cat},$A{r})')
    sm.cell(row=r, column=3, value=f'=COUNTIFS({cat},$A{r},{per},"FTO2")')
    sm.cell(row=r, column=4, value=f'=COUNTIFS({cat},$A{r},{per},"FTO2",{cb},"Yes")')
    sm.cell(row=r, column=5, value=f'=COUNTIFS({cat},$A{r},{per},"FTO2",{mn},"Yes")')
    for j, kv in zip((6, 7, 8), ('Standalone (1 defect)', 'Short list (2-10)', 'Inspection list (>10)')):
        sm.cell(row=r, column=j, value=f'=COUNTIFS({cat},$A{r},{per},"FTO2",{kd},"{kv}")')
tr = 5 + len(cats)
sm.cell(row=tr, column=1, value='Total').font = B
for j in range(2, 9):
    L = get_column_letter(j)
    c = sm.cell(row=tr, column=j, value=f'=SUM({L}5:{L}{tr-1})'); c.font = B
    c.border = Border(top=Side(style='thin'))
for row in sm.iter_rows(min_row=5, max_row=tr - 1):
    for c in row: c.font = BODY
sm.column_dimensions['A'].width = 22
for j in range(2, 9): sm.column_dimensions[get_column_letter(j)].width = 15
sm.row_dimensions[4].height = 32
# ---- Read me
rm = wb['Read me']
notes = [
    ('FTO2 defect table', ''),
    ('Source', 'Skywise NC export fto2_dashboard_data (1,000 NCs, 20 Jan - 28 Sep 2026) + missing-IDs file (127 NCs). Defects parsed with nc_defect_parser v4.8.'),
    ('One row =', 'one defect. NC columns are repeated on every defect of the same NC.'),
    ('Perimeter', 'FTO2 = counted in the Pareto. Retour client, Fournisseur, Supprimée (deleted), Autre are shown separately or excluded.'),
    ('NC kind', 'Standalone = the NC has one defect. Short list = 2-10 defects. Inspection list = more than 10 (finishing / final-control lists).'),
    ('Phase', 'SERIE / REC / FTI as tagged today by the pipeline (Programme_auto, from workflow_list and constituent_assembly).'),
    ('Pareto category / Sub-category / RCA', 'v4.8 classification: 9 categories; RCA names as renamed by the team.'),
    ('Minor', 'Tie-wraps (tyraps) and caps only, as defined for the dashboard.'),
    ('Cable problem', 'Yes when the cable itself has to be remade or supplied again. Cable state (Length / Damage) and Cable origin (Line / Received / Not stated) only for those rows. Origin is set only when the text says it explicitly.'),
    ('Classified from', 'Code + text = official code written and confirmed by the text; Text = no code, text only; Best guess = text too thin, nearest sub-category.'),
    ('Parser confidence', 'HIGH = official code written; MEDIUM/LOW = keyword match; NONE = nothing usable.'),
    ('Caveat', 'The 1,000-NC export is cut by .head(1000) in the pipeline notebook, so early January is only partly covered.'),
]
for i, (a, b) in enumerate(notes, 1):
    rm.cell(row=i, column=1, value=a).font = T if i == 1 else B
    c = rm.cell(row=i, column=2, value=b); c.font = BODY; c.alignment = Alignment(wrap_text=True, vertical='top')
    rm.cell(row=i, column=1).alignment = Alignment(vertical='top')
rm.column_dimensions['A'].width = 34; rm.column_dimensions['B'].width = 110
wb.move_sheet('Defects', offset=-1)
wb.active = 0
wb.save(f)
print(f, len(out), 'rows', len(out.columns), 'cols')
