# FTO2 NC dashboard in Skywise

**Everything to download is in one file: `FTO2_Skywise_installation.zip`** (in this folder, kept up to date by the build).

What you end up with: one notebook that writes four tables, and one Slate app with the dashboard (Essentiel and Deep dive in
one page) and the MFT page. The Tableau Elizabeth is optional. Every file named below is in this folder.

The settings (rules, rates, targets, production plan, MFT actions...) are the tables of `data/config/` in the notebook's
workspace: see `docs/comment_faire.md` at the top of the repository.

Details (what each level proves, what was tested): `DETAILS.md`.

## Set it up

**1. The notebook** (the Code Workspace where the pipeline notebook runs today)

1. Upload the whole folder `level3_datasets/notebook_kit` next to the notebook (the code).
2. Upload the folder `level3_datasets/config` into `data/`, so that it becomes `data/config/` (the settings). Do this once:
   from then on the settings are changed there, and uploading the folder again would overwrite those changes.
   The `data/` folder keeps the station mapping, the GPS register and the Test list.
3. Upload `level3_datasets/notebook_kit/fto2_ai_labels.csv` once, as a dataset named `fto2_ai_labels`.
4. Replace the notebook by `level3_datasets/fto2_pipeline_notebook.ipynb` (a few lines: the steps are in `notebook_kit/fto2/`).
5. In the Data panel, add these datasets with these names:

   | Dataset | Name | |
   |---|---|---|
   | Non Conformity | `non_conformity` | read |
   | `fto2_ai_labels` | `fto2_ai_labels` | read |
   | Work_Order_Operation | `work_order_operation` | read |
   | MES Disruptions | `mes_disruptions` | read |
   | four new datasets | `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions`, `fto2_dash_ref` | write |

6. Run all cells. The last lines list the tables written.

While the old Slate app is still in use, the notebook also writes its four old outputs. Once the new app has replaced it,
set `garder_anciennes_sorties` to `non` in `data/config/2_parametres.csv`.

**2. Sync** `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions` and `fto2_dash_ref` to Postgres, same names, schema
`foundry_sync`, as was done for `fto2_plant`.

**3. The dashboard page**

1. Create a new Slate app. Keep the old one until this one works.
2. Add four queries on `postgate-airbus-2`, named exactly: `q_fto2_nc`, `q_fto2_def`, `q_fto2_dis`, `q_fto2_ref`. Their text is
   in `level3_datasets/q_fto2_nc.sql`, `q_fto2_def.sql`, `q_fto2_dis.sql`, `q_fto2_ref.sql`.
3. Add a Code Sandbox, full width, about 1,400 px high.
4. Paste `level3_datasets/fto2_level23.css`, `fto2_level23.html` and `fto2_level23.js` into its CSS, HTML and JS tabs.
5. Paste `level3_datasets/state.json` into its state box (it shows `"input": "Hello World"` at first).

Check: on the laptop data to 26 October 2026 (Série, Responsabilité: FTO2 only, the defaults), Deep dive, Vue d'ensemble shows
**868 NC, 3 160 défauts, 388 k€**. Skywise holds a few more days of NCs, so its figures are a little higher.

**4. The MFT page** (a second page in the same app)

1. It uses the queries `q_fto2_nc`, `q_fto2_def` and `q_fto2_ref`: nothing to add.
2. Add a Code Sandbox, full width, about 1,400 px high. Paste `mft/fto2_mft.css`, `mft/fto2_mft.html`, `mft/fto2_mft.js`
   into its CSS, HTML and JS tabs, and `mft/state.json` into its state box.

Check: the page opens on the line with the most NCs, on the last full week (laptop data to 26 October: A330, S43, 11 NC, 21 défauts).
The browser remembers the line last chosen.

The MFT actions are the table `data/config/1_actions_mft.csv`: an action added there appears for everyone after the next run of
the notebook. An action typed on the MFT page itself stays in that browser only, until it is added to the table.

**5. The Tableau Elizabeth** (optional): a third page, same as the MFT with the files of `elizabeth/`.

Not needed: `views/` (now the dashboard's Essentiel mode), `level1_dummy_in_js` and `level2_dummy_queries` (tests on made-up
data, only if something fails), `level4_import` (untested).

**6. Optional: the calculations in Slate functions.** The targets and forecast, the alarms and the cost explanation can run
as Slate functions instead of in the page, so that the page only draws. Two ways to set it up, both explained in
`level3_datasets/fonctions/README.md`. The page works without them.

