# Updating the installed dashboard (November 2026)

For a Skywise set-up that already runs: the notebook writes the four tables, the Slate app shows the dashboard and the MFT
page. Follow the steps in this order: the new pages need the data of the new update. Every file named here is in
`FTO2_Skywise_installation.zip`, at the same place.

What changes:
- The settings people fill in by hand come from the Fusion spreadsheet *FTO2 NC Dashboard - Settings*.
- The tables hold two years, the comparison year and the year followed; each page chooses what it shows.
- The target and the pages' opening view are read by the pages straight from Fusion: a change shows at the next reload,
  without an update.
- The MFT actions are kept for everyone, in the NC writer's object type.
- The MFT page has the dashboard's *Responsabilité* list (FTO2 ticked at first).
- An NC written with the NC writer is read line by line: each defect takes the cause of its official code.
- The year follows the calendar: nothing to change in January.

## 1. Fusion

The spreadsheet has seven sheets. If an earlier version had the sheets *Planned volume*, *Deliveries last year* or *Plant*,
delete them: nothing reads them any more.

| Sheet | Dataset | Read by |
|---|---|---|
| Target and pages | `fto2_set_targets` | the pages (step 4) |
| Cost rates and times | `fto2_set_cost` | the update (step 2) |
| Blackout days | `fto2_set_blackout` | the update |
| Part prices | `fto2_set_part_prices` | the update |
| Cable tracker | `fto2_set_cables` | the update |
| GPS register | `fto2_set_gps` | the update |
| Test list | `fto2_set_test` | the update |

In *Blackout days*, add this year's Christmas closure (one row: first day, last day, 0, the reason). Until it is there, the
update warns at its start and its end.

## 2. The update (the notebook)

1. Unzip `FTO2_Skywise_installation.zip` on your computer.
2. In the Code Workspace, delete the folder `notebook_kit`, then upload `level3_datasets/notebook_kit` in its place.
3. Delete `data/config`, then upload `level3_datasets/config` into `data/`. This is safe now: the values people change are
   in Fusion; these files hold the rules, and the fallback values used when a Fusion dataset is not in the Data panel.
4. Replace the notebook by `level3_datasets/fto2_pipeline_notebook.ipynb`: it reads the Fusion settings first.
5. In the Data panel, add the six datasets that the update reads (table above), each under its own name: `fto2_set_cost`,
   `fto2_set_blackout`, `fto2_set_part_prices`, `fto2_set_cables`, `fto2_set_gps`, `fto2_set_test`.
6. Run all cells. The first lines list the settings taken from Fusion, one line per dataset. The last lines list the tables
   written, then `Done.`.

The four tables now hold last year's NCs too: about twice the rows.

## 3. The sync to Postgres

Add two datasets to the sync, schema `foundry_sync`, as the four tables:
- `fto2_set_targets` (the sheet *Target and pages*), same name;
- the dataset the NC writer's action writes to (the output dataset set on the action of *a30 Nc Writer Dataset*), under the
  name `fto2_mft_store`. It holds the MFT actions.

## 4. Slate

The two lines below go in a sandbox's state box by hand, just after the first `{`: pasting `state.json` does not add them.

**The dashboard**
1. Paste `level3_datasets/fto2_level23.css`, `fto2_level23.html` and `fto2_level23.js` into the sandbox's three tabs.
2. Add the query `q_fto2_set_targets` on `postgate-airbus-2`. Its text: `level3_datasets/q_fto2_set_targets.sql`.
3. In the sandbox's state box, add the line `"reglages": "{{q_fto2_set_targets}}",`

**The MFT page** (the sandbox `w_fto2_mft`)
1. Paste `mft/fto2_mft.css`, `fto2_mft.html` and `fto2_mft.js` into its three tabs.
2. In its state box, add the same line `"reglages": "{{q_fto2_set_targets}}",`
3. Set up the saving of the actions: `README.md`, step 4, "Optional: the MFT actions kept for everyone", its eight steps. In
   short: the sandbox's event `save`; the variable `v_mft_store`; an event that fills it; under the page, an Action widget
   with the NC writer's action, its fields bound to `v_mft_store`; the query `q_fto2_mft_store` (its text:
   `mft/q_fto2_mft_store.sql`); an event that runs the query once Submit has succeeded; and in the state box the line
   `"store": "{{q_fto2_mft_store}}",`. The sync of its step 5 is the one of step 3 above.

**The NC writer**
1. Paste `nc_writer/nc_writer.js` into its sandbox's JavaScript tab (the products CA, CA Superior and Element OTP are in the
   list).

## 5. Checks

- The dashboard opens with the date *Données au…* of the latest NC. Deep dive › Pareto ends with *Les causes mois par mois*;
  the main charts have a **PNG** button.
- Change the target in the sheet *Target and pages* (for example 0.25 to 0.30), wait for the sheet to sync, reload the
  dashboard: Deep dive, the Production tab says *Objectif = taux* of last year *− 30 %*. Put the value back.
- The MFT page opens with *Responsabilité: FTO2*. On the *Suivi des actions* tab, change an action (for example its weekly
  point): a grey note asks for Submit. Press **Submit** in the save form under the page; the note goes. Open the page on
  another computer: the change is there.
- The NC writer opens on *Nouvelle NC*, with CA Superior in the list of products.

## Later: the update on a schedule

`code_repository/README.md`: the same update as a transform of a Code Repository, which Skywise runs on a schedule. Add the
six Fusion datasets of step 2 as inputs, one line each. Once it runs, stop using the notebook: one copy of the code only.
