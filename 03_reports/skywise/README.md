# FTO2 NC dashboard in Skywise

What you end up with: one notebook that writes three tables, and one Slate app with the dashboard (Essentiel and Deep dive in one
page) and the MFT page. The Tableau Elizabeth is optional. Every file named below is in this folder.

Details (what each level proves, what the notebook changes, what was tested): `DETAILS.md`.

## Set it up

**1. The notebook** (the Code Workspace where the pipeline notebook runs today)

1. Upload the whole folder `level3_datasets/notebook_kit` next to the notebook. The `data/` folder (station mapping, GPS
   register, Test list) stays where it is.
2. Upload `level3_datasets/notebook_kit/fto2_ai_labels.csv` once, as a dataset named `fto2_ai_labels`.
3. Replace the notebook by `level3_datasets/fto2_pipeline_notebook.ipynb`.
4. In the Data panel, add these datasets with these names:

   | Dataset | Name | |
   |---|---|---|
   | Non Conformity | `non_conformity` | read |
   | `fto2_ai_labels` | `fto2_ai_labels` | read |
   | Work_Order_Operation | `work_order_operation` | read |
   | MES Disruptions | `mes_disruptions` | read |
   | three new datasets | `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions` | write |

5. Run all cells. The last print lists the three tables written.

While the old Slate app is still in use, the notebook also writes its four old outputs. Once the new app has replaced it,
set `KEEP_OLD_OUTPUTS = False` in the first code cell.

**2. Sync** `fto2_dash_nc`, `fto2_dash_defects` and `fto2_dash_disruptions` to Postgres, same names, schema
`foundry_sync`, as was done for `fto2_plant`.

**3. The dashboard page**

1. Create a new Slate app. Keep the old one until this one works.
2. Add three queries on `postgate-airbus-2`, named exactly: `q_fto2_nc`, `q_fto2_def`, `q_fto2_dis`. Their text is in
   `level3_datasets/q_fto2_nc.sql`, `q_fto2_def.sql`, `q_fto2_dis.sql`.
3. Add a Code Sandbox, full width, about 1,400 px high.
4. Paste `level3_datasets/fto2_level23.css`, `fto2_level23.html` and `fto2_level23.js` into its CSS, HTML and JS tabs.
5. Paste `level3_datasets/state.json` into its state box (it shows `"input": "Hello World"` at first).

Check: on the laptop data to 26 October 2026 (Série, Responsabilité: FTO2 only, the defaults), Deep dive, Vue d'ensemble shows
**868 NC, 3 160 défauts, 388 k€**. Skywise holds a few more days of NCs, so its figures are a little higher.

**4. The MFT page** (a second page in the same app)

1. It uses the same queries `q_fto2_nc` and `q_fto2_def`: nothing to add.
2. Add a Code Sandbox, full width, about 1,400 px high. Paste `mft/fto2_mft.css`, `mft/fto2_mft.html`, `mft/fto2_mft.js`
   into its CSS, HTML and JS tabs, and `mft/state.json` into its state box.

Check: the page opens on the line with the most NCs, on the last full week (laptop data to 26 October: A330, S43, 11 NC, 21 défauts).
The browser remembers the line last chosen.

Good to know: actions typed on the MFT page are saved in that computer's browser only. Other users do not see them.
Sharing them needs a table Slate can write to, to ask IT for.

**5. The Tableau Elizabeth** (optional): a third page, same as the MFT with the files of `elizabeth/`.

Not needed: `views/` (now the dashboard's Essentiel mode), `level1_dummy_in_js` and `level2_dummy_queries` (tests on made-up
data, only if something fails), `level4_import` (untested).

## Already set up on 23 October? What to change

1. Upload `level3_datasets/notebook_kit` again, the whole folder (it holds the current cost rates, the A400M title rules and the
   data steps).
2. Replace the `fto2_ai_labels` dataset with `level3_datasets/notebook_kit/fto2_ai_labels.csv` (3,489 rows: the labels of every
   defect line to 26 October).
3. Run the notebook once.
4. Paste the new `fto2_level23.css`, `.html` and `.js` into the dashboard's sandbox.
5. Paste the new `mft/fto2_mft.js` into the MFT sandbox, or add the MFT page (step 4 above) if it is not there yet.

The notebook file, the other datasets, the sync, the queries and the state boxes stay as they are.

## Keep it up to date

- **New NCs:** run the notebook. The pages follow once the sync has run.
- **A change made on the laptop** (a page's look, the MFT tracker actions, the production plan, 2025, the A400M title rules):
  run `python3 -I build/build_all.py` and `python3 -I 07_scripts/mft/build_mft.py`, then paste the new files into the
  sandboxes. If `notebook_kit` changed, upload it again and run the notebook.
- **New defect lines** get the parser's label until the AI labelling pass labels them (see `DETAILS.md`). The dashboard
  stays complete either way.

## If a page shows a box instead of the dashboard

The box says what is wrong:

- **Still loading after 20 seconds:** it names the query it waits for. Check the name and that the query runs.
- **"La requête … n'a renvoyé aucune ligne":** the query runs but returns nothing. Check the sync.
- **"aucune NC lisible … colonnes reçues : …":** Slate passes the data in a form the page does not expect. Send the list of
  columns it shows.
- **"exactement N lignes reçues":** Slate probably cut the result. Look for a row limit on the query.
