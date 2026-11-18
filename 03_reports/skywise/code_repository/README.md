# FTO2 NC dashboard: the update in the Code Repository

The update that writes the dashboard's tables, as one Python transform that Skywise runs on a schedule. It replaces the
notebook: same code, same settings, same tables (checked on the laptop, `tests/repository_rehearsal.py`).

## What changes in the repository

```
transforms-python/
  conda_recipe/meta.yaml           3 lines added (step 5)
  src/
    fto2/                          NEW: the code, its settings (settings/) and the station list (files/)
    myproject/datasets/
      fto2_update.py               NEW: the transform
      lightweight-transform.py     DELETE: the empty example
    setup.py                       1 line added (step 6)
```

Everything else stays as it is.

## Steps

0. **The repository must sit in the team's project**, the project where the tables are written (for example
   *protected › Qualité › NC Dashboard › For Developer*): Skywise only lets a repository write tables inside its own project,
   and a repository in a personal folder stops with its owner. To make one there: open that folder, *New* › *Code
   repository*, Python transforms.
1. **Start clean.** If the right-hand panel says *Conflicting remote changes*, press *Review and discard changes* (or *Merge
   and resolve* if you have changes to keep). The status bar should no longer show commits waiting (the arrows at the bottom).
2. **Delete the example.** Right-click `src/myproject/datasets/lightweight-transform.py`, Delete.
3. **Add the code.** From this zip, drag the folder `transforms-python/src/fto2` onto `src` in the Explorer. It must sit next
   to `myproject`, not inside it.
4. **Add the transform.** Drag `transforms-python/src/myproject/datasets/fto2_update.py` onto `src/myproject/datasets`.
5. **The libraries.** Open `conda_recipe/meta.yaml`. Under `run:`, after the last line, add these three lines, with the same
   indentation as the lines above:

       - pandas
       - pyarrow
       - polars

6. **Keep the settings with the code.** Open `src/setup.py`. After the line `install_requires=[],` add this line:

       package_data={"fto2": ["settings/*", "files/*"]},

7. **The station list.** In the old Code Workspace, download `data/fto2_station_mapping.csv`, and drag it onto
   `src/fto2/files`.
8. **The lines at the top of `fto2_update.py`** already hold the team's folders: `FOLDER`, where the tables are written
   (*protected › Qualité › NC Dashboard › For Developer › Datasets*), and `FUSION`, the *Fusion Sheets* folder in it, which
   holds the datasets of the Fusion spreadsheet (*FTO2 NC Dashboard - Settings - Blackout days*...). Change them only if
   those folders move; then copy the path, do not type it. If one dataset was renamed or moved, write its id (*Copy RID*)
   on its own line instead.
   - Leave `TEST = "_test"`.
9. **Commit**, then wait until the *Checks* tab is green.
10. **Test build.** With `fto2_update.py` open, press *Build* (right-hand panel) and choose `fto2_dash_nc_test`. It takes a
    few minutes. The log starts with *Settings from Fusion: ...*, then one line for each sheet pasted whole (*Fusion
    sheet GPS register: header on row 4, 812 rows*), and ends with the tables written. A line that starts with ⚠️ names a
    sheet the update could not use, and why. Open `fto2_dash_nc_test`: it holds this year's NCs and last year's.
11. **Switch.** In `fto2_update.py`, set `TEST = ""`. Commit, then build `fto2_dash_nc`.
12. **The sync.** Point the Postgres sync at the four new tables `fto2_dash_nc`, `fto2_dash_defects`,
    `fto2_dash_disruptions`, `fto2_dash_ref`, under the same names as today.
13. **The pages.** Right after the first sync, paste the new files of the three pages (`UPDATE.md`, step 4): the pages of
    before would count last year's NCs too.
14. **Schedule.** Best done by the person who takes over (a schedule runs under its owner's account):
    - open the dataset `fto2_dash_nc`, then *Schedules* (or, in Data Lineage, select it and open the *Schedules* panel),
      and create a new schedule;
    - *Trigger*: time, every weekday (Monday to Friday) at 6:00, time zone Europe/Paris;
    - *Target*: `fto2_dash_nc` alone: build only this dataset, not what is upstream (the source data belongs to other
      teams). The one build writes all six tables;
    - if offered, make it run for the project (project scope) rather than as a person, and tick the notification on
      failure for the owner;
    - name it *FTO2 NC dashboard - daily update* and save. Check the next morning: the build ran (the *Builds* history)
      and the dashboard's date *Données au…* moved.
15. **The notebook** is no longer used. Keep its workspace as a backup; change the code here only.

## Later

- **The production plan:** download the export of the Tableau Avances / Retards as a CSV, as it is, and name it
  `Avances_Retards_<date of the export>.csv` (for example `Avances_Retards_2026-11-18.csv`). Upload it into `src/fto2/files/`,
  beside the station list and the older exports (keep them: the newest wins, an aircraft it no longer lists keeps its last
  line), commit, build. Check before: the first row of each aircraft holds dates, not `#REF!` (download from the original
  Tableau, not a copy).
- **The cable tracker, the GPS register, the Test list:** empty the Fusion sheet, paste the whole Google sheet there, as it
  is, from cell A1, then build (or wait for the schedule). Nothing to delete or rename: the update finds the header row
  itself.
- **A rule changed** (a table of `src/fto2/settings`): edit the table, commit, build. The settings people fill in by hand are
  in Fusion: nothing to commit for them.

## If something fails

| What you see | What to do |
|---|---|
| The checks fail on code style (*line too long*, *E501*...) | In `src/setup.cfg`, add the line `exclude = fto2` under `[flake8]` and under `[pycodestyle]`. In `src/.pylintrc`, under `[MASTER]`, add `ignore=fto2`. Commit again. |
| *Alias ... does not exist* (*FTO2 NC Dashboard - Settings - ...*) | Step 8: copy the `FUSION` folder's path again (ending with `/`), or put each dataset's id on its line. *... - Production plan*: the sheet and its sync are not made yet (`UPDATE.md`, step 1) |
| *⚠️ Fusion sheet ... NOT USED* in the log, or the cables or the plan not updated on the dashboard | The line says why (the columns it did not find) and what was kept instead. Empty the sheet and paste the whole sheet again, as it is, from A1. If a column was renamed at the source, the line names it: tell the developer |
| *... could not be created since the user is not authorized. Datasets can only be created in the same project as the code repository* | Step 0: the repository is outside the project of `FOLDER` (a personal folder, for example) |
| An input of another project must be added to the project | Accept the offer to add it to the project's references (a project owner may have to approve) |
| `No module named` pandas, pyarrow or polars | Step 5 |
| A settings table not found | Step 6 |
| *The station list is missing* | Step 7 |
| At the switch: a table already made by another job | The notebook writes tables of those names in that folder: keep `TEST = "_test"` and point the sync at the `_test` tables, under the usual names |
| Out of memory | Ask for a bigger container for the transform |
