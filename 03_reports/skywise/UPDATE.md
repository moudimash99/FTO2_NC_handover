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

## 2. The update (the Code Repository)

The update now runs as a Python transform in the Code Repository, on a schedule: no notebook. Follow
`code_repository/README.md`, steps 1 to 11. Its step 12 is the sync below, its step 13 the pages of step 4, its step 14 the
schedule.

The tables now hold last year's NCs too: about twice the rows.

To stay on the notebook instead (the fallback): in the Code Workspace, replace `notebook_kit`, `data/config` and the notebook by
those of `level3_datasets/`, add the six Fusion datasets to the Data panel under their own names, and run all cells.

## 3. The sync to Postgres

- Point it at the four tables the transform writes: `fto2_dash_nc`, `fto2_dash_defects`, `fto2_dash_disruptions`,
  `fto2_dash_ref`, schema `foundry_sync`, under the same names as today.

For the options of step 4 (they can come later), add two datasets, same schema:
- `fto2_set_targets` (the sheet *Target and pages*), same name;
- the dataset the NC writer's action writes to (the output dataset set on the action of *a30 Nc Writer Dataset*), under the
  name `fto2_mft_store`. It holds the MFT actions.

## 4. Slate

**Needed, right after the first sync.** Paste the new CSS, HTML and JS of the three pages into their sandboxes' three tabs:
the dashboard (`level3_datasets/fto2_level23.*`), the MFT page (`mft/fto2_mft.*`), the Tableau Elizabeth
(`elizabeth/fto2_elizabeth.*`). The state boxes stay as they are. If the Slate functions are set up, paste their three files
again too (`03_reports/skywise/level3_datasets/fonctions/` on GitHub). The pages of before would count last year's NCs as well.

**Options, they can come later.** The lines below go in a sandbox's state box by hand, just after the first `{`.

*The target and the opening view read from Fusion* (the sync of `fto2_set_targets` first, step 3):
1. Add the query `q_fto2_set_targets` on `postgate-airbus-2`. Its text: `level3_datasets/q_fto2_set_targets.sql`.
2. In the dashboard's state box, and in the MFT page's, add the line `"reglages": "{{q_fto2_set_targets}}",`

*The MFT actions kept for everyone* (the sync of `fto2_mft_store` first, step 3): `README.md`, step 4, "Optional: the MFT
actions kept for everyone", its eight steps. In short: the sandbox's event `save`; the variable `v_mft_store`; an event that
fills it; under the page, an Action widget with the NC writer's action, its fields bound to `v_mft_store`; the query
`q_fto2_mft_store` (its text: `mft/q_fto2_mft_store.sql`); an event that runs the query once Submit has succeeded; and in
the MFT page's state box the line `"store": "{{q_fto2_mft_store}}",`.

*The NC writer*: paste `nc_writer/nc_writer.js` into its sandbox's JavaScript tab (the products CA, CA Superior and Element
OTP are in the list).

## 5. Checks

- The dashboard opens with the date *Données au…* of the latest NC. Deep dive › Pareto ends with *Les causes mois par mois*;
  the main charts have a **PNG** button.
- With the Fusion option: change the target in the sheet *Target and pages* (for example 0.25 to 0.30), wait for the
  sheet to sync, reload the dashboard: Deep dive, the Production tab says *Objectif = taux* of last year *− 30 %*. Put the
  value back.
- The MFT page opens with *Responsabilité: FTO2*. With the actions kept for everyone: on the *Suivi des actions* tab,
  change an action (for example its weekly point): a grey note asks for Submit. Press **Submit** in the save form under the page; the note goes. Open the page on
  another computer: the change is there.
- The NC writer opens on *Nouvelle NC*, with CA Superior in the list of products.
