# FTO2 NC dashboard in Skywise (Slate): migration guide

## Start here: everything into Skywise, step by step

What you end up with: one notebook that writes three tables every time it runs, and one Slate app with two pages, the
dashboard (Simple and Expert in one page) and the MFT page. The Tableau Elizabeth is optional. Every file named below is in
this folder (`03_reports/skywise/`).

**Step 1. The data: the notebook (Skywise Code Workspace).**

1. Open the Code Workspace where the pipeline notebook runs today.
2. Upload the whole folder `level3_datasets/notebook_kit` next to the notebook, as `nc_defect_parser.py` is today. It holds
   the Python and, in `ref/`, the reference files (official sub-codes, French names, A400M title rules).
3. Upload `level3_datasets/notebook_kit/fto2_ai_labels.csv` once, as a dataset named **`fto2_ai_labels`**.
4. Replace the notebook by `level3_datasets/fto2_pipeline_notebook.ipynb`.
5. In the Data panel, add these datasets with these names (aliases):

   | Dataset | Alias | Read or write |
   |---|---|---|
   | Non Conformity | `non_conformity` | read |
   | `fto2_ai_labels` | `fto2_ai_labels` | read |
   | Work_Order_Operation | `work_order_operation` | read |
   | MES Disruptions | `mes_disruptions` | read |
   | three new datasets | `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions` | write |

6. Run all cells. The last print lists the three tables written.

**Step 2. Sync the three tables to Postgres**, as was done for `fto2_plant`: `fto2_dash_nc`, `fto2_dash_defects` and
`fto2_dash_disruptions`, same names, schema `foundry_sync`.

**Step 3 (optional, 10 minutes). Check that Slate takes the page, on made-up data.** In any Slate app, add a Code Sandbox and
paste the three files of `level1_dummy_in_js` into its CSS, HTML and JS tabs. Expected: titles starting with "Fictif", 543 NC.
Delete it afterwards.

**Step 4. The dashboard page.**

1. Create a new Slate app (do not change the current one until this one works).
2. Add three queries on the Postgres source `postgate-airbus-2`, with these exact names and the text of these files:
   `q_fto2_nc` = `level3_datasets/q_fto2_nc.sql`, `q_fto2_def` = `level3_datasets/q_fto2_def.sql`,
   `q_fto2_dis` = `level3_datasets/q_fto2_dis.sql`.
3. Add a **Code Sandbox**, full width, about 1,400 px high.
4. Paste `level3_datasets/fto2_level23.css` into its CSS tab, `fto2_level23.html` into its HTML tab, `fto2_level23.js` into
   its JS tab.
5. In the sandbox's **state** box (it shows `"input": "Hello World"` at first), paste the content of
   `level3_datasets/state.json`.
6. Expected: "Chargement des données Slate…", then the dashboard. In Expert, Vue d'ensemble, on the data of 28 September 2026:
   **910 NC, 2 960 défauts, 3,3 défauts par NC, 347,4 k€**.

**Step 5. The MFT page, in the same app.**

