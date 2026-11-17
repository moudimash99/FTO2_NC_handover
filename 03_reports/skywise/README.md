# FTO2 NC dashboard in Skywise

**Everything to download is in one file: `FTO2_Skywise_installation.zip`** (in this folder, kept up to date by the build).

**Already installed? Follow `UPDATE.md`** (November 2026: the settings from Fusion, two years in the tables, the MFT actions
kept for everyone). This file sets everything up from nothing.

What you end up with: one notebook that writes four tables, and one Slate app with the dashboard (Essentiel and Deep dive in
one page) and the MFT page. The Tableau Elizabeth is optional. Every file named below is in this folder.

The settings (rules, rates, targets, production plan, MFT actions...) are the tables of `data/config/` in the notebook's
workspace: see `docs/comment_faire.md` at the top of the repository.

Details (what each level proves, what was tested): `DETAILS.md`.

## Set it up

**1. The notebook** (the Code Workspace where the pipeline notebook runs today)

1. Upload the whole folder `level3_datasets/notebook_kit` next to the notebook (the code).
2. Upload the folder `level3_datasets/config` into `data/`, so that it becomes `data/config/` (the rules, and the fallback
   values used when a Fusion dataset is not in the Data panel: the values people change are in the Fusion spreadsheet
   *FTO2 NC Dashboard - Settings*, `fusion/`). Uploading it again with a new version is safe.
   Put in `data/` the three files of the team, under the names of `data/config/2_sources.csv`: the station mapping
   `fto2_station_mapping.csv` (the notebook stops without it), the GPS register and the Test list (without them the
   notebook runs and says so). The `data/` folder also keeps the files the team downloads:
   the exports of the Tableau Avances / Retards (named `Avances_Retards...csv`; keep the earlier ones) and the export of
   the cable team's tracker (with `cables` in its name). The run reads the production plan and the cable requests from
   them; without any, it uses the tables `0_plan_msn.csv` and `0_demandes_cables.csv` of `data/config/`.
3. Upload `level3_datasets/notebook_kit/fto2_ai_labels.csv` once, as a dataset named `fto2_ai_labels` (3,489 rows).
   If the dataset exists already with fewer rows, give it the content of this file.
4. Replace the notebook by `level3_datasets/fto2_pipeline_notebook.ipynb` (a few lines: the steps are in `notebook_kit/fto2/`).
5. In the Data panel, add these datasets with these names:

   | Dataset | Name | |
   |---|---|---|
   | Non Conformity | `non_conformity` | read |
   | `fto2_ai_labels` | `fto2_ai_labels` | read |
   | Work_Order_Operation | `work_order_operation` | read |
   | MES Disruptions | `mes_disruptions` | read |
   | the Fusion settings (*FTO2 NC Dashboard - Settings - Cost rates and times*, *... - Blackout days*, *... - Part prices*, *... - Cable tracker*, *... - GPS register*, *... - Test list*) | `fto2_set_cost`, `fto2_set_blackout`, `fto2_set_part_prices`, `fto2_set_cables`, `fto2_set_gps`, `fto2_set_test` | read (each one optional) |
   | four new datasets | `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions`, `fto2_dash_ref` | write |

6. Run all cells. The last lines list the tables written.

While the old Slate app is still in use, the notebook also writes its four old outputs (they must then be in the Data
panel too). With no old app to feed, or once the new app has replaced it, set `garder_anciennes_sorties` to `non` in
`data/config/2_parametres.csv`.

A dataset missing from the Data panel stops the run where it is first read or written, with the error `AliasNotDefined`
and the list of the names the panel holds (`definedAliases`): add it under its name, then run all cells again.

**2. Sync** `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions` and `fto2_dash_ref` to Postgres, same names, schema
`foundry_sync`, as was done for `fto2_plant`.

**3. The dashboard page**

1. Create a new Slate app. Keep the old one until this one works.
2. Add four queries on `postgate-airbus-2`, named exactly: `q_fto2_nc`, `q_fto2_def`, `q_fto2_dis`, `q_fto2_ref`. Their text is
   in `level3_datasets/q_fto2_nc.sql`, `q_fto2_def.sql`, `q_fto2_dis.sql`, `q_fto2_ref.sql`.
3. Add a Code Sandbox, full width, about 1,400 px high.
4. Paste `level3_datasets/fto2_level23.css`, `fto2_level23.html` and `fto2_level23.js` into its CSS, HTML and JS tabs.
5. Paste `level3_datasets/state.json` into its state box (it shows `"input": "Hello World"` at first).

Check: the page opens with the date *Données au…* of the latest NC, on Série with Responsabilité FTO2 (the defaults);
Deep dive, Vue d'ensemble shows the year's NCs, defects and cost.

**Optional: the target and the filters at opening read from the Fusion sheet.** The Head of Quality fills the sheet "Target
and pages" of the Fusion spreadsheet (`fusion/`), synced to the dataset *FTO2 NC Dashboard - Settings - Target and pages*. With the three steps below the pages
read that sheet themselves: a change there shows the next time the page is opened, without waiting for the notebook.

