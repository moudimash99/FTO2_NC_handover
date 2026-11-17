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
8. **Two lines in `fto2_update.py`**, at the top:
   - `FUSION`: the folder that holds the six datasets of the Fusion spreadsheet: `fto2_set_cost`, `fto2_set_blackout`,
     `fto2_set_part_prices`, `fto2_set_cables`, `fto2_set_gps`, `fto2_set_test`. To find it: open one of them in Skywise
     and copy its folder's path. If one of them has another name or folder, write its own path on its line instead.
   - `FOLDER`: where the tables are written. Your own folder is fine for the test.
   - Leave `TEST = "_test"`.
9. **Commit**, then wait until the *Checks* tab is green.
10. **Test build.** With `fto2_update.py` open, press *Build* (right-hand panel) and choose `fto2_dash_nc_test`. It takes a
    few minutes. The log starts with *Settings from Fusion: ...* (one entry per sheet) and ends with the tables written.
    Open `fto2_dash_nc_test`: it holds this year's NCs and last year's.
11. **Switch.** In `fto2_update.py`, set `FOLDER` to the team's project folder and `TEST = ""`. Commit, then build
    `fto2_dash_nc`.
12. **The sync.** Point the Postgres sync at the four new tables `fto2_dash_nc`, `fto2_dash_defects`,
    `fto2_dash_disruptions`, `fto2_dash_ref`, under the same names as today.
13. **The pages.** Right after the first sync, paste the new files of the three pages (`UPDATE.md`, step 4): the pages of
    before would count last year's NCs too.
14. **Schedule.** On `fto2_dash_nc`, add a schedule, for example every weekday at 6:00. It must run under an account that
    stays (or the project's service account), never under the account of someone who leaves.
15. **The notebook** is no longer used. Keep its workspace as a backup; change the code here only.

## Later

- **The production plan.** Until it is set up, the plan stays as it was last saved (`src/fto2/settings/0_plan_msn.csv`).
  To read new exports of the Tableau Avances / Retards: put them, one file per download, in a dataset (the date at the end of
  each name, `Avances_Retards_2026-11-03.csv`; keep the older ones). In `fto2_update.py`, remove the `#` on the two lines
  `fto2_plan_exports` (one in the list of inputs, one under `def compute(`) and write that dataset's path. Commit.
- **A rule changed** (a table of `src/fto2/settings`): edit the table, commit, build. The settings people fill in by hand are
  in Fusion: nothing to commit for them.

## If something fails

| What you see | What to do |
|---|---|
| The checks fail on code style (*line too long*, *E501*...) | In `src/setup.cfg`, add the line `exclude = fto2` under `[flake8]` and under `[pycodestyle]`. In `src/.pylintrc`, under `[MASTER]`, add `ignore=fto2`. Commit again. |
| A dataset not found (`fto2_set_...`) | Step 8: the `FUSION` folder, or that dataset's own path on its line |
| `No module named` pandas, pyarrow or polars | Step 5 |
| A settings table not found | Step 6 |
| *The station list is missing* | Step 7 |
| At the switch: a table already made by another job | The notebook writes tables of those names in that folder: keep `TEST = "_test"` and point the sync at the `_test` tables, under the usual names |
| Out of memory | Ask for a bigger container for the transform |
