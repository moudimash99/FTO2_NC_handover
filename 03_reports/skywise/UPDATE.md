# Updating the installed dashboard (November 2026)

For a Skywise set-up that already runs: the notebook writes the four tables, the Slate app shows the dashboard and the MFT
page. Follow the steps in this order: the new pages need the data of the new update. Every file named here is in
`FTO2_Skywise_installation.zip`, at the same place.

What changes:
- The update runs in the Code Repository, on a schedule, instead of the notebook.
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

Fusion names each sheet's dataset after the spreadsheet and the sheet: *FTO2 NC Dashboard - Settings - Blackout days*. The
code calls each one by a short name:

| Sheet | Short name in the code | Read by |
|---|---|---|
| Target and pages | `fto2_set_targets` | the pages (step 4), through the sync |
| Cost rates and times | `fto2_set_cost` | the update (step 2) |
| Blackout days | `fto2_set_blackout` | the update |
| Part prices | `fto2_set_part_prices` | the update |
| Cable tracker | `fto2_set_cables` | the update |
| GPS register | `fto2_set_gps` | the update |
| Test list | `fto2_set_test` | the update |

In *Blackout days*, add this year's Christmas closure (one row: first day, last day, 0, the reason). Until it is there, the
update warns at its start and its end.

## 2. The update (the Code Repository)

The update now runs as a Python transform in the Code Repository, on a schedule: no notebook. Follow
`code_repository/README.md`, steps 1 to 11. Its step 12 is the sync below, its step 13 the pages of step 4, its step 14 the
schedule.

The tables now hold last year's NCs too: about twice the rows.

To stay on the notebook instead (the fallback): in the Code Workspace, replace `notebook_kit`, `data/config` and the notebook by
those of `level3_datasets/`, add the six Fusion datasets of the update to the Data panel, each under its short name (`fto2_set_cost`...), and run all
cells.

## 3. The sync to Postgres

- Point it at the four tables the transform writes: `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions`,
  `fto2_dash_ref`, schema `foundry_sync`, under the same names as today.

For the options of step 4 (they can come later), add two datasets, same schema:
- the dataset *FTO2 NC Dashboard - Settings - Target and pages*, under the name `fto2_set_targets`;
- the dataset the NC writer's action writes to (the output dataset set on the action of *a30 Nc Writer Dataset*), under the
  name `fto2_mft_store`. It holds the MFT actions.

## 4. Slate

Each page is a Slate app of its own: each app gets the queries its page reads (their texts are the `.sql` files named).

| App | Queries |
|---|---|
| The dashboard | `q_fto2_nc`, `q_fto2_def`, `q_fto2_dis`, `q_fto2_ref` (as before), `q_fto2_set_targets` |
| The MFT page | `q_fto2_nc`, `q_fto2_def`, `q_fto2_ref`, `q_fto2_set_targets`, `q_fto2_mft_store` |
| The NC writer | none |

`q_fto2_set_targets`: `level3_datasets/q_fto2_set_targets.sql`. `q_fto2_mft_store`: `mft/q_fto2_mft_store.sql`. If Slate says
a column does not exist, write its name as Postgres has it, between double quotes (`"Msn"`, `"Texte Sap"`).

**The dashboard** (right after the first sync of the new tables: the pages of before would count last year's NCs too)
1. Paste `level3_datasets/fto2_level23.css`, `.html` and `.js` into the sandbox's three tabs.
2. Paste `level3_datasets/state.json` into its state box (it holds the line `reglages`).

**The MFT page** (a sandbox named `w_fto2_mft`)
1. Paste `mft/fto2_mft.css`, `.html` and `.js` into its three tabs, and `mft/state.json` into its state box (it holds the
   lines `reglages` and `store`).
2. The saving of the actions: `README.md`, step 4, "Optional: the MFT actions kept for everyone", steps 1 to 9: the event
   `save` of the sandbox, the variable `v_mft_store`, the event that fills it, the Action widget, the event that runs
   `q_fto2_mft_store` after a save, and the event that submits the Action widget when `v_mft_store` changes (one click).

**The NC writer** (a sandbox named `w_nc_writer`)
1. Paste `nc_writer/nc_writer.html`, `.css` and `.js` into its three tabs; its state box: `{}`.
2. `nc_writer/README.md`, section 3, steps 1 to 4: the event `submit`, the variable `v_submission`, the Action widget, and the
   event that submits it when `v_submission` changes (one click).

If the Slate functions are set up on the dashboard, paste their three files again too
(`03_reports/skywise/level3_datasets/fonctions/` on GitHub). The Tableau Elizabeth is no longer used.

## 5. Checks

- The dashboard opens with the date *Données au…* of the latest NC and shows this year only. Deep dive › Pareto ends with
  *Les causes mois par mois*; every chart has an **⤓ Image** button; under *Détail des NC*, two CSV downloads.
- Change the target in the sheet *Target and pages* (for example 0.25 to 0.30), wait for the sheet to sync, reload the
  dashboard: Deep dive, the Production tab says *Objectif = taux* of last year *− 30 %*. Put the value back.
- The MFT page opens with *Responsabilité: FTO2*. On the *Suivi des actions* tab, change an action (for example its weekly
  point): a grey note shows while it is saved, then goes. Open the page on another computer: the change is there.
- The NC writer: write a test NC and press *Soumettre la NC*: the page says *NC envoyée*, and a new row is in the action's
  dataset.