## Already set up? What to change (4 November: settings in tables, reference data from the notebook)

1. Upload `level3_datasets/notebook_kit` again, the whole folder: it now holds the folder `fto2/`. Delete the files the old kit
   had at its top (`fto2_core.py`, `fto2_logic.py`, `nc_defect_parser.py`, `cnq/`, `ref/`): nothing reads them any more.
2. Upload the folder `level3_datasets/config` into `data/` (it becomes `data/config/`).
3. Replace the notebook by the new `fto2_pipeline_notebook.ipynb`.
4. Data panel: add the dataset `fto2_dash_ref` (write).
5. Run the notebook, then sync `fto2_dash_ref` to Postgres as the three others.
6. In Slate: add the query `q_fto2_ref` (`level3_datasets/q_fto2_ref.sql`); paste the new `.js` and the new `state.json` into the
   dashboard's, the MFT's and the Elizabeth's sandboxes (the CSS and HTML files changed too: paste all three to be sure).

## Already set up? What to change (13 November: part values from the material, logistics time)

1. Upload `level3_datasets/notebook_kit` again (the whole folder).
2. In `data/config/`: add the line `minutes_logistique` to `2_cout_parametres.csv` and the line
   `logistique_seulement_avec_materiel` to `3_cout_avance.csv` (copy them from `level3_datasets/config/`), and add the table
   `1_prix_pieces.csv` (the price of each material; see `notebook_kit/part_prices.md`).
3. Restart the kernel and run the notebook. Its last lines say how many NCs have a material and how many prices are missing;
   the materials to price are listed in `fto2_parts_to_price.csv`.
4. In Slate: replace the text of the query `q_fto2_nc` by the new `level3_datasets/q_fto2_nc.sql` (four new columns at the
   end), once the sync has run; then paste the new `fto2_level23.js` into the dashboard's sandbox.

## Already set up? What to change (13 November: the year is a setting)

Can be done together with the change above.

1. Upload `level3_datasets/notebook_kit` again (the whole folder).
2. In `data/config/2_parametres.csv`, add the line `annee;2026` (copy it from `level3_datasets/config/2_parametres.csv`).
   The lines `date_debut`, `annee_listes_manuelles` and `debut_ordres_et_aleas` are no longer read: delete them.
   `annee_comparaison` can stay, or be emptied (empty = the year before).
3. Restart the kernel and run the notebook. Its first line says the year followed and the comparison year.
4. In Slate, once the sync has run: paste the new `fto2_level23.js` into the dashboard's sandbox, `mft/fto2_mft.js` into the
   MFT's and `elizabeth/fto2_elizabeth.js` into the Elizabeth's. No query changes.

Nothing changes on the pages for 2026: this only prepares the next years.

## Keep it up to date

- **New NCs:** run the notebook. The pages follow once the sync has run.
- **A new year** (each January): write the year on the line `annee` of `data/config/2_parametres.csv`, bring the production
  plan and the shutdown calendar up to date, save the new year's GPS register and Test list, and run the notebook. Nothing
  to paste in Slate. The steps are in `docs/comment_faire.md` ("Commencer une nouvelle année").
- **A setting** (a rule, a rate, the production plan, an MFT action...): change its table in `data/config/` and run the
  notebook. Nothing to paste in Slate.
- **A change of the code** (a page's look, a new chart): run `python3 -I build/build_all.py`,
  `python3 -I 07_scripts/mft/build_mft.py` and `python3 -I 07_scripts/elizabeth/build_elizabeth.py` on the laptop, then paste
  the new files into the sandboxes. If `notebook_kit` changed, upload it again and run the notebook.
- **New defect lines** get the parser's label until the AI labelling pass labels them (see `DETAILS.md`). The dashboard
  stays complete either way.

## If a page shows a box instead of the dashboard

The box says what is wrong:

- **Still loading after 20 seconds:** it names the query it waits for. Check the name and that the query runs.
- **"La requête … n'a renvoyé aucune ligne":** the query runs but returns nothing. Check the sync.
- **"aucune NC lisible … colonnes reçues : …":** Slate passes the data in a form the page does not expect. Send the list of
  columns it shows.
- **"exactement N lignes reçues":** Slate probably cut the result. Look for a row limit on the query.