1. Add a second page to the app.
2. Use the same two queries `q_fto2_nc` and `q_fto2_def` (nothing to add: they are the app's).
3. Add a Code Sandbox, full width, about 1,400 px high. Paste `mft/fto2_mft.css`, `mft/fto2_mft.html` and `mft/fto2_mft.js`
   into its CSS, HTML and JS tabs, and `mft/state.json` into its state box.
4. Expected: A350, week S39: 10 NC, 73 défauts, first category MEO Facteur humain.
5. Know before using it: in Slate, actions typed on the MFT page are saved in the browser of that computer only. Other users
   do not see them. Sharing them needs a table Slate can write to, to ask IT for.

**Step 6 (optional). The Tableau Elizabeth**: a third page, same as step 5 with the files of `elizabeth/`
(see `elizabeth/README.md`).

**Not needed:** `views/` (Synthèse and Détail are now the dashboard's Simple mode), `level2_dummy_queries` (a connection test
on made-up data, only if step 4 fails), `level4_import` (a ready-made app to import, untested).

**Keeping it up to date.**

- New NCs: run the notebook again (step 1.6). The pages show the new data once the sync has run. Nothing to paste.
- A change made on the laptop (the look of a page, the MFT tracker actions, the production plan, 2025, the A400M title rules):
  run `python3 -I build/build_all.py` and `python3 -I 07_scripts/mft/build_mft.py`, then paste the new JS (and the CSS and HTML
  if they changed) into the sandboxes. If `notebook_kit` changed (data rules, A400M rules), upload it again and run the
  notebook.
- If a page shows a coloured box instead of the dashboard, the box says what is wrong: see "Level 2" below for the messages.

## The four levels, in detail

Four levels, to try in order. Each level adds one thing, so when something fails you know where.

| Level | Data | What it proves |
|---|---|---|
| 1. `level1_dummy_in_js` | fictitious, written in the JS | the dashboard works in a Slate code sandbox (looks, tabs, filters) |
| 2. `level2_dummy_queries` | fictitious, made by two Slate queries | the path query → sandbox state → page works |
| 3. `level3_datasets` | real, from two datasets the notebook writes | the real data, refreshed by the Skywise notebook |
| 4. `level4_import` | as levels 2 and 3 | a ready-made Slate app to import (worth a try, not testable here) |

**Simple and Expert (30 Oct).** The dashboard has two modes, switched by "Simple | Expert" at the right of the title, with an
animation (a double click skips it). Simple: Synthèse and Détail, a few charts. Expert: the full dashboard, as before. It opens
in Simple (or in the mode last used, where the browser keeps it). The figures below are Expert's Vue d'ensemble.

The views page (Synthèse et Détail) has its own guide, with two ways to set it up: `views/README.md`.
The MFT page has its own, same setup as level 3: `mft/README.md`. So has the Tableau Elizabeth: `elizabeth/README.md`.

Everything in this folder is written by `python3 -I build/build_all.py`. Do not edit the files by hand; change the
template or the build and rebuild.

## What the dashboard needs

- **Three tables.** `fto2_dash_nc`: one row per NC, 51 columns. `fto2_dash_defects`: one row per defect line, 17
  columns. `fto2_dash_disruptions` (optional): one row per quality aléa that led to no NC, 10 columns, for the
  disruption block shown beside the cost. The meaning of each column is in `level3_datasets/columns.json` (defined in
  `build/fto2_core.py`, `NC_COLUMNS`, `DEF_COLUMNS`, `DIS_COLUMNS`). The JavaScript (`fto2FromTables`) rebuilds
  everything the page shows from them.
- **Fixed references, written in the JS** (`window.FTO2_REF` at the top of the JS part): official code sheet, MFT
  actions, CNQ parameters, EqMSN production plan, root-cause tree, and 2025 (the 2025 NCs summed per month, scope,
  phase, line and product, and the 2025 deliveries per product). To change the production plan, the MFT actions or
  2025: update the files in `06_input_data` / `04_reference`, rebuild on the laptop, paste the new JS part.
- **No JavaScript library to import.** The only outside link is the Google Fonts line at the top of the CSS; if Slate
  blocks it, the page uses Georgia and the system font.
- **The NC selection is the pipeline's.** Level 3 runs the pipeline notebook's own selection code, in one run with the
  missing IDs (see level 3 A). Each NC carries its origin (`origin` = normal or missing_ids), and the filter bar's
  "Origine" can show one or the other.

## Level 1: visual check (fictitious data in the JS)

1. In a new Slate app (or a new page), add a **Code Sandbox** widget. Make it large: full width, about 1,400 px high
   (the dashboard scrolls inside it).
2. Paste `fto2_level1.css` into the CSS tab, `fto2_level1.html` into the HTML tab, `fto2_level1.js` into the JS tab.
   (Or open `FTO2_Level1_Slate.html` and copy what sits between the START and END markers.)
3. Expected: the dashboard with fictitious data (titles start with "Fictif", NC numbers 900000001...). Default view
   (Série, Usine FTO2 uniquement): **543 NC, 1 138 défauts, 2,3 défauts par NC, 216,7 k€, 1,08 NC par MSN**.
4. Check every tab, the filters, FR/EN and "Expliquer le calcul".

If something is wrong, a red box at the top of the dashboard says what (for example: HTML part missing).

## Level 2: connection check (fictitious data made by queries)

1. Same widget, same CSS and HTML (`fto2_level23.css` and `fto2_level23.html` are the same as level 1's). Replace the
   JS by `level2_dummy_queries/fto2_level23.js`.
2. Add three queries on the Postgres source the current app uses (`postgate-airbus-2`):
   - `q_fto2_nc` with the text of `q_fto2_nc_dummy.sql`,
   - `q_fto2_def` with the text of `q_fto2_def_dummy.sql`,
   - `q_fto2_dis` with the text of `q_fto2_dis_dummy.sql` (the disruption block; optional).

   They need no dataset: they make the fictitious data themselves (always the same).
3. In the code sandbox's **state** (the JSON box that shows `"input": "Hello World"` by default), put the content of
   `state.json`:

   ```json
   { "nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}", "dis": "{{q_fto2_dis}}" }
   ```
4. Expected: "Chargement des données Slate…", then exactly the level-1 figures (543 · 1 138 · 2,3 · 216,7 k€ · 1,08),
   and on the Coût tab the block "Aléas qualité sans NC": 2 823 €, 77 aléas. Same figures as level 1 = the queries
   reach the page. Without `q_fto2_dis` the page starts after about 4 seconds, without the block.

If it does not work, the message in the green or orange box says why:

- **Still loading after 20 s**: it names the query it is waiting for. Check the name (exactly `q_fto2_nc`,
  `q_fto2_def`) and that the query runs in the query editor.
- **"La requête q_fto2_nc n'a renvoyé aucune ligne"**: the query ran but returned nothing.
- **"aucune NC lisible … colonnes reçues : …"**: Slate passes the result in a form the page does not expect. Send me
  the list of columns it shows.
- **"exactement N lignes reçues"**: Slate probably cut the result (row limit). Look for a row limit on the query.
- If the source refuses the generator (`generate_series`, `md5`): upload `build/dummy/fto2_dash_nc_dummy.csv` and
  `fto2_dash_defects_dummy.csv` as datasets, sync them to Postgres and use the level-3 queries with their table names.

## Level 3: real data

### A. In the Skywise notebook: one run (the Code Workspace of the pipeline notebook)

`level3_datasets/fto2_pipeline_notebook.ipynb` (and the same as `.py`) replaces the pipeline notebook and the
missing-ID generator. It is made by the build from `06_input_data/pipeline_notebook.py`: the NC selection, the
`*_auto` columns and the GPS / Test merge are that notebook's code, unchanged. What changed:

- **One run** does both selections: the standard one, then the NCs of the GPS / Test lists it does not catch. No
  `RUN_MODE` to switch and no second run. Each NC keeps its origin (normal / missing_ids).
- **The missing IDs are computed in the run**, as `missing_id_generator` did: the NC numbers of the GPS register and the
  Test list dated 2026, minus the standard selection, fetched by number from `non_conformity`. No list to paste.
- **No 1,000-row cap** on the standard selection (`ROW_CAP = None`; it was `head(1000)`). The cap had already dropped
  1-19 January: 57 FTO2 NCs, of which 46 came back only because they are on the lists; 11 were lost.
- **The run writes the dashboard's three tables.** While the current Slate app is in use, `KEEP_OLD_OUTPUTS = True` also
  writes the four former outputs as before; set it to `False` once the new dashboard has replaced the old one.

Steps:

1. Upload the folder `level3_datasets/notebook_kit` next to the notebook, as `nc_defect_parser.py` is today. It holds
   the same Python as the laptop build: `fto2_core.py` (the data steps), the parser v4.8, the CNQ model
   `cnq-2026.10.20b` (with `cnq_orders.py` and `cnq_disruptions.py`), two reference files. The `data/` folder (station
   mapping, GPS register, Test list) stays where it is.
2. Upload `notebook_kit/fto2_ai_labels.csv` once as a dataset named **`fto2_ai_labels`** (the stored root-cause labels).
3. In the workspace's Data panel:

   | Dataset | Alias (name in the notebook) | Use |
   |---|---|---|
   | Non Conformity | `non_conformity` | read, as today |
   | `fto2_ai_labels` | `fto2_ai_labels` | read: the stored root-cause labels |
   | Work_Order_Operation | `work_order_operation` | read: the rework orders' planned times |
   | MES Disruptions | `mes_disruptions` | read: the aléas |
   | new | `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions` | write |
   | yours, while the old app is used | `fto2_dashboard_data`, `fto2_dashboard_data_missing_ids`, `fto2_parsed_defects`, `fto2_parsed_defects_missing_ids` | write (`KEEP_OLD_OUTPUTS`) |

   If you give the two Skywise datasets other aliases, change `WO_OPERATIONS` and `MES_DISRUPTIONS` in the first code
   cell. Left empty, the run works without them: the model's work times, the flat 41-min alert, no disruption block.
4. Run all cells once.
5. Expected print: the standard selection's counts, then `GPS / Test lists: N NCs from 2026; M not in the standard
   selection, fetched by number`, then the three tables. Tested here on a stand-in for Skywise built from the
   September exports and the raw January 2026 NCs: 1,137 NCs (the 1,127 of today plus 11 of 9-19 January, minus one
   FNZ1 NC whose list date is 2025), 1,062 normal and 75 missing_ids; the 1,126 NCs in both runs are identical in every
   column. Level-3 CNQ on AEC there: 179,741 EUR.

### B. Sync the three datasets to Postgres

As was done for `fto2_plant`: sync `fto2_dash_nc`, `fto2_dash_defects` and `fto2_dash_disruptions` to the Postgres
source, with these table names in the schema `foundry_sync`. With other names, change the `FROM` line of the queries.

### C. In Slate

Replace the text of `q_fto2_nc`, `q_fto2_def` and `q_fto2_dis` by `level3_datasets/q_fto2_nc.sql`, `q_fto2_def.sql`
and `q_fto2_dis.sql`. The JS, CSS, HTML and state stay those of level 2.

Expected: the real dashboard, same figures as the laptop build. Default view on the data of 28 September 2026:
**910 NC, 2 960 défauts, 3,3 défauts par NC, 347,4 k€** (since 2 Nov the A400M NCs get a defect line from their title, see `04_reference/a400m_titres_souscodes.csv`) (with the September 2026 operations and the
Jan-Sep aléas, as on the laptop). Every NC of the selection counts (decided 20 Oct): all phases, all dates and the plant
switch off show every row of `fto2_dash_nc` (1,127 on the laptop data). "Usine FTO2 uniquement" keeps the NCs whose `plant` is FTO2
or FT02 (988 on the laptop data, all production types); the Customer returns tab shows `Type_NC_auto` "NC Retour client" with
FTO2 in the liability (69; 34 in Série). Since 20 Oct `fto2_dash_nc` has no `plant_scope` column: re-run the notebook with the
new `notebook_kit` files and paste the new `q_fto2_nc.sql` together, or the old query asks for a column that is gone. The cost is FTO2's only where FTO2 is liable;
the other NCs count as NCs with a cost of 0 (the footnote gives their number and handling cost). Coût tab, block "Aléas
qualité sans NC": 8 233 € (at the production rate, 123 €/h), 66,9 h, 89 aléas (19 possible ERMA aléas left out).

### Refresh

Run `fto2_pipeline_notebook`; the dashboard shows the new data once the sync has run.

## Level 4: import a ready-made app (worth a try)

1. Create a **new, empty** Slate app (not the existing one: importing replaces the whole app).
2. Import `level4_import/FTO2_NC_Dashboard_level2.slate.json`, from the same menu where the v106 JSON was exported.
3. Expected: one page with the code sandbox and the three queries already set up, and the level-2 figures.
4. Once level 3's datasets exist, do the same with `FTO2_NC_Dashboard_level3.slate.json`.

The files follow the structure of the v106 export key by key, but no import could be tried here. If Slate refuses the
file or the page stays blank, do levels 2 and 3 by hand: nothing else depends on level 4.

## The periodic AI pass (labels for new defect lines)

- A new defect line, or one whose text changed, gets the parser's label until it is labelled; the dashboard stays
  complete either way.
- `fto2_pipeline_notebook` writes `fto2_lines_to_label.csv`: one row per line to label, with its full text (`snippet`) and the
  NC's long text.
- Once IT has approved a tool for the NC texts: label those lines with the same columns as `fto2_ai_labels`
  (`notification_number`, `seq`, `snippet`, `llm_sous_categorie`, `llm_sous_code`, `llm_confiance`, `llm_symptome`,
  `llm_defaut_cable`, ...), append the rows to `fto2_ai_labels`, and rerun the cell. A label is used only while the
  line's text is the same as its `snippet`. (Checked: 50 labels removed, exported and put back give the same tables.)
- Earlier labelling scripts, for reference: `07_scripts/llm_longtext/`.

## Rebuilding this folder on the laptop

- `python3 -I build/build_all.py`: rewrites all four levels, from the template and the current data.
- `python3 -I build/dummy_tables.py`: rewrites the fictitious-data queries and, with a local Postgres, the level-1
  data (`build/dummy/`). Only needed if the fictitious data should change.

## What was tested, and what could not be

Tested here:

- Level 1, and level 2 with a stand-in for Slate's API (`preview_local_only.html`): same figures, no NaN in any tab,
  "Expliquer le calcul" adds up on all 514 fictitious reworked NCs; the disruption block shows the same 77 aléas. Without
  `q_fto2_dis`, level 2 starts after about 4 seconds, same figures, no block.
- The level-2 SQL on Postgres 16 (it made the level-1 data).
- The level-3 SQL on Postgres 16, on the real tables loaded as a sync would store them (dates as dates, empty values
  as NULL). The page it gives has the same NCs, defect lines, aléas and figures as the laptop dashboard.
- The notebook code on the exports read as Skywise gives datasets (timestamps, lists, numbers), with the work-order
  operations and the aléas typed as numbers and timestamps: identical tables, origin included.
- The one-step notebook, run whole on a stand-in for Skywise (`non_conformity` rebuilt from the exports and the raw
  January 2026 NCs, the GPS / Test lists rebuilt from the exports' columns): it runs end to end and gives the tables
  described in level 3 A. This found and fixed one problem: the pipeline writes its empty GPS / Test columns as `''`,
  which was read as a GPS NC type (423 NCs lost their type); empty text now counts as missing.
- The messages for a missing query, an empty query, wrong columns, and a page opened outside Slate.

Not testable here, to watch on the first try:

- How Slate passes a query result into the sandbox state. The page accepts an object with one array per column (how
  Slate returns queries), a list of rows, or the same as JSON text.
- Slate's row limits on queries (the page warns when a count looks cut).
- Whether Slate accepts the level-4 file.
- The columns of Work_Order_Operation and MES Disruptions as the notebook reads them. The cell needs, for the
  operations: `order_number`, `order_type`, `plant`, `operation_short_text`, `labor_standard_value`,
  `setup_standard_value` and their two unit columns (unit IM = 1/100 hour); for the aléas: `disruption_id`, `plant`,
  `physical_station`, `work_order`, `wo_designation`, `ds_material`, `type_desc`, `open_date_time`, `open_date_time_tz`,
  `status`, `time_lost`, `program`, `comment`. These are the names in the September 2026 extracts.
- Whether MES Disruptions holds every aléa: the extract stopped at exactly 2,500 rows (check H7).
