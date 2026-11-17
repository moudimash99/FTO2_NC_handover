# Updating the installed dashboard (November 2026)

For a Skywise set-up that already runs: the notebook writes the four tables, the Slate app shows the dashboard and the MFT
page. Follow the steps in this order: the new pages need the data of the new update. Every file named here is in
`FTO2_Skywise_installation.zip`, at the same place.

What changes:
- The settings people fill in by hand come from the Fusion spreadsheet *FTO2 NC Dashboard - Settings*.
- The tables hold two years, the comparison year and the year followed; each page chooses what it shows.
- The target and the pages' opening view are read by the pages straight from Fusion: a change shows at the next reload,
  without an update.
- The MFT actions are kept for everyone, in one object of the NC writer's object type.
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

Add two datasets to the sync, schema `foundry_sync`, same names:
- `fto2_set_targets` (the sheet *Target and pages*);
- the dataset the NC writer's action writes to (the output dataset you set on the action; it holds the MFT actions).

## 4. Slate

**The dashboard**
1. Paste `level3_datasets/fto2_level23.css`, `fto2_level23.html` and `fto2_level23.js` into the sandbox's three tabs.
2. Add the query `q_fto2_set_targets` (its text: `level3_datasets/q_fto2_set_targets.sql`).
3. Paste `level3_datasets/state.json` into the sandbox's state: it adds the key `reglages`.

**The MFT page**
1. Paste `mft/fto2_mft.css`, `fto2_mft.html` and `fto2_mft.js`.
2. Set up the saving of the actions: see `mft/README.md`, "The MFT actions, kept for everyone".

**The NC writer**
1. Paste `nc_writer/nc_writer.js` (the products CA, CA Superior and Element OTP are in the list).

## 5. Checks

- The dashboard opens with the date *Données au…* of the latest NC. Deep dive › Pareto ends with *Les causes mois par mois*;
  the main charts have a **PNG** button.
- Change the target in the sheet *Target and pages* (for example 0.25 to 0.30), wait for the sheet to sync, reload the
  dashboard: the target's texts and lines follow. Put the value back.
- The MFT page lists the actions. Change one, press **Submit** in the save form, reload: the change is there, for everyone.

## Later: the update on a schedule

`code_repository/README.md`: the same update as a transform of a Code Repository, which Skywise runs on a schedule. Add the
six Fusion datasets of step 2 as inputs, one line each. Once it runs, stop using the notebook: one copy of the code only.