1. Sync *FTO2 NC Dashboard - Settings - Target and pages* to Postgres under the name `fto2_set_targets`, schema
   `foundry_sync`, as the four tables.
2. Add a query `q_fto2_set_targets` on `postgate-airbus-2`. Its text is in `level3_datasets/q_fto2_set_targets.sql`.
3. In the dashboard's state box, add this line just after the first `{`: `"reglages": "{{q_fto2_set_targets}}",`

The page then takes from the sheet the target (`objectif_baisse`: 0.25, 0,25 or 25 % all mean 25 % fewer NCs), the filters at
opening (`defaut_phase`, `defaut_responsabilite`, `defaut_periode`) and the target of an MFT action (`action_objectif_baisse`,
`action_semaines_tenues`). A line missing or wrongly written keeps the notebook's value, and the browser's console (F12) says
which. Without the line in the state box, the page works as before.

Check: write 0.3 on the line `objectif_baisse` of the sheet, let the sync run, open the page again: Deep dive, the Production
tab says "Objectif = taux" of last year "− 30 %". Put 0.25 back afterwards.

**4. The MFT page** (a second page in the same app)

1. It uses the queries `q_fto2_nc`, `q_fto2_def` and `q_fto2_ref`: nothing to add.
2. Add a Code Sandbox, full width, about 1,400 px high, named `w_fto2_mft`. Paste `mft/fto2_mft.css`, `mft/fto2_mft.html`,
   `mft/fto2_mft.js` into its CSS, HTML and JS tabs, and `mft/state.json` into its state box.

Check: the page opens on the line with the most NCs, on the last full week, with Responsabilité FTO2.
The browser remembers the line last chosen.

With the Fusion sheet (optional, step 3): add the same line to this page's state box, `"reglages": "{{q_fto2_set_targets}}",`.
The MFT page takes the target of an action from it.

The MFT actions are the table `data/config/1_actions_mft.csv`: an action added there appears for everyone after the next run of
the notebook. An action typed on the MFT page itself stays in that browser only, until it is added to the table. Unless the
actions are kept for everyone, as below.

**Optional: the MFT actions kept for everyone.** The actions are then kept in one object of the NC writer's object type
"a30 Nc Writer Dataset" (its Msn is `MFT-ACTIONS`, its Texte Sap holds all the actions). It is saved the way the NC writer
saves an NC: the page hands over the whole list, and the user presses Submit in a save form. These are the steps tried with the
test box of `08_tools/mft_store_test/` (it used `w_store` and `v_store`).

1. In the MFT page's sandbox (`w_fto2_mft`), Interaction tab, Events: `["save"]`.
2. Variables panel: add `v_mft_store`, value `{}`.
3. Events panel: add an event. Trigger: `w_fto2_mft.save`. Action: `v_mft_store.set`. Code: `return ` followed by the binding
   of `slEventValue` (double curly braces) and `;`.
4. Under the page, add an Action widget with the action of the object type "a30 Nc Writer Dataset" (the NC writer's). In its
   default parameters, give each field the binding of `v_mft_store.<field>` (double curly braces), text fields between quotes:

   | Field of the action | Binding (inside double curly braces) |
   |---|---|
   | Detection | `v_mft_store.detection` |
   | Produit | `v_mft_store.produit` |
   | Msn | `v_mft_store.msn` |
   | Texte Sap | `v_mft_store.texte_sap` |
   | Total Defauts | `v_mft_store.total_defauts` (no quotes: a number) |

5. The dataset the action writes to (the one read back in the test): sync it to Postgres, schema `foundry_sync`, under the name
   `fto2_mft_store`.
6. Add a query `q_fto2_mft_store` on `postgate-airbus-2`. Its text is in `mft/q_fto2_mft_store.sql`.
7. Events panel: add an event. Trigger: the Action widget's submit, once it has succeeded (in the list of triggers, under the
   Action widget's name). Action: run the query `q_fto2_mft_store`. The page then reads the save at once. Without this event,
   it reads it the next time the page is opened.
8. In the MFT page's state box, add this line just after the first `{`: `"store": "{{q_fto2_mft_store}}",`

What the users see: a change on the "Suivi des actions" tab (a new action, an edit, a closing, a weekly point...) shows at once,
with a grey note saying to press Submit in the save form so that everyone sees it. After Submit, the note goes once the query
has read the save back. Several changes can wait for one Submit: the form always holds the whole list.

Check: close an action on the page, press Submit, open the page on another computer: the action is closed there too.

Good to know:

- At the start the store is empty: the page shows the actions of `1_actions_mft.csv`, and the first Submit keeps them in the
  store. From then on the page shows the store's actions: an action added to the table afterwards does not show. Type it on the
  page.
- Each Submit adds one object. The page takes the one saved last; the query reads the 20 latest. The objects written by the
  test box are not read.
- If two people change the actions at the same time, the one saved last wins.
- The "Vu" marks of the bell stay in each browser.
- If a column name is refused by the query, write it as Postgres has it, between double quotes (the comment at the top of the
  query says how).
- The page warns when the list of actions grows beyond 30,000 characters: the object may cut a longer text. Delete closed
  actions then.
- Without the line `"store"` in the state box, the page works as before (actions in each browser).

**5. The Tableau Elizabeth** (optional): a third page, same as the MFT with the files of `elizabeth/`.

Not needed: `level1_dummy_in_js` and `level2_dummy_queries` (tests on made-up data, only if something fails),
`level4_import` (untested).

**6. The NC writer** (optional): a page where an operator writes an NC with the official codes; each NC is saved as an
object of the object type "a30 Nc Writer Dataset" through its action. The files and the Slate set-up (a sandbox, an event,
a variable, the action) are in `nc_writer/` of the zip, its `README.md` section 3.

**7. Optional: the calculations in Slate functions.** The targets and forecast, the alarms and the cost explanation can run
as Slate functions instead of in the page, so that the page only draws. Two ways to set it up, both explained in
`level3_datasets/fonctions/README.md`. The page works without them. With the Fusion sheet (step 3), the page sends its target
to the functions with each request, so they compute with the sheet's target too.

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
2. The year is the line `annee` of `data/config/1_parametres.csv` (the change of 15 November below brings that table).
   With the former settings folder left as it is, the run takes the year of the line `date_debut` of `2_parametres.csv`.
3. Restart the kernel and run the notebook. Its first line says the year followed and the comparison year.
4. In Slate, once the sync has run: paste the new `fto2_level23.js` into the dashboard's sandbox, `mft/fto2_mft.js` into the
   MFT's and `elizabeth/fto2_elizabeth.js` into the Elizabeth's. No query changes.

Nothing changes on the pages for 2026: this only prepares the next years.

## Already set up? What to change (15 November: the settings in groups, the downloads read as they are)

Can be done together with the two changes above: it replaces their step 2.

1. Upload `level3_datasets/notebook_kit` again (the whole folder).
2. Replace the settings folder. **First download from `data/config/` any table changed there** (the price list
   `1_prix_pieces.csv` if prices were typed in). Then delete `data/config/` and upload `level3_datasets/config` in its
   place, and put the downloaded tables back. The tables now start with their group: `0_` data, `1_` the manager's
   settings, `2_` rules, `3_` expert (`docs/comment_faire.md`).
   The run also works with the former folder as it is (tables under their former names), so this step can wait.
3. From now on, the production plan and the cable requests are updated by saving a download in `data/`: an export of the
   Tableau Avances / Retards (name starting with `Avances_Retards`; keep the earlier ones) or of the cable team's tracker
   (with `cables` in its name). Nothing has to be saved today: the tables hold the plan of 3 November.
4. Restart the kernel and run the notebook. Its last lines say which year is followed and which downloads were read.
5. In Slate: nothing more than the JS files of the change above.

## Already set up? What to change (17 November: the Fusion sheet read by the pages, the MFT actions kept for everyone)

The whole update of November, in order (Fusion, the notebook, the sync, Slate): `UPDATE.md`.

Both are options. Without them the pages work as before, so step 1 alone is enough.

1. In Slate: paste the new `level3_datasets/fto2_level23.js` into the dashboard's sandbox and `mft/fto2_mft.js` into the
   MFT's (the MFT's CSS and HTML changed only in their first line). With the Slate functions (step 7), paste the three
   function files again too: the page now sends its target with each request.
2. To read the target and the filters at opening from the Fusion sheet: step 3, "Optional: the target and the filters at
   opening read from the Fusion sheet", then the same state line for the MFT page (step 4).
3. To keep the MFT actions for everyone: step 4, "Optional: the MFT actions kept for everyone".

## Keep it up to date

- **New NCs:** run the update (the notebook, or the transform once it runs on a schedule). The pages follow once the sync
  has run.
- **A new year** (each January): nothing to write, the year followed changes by itself (the line `annee` of
  `1_parametres.csv` stays empty). In the Fusion spreadsheet, add the new year's blackout days (sheet *Blackout days*) and
  its GPS register (sheet *GPS register*); save a fresh export of the Tableau Avances / Retards in `data/`, keeping the older
  ones; run the update. Nothing to paste in Slate. The details: `docs/comment_faire.md` ("Commencer une nouvelle année").
- **A setting people change** (the cost rates, the part prices, the blackout days, the lists): in the Fusion spreadsheet,
  then run the update. The target, the filters at opening and the target of an MFT action: the sheet "Target and pages",
  read by the pages themselves (step 3): a change shows the next time the page is opened, once Fusion has synced.
- **A rule** (the exclusions, the NC types, the causes...): its table in `data/config/`, then run the update.
- **An MFT action:** on the MFT page itself, with the actions kept for everyone (step 4); otherwise in
  `data/config/1_actions_mft.csv`, then run the update.
- **The production plan, the cable requests:** save the new download in `data/` and run the notebook.
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
- **"Les actions partagées ne sont pas encore lues"** (MFT page, actions kept for everyone): the query `q_fto2_mft_store`
  gave nothing after 20 seconds. Check that it runs: its table name, and the column names (step 4).
