# FTO2 NC dashboard: the update in a Code Repository

The update (the pipeline notebook) as a transform that Skywise runs on a schedule. Same code, same settings, same tables:
checked on the laptop, the transform writes exactly the notebook's tables (`tests/repository_rehearsal.py`).

## What goes where in the repository

| In this folder | In the repository |
|---|---|
| `transforms-python/src/fto2/` | the same place: the code (`fto2/*.py`), the settings (`fto2/settings/`), the station list (`fto2/files/`) |
| `transforms-python/src/myproject/datasets/fto2_update.py` | the same place: the transform |

## Steps

1. **Add the files** at the places above (Files panel, Add, Upload; or drag the folders in VS Code). Delete
   `myproject/datasets/lightweight-transform.py`: it declares the same tables.
2. **The station list.** Download `data/fto2_station_mapping.csv` from the notebook's Code Workspace and upload it into
   `src/fto2/files/`.
3. **Keep the settings with the code.** In `src/setup.py`, add this line under the line `packages=...`:

       package_data={"fto2": ["settings/*", "files/*"]},

4. **Libraries.** In the Libraries panel, add `pandas` and `pyarrow` if they are not listed (`polars` is there already).
5. **Commit**, and wait for the checks to pass.
6. **First build.** Build `fto2_dash_nc_test`. The build writes six tables ending in `_test` in the folder named on the
   line `FOLDER` of the transform, and its log prints the same lines as the notebook: compare the numbers of NCs, defect
   lines and the cost with the notebook's last run.
7. **Switch.** When they agree, write `TEST = ""` in the transform, commit, and build again: the transform now writes the
   tables the pages read. If the checks say a table is already produced elsewhere (by the notebook), keep `TEST = "_test"`
   and point the Postgres sync at the `_test` tables instead.
8. **Schedule.** On `fto2_dash_nc`, add a schedule (for example every weekday at 6:00). From then on, nobody needs to run
   the notebook.

## Optional inputs

One line each in the list of inputs of the transform, nothing else to change:

- **The settings kept in Fusion:** `fto2_set_targets`, `fto2_set_cost`, `fto2_set_blackout`, `fto2_set_deliveries`,
  `fto2_set_eqmsn`, `fto2_set_plant`, `fto2_set_part_prices`, `fto2_set_cables`, `fto2_set_gps`, `fto2_set_test`, for
  example `fto2_set_cost=Input("<the dataset of the sheet Cost rates and times>"),`. A sheet not listed: its file in
  `src/fto2/settings/` is used. The first lines of the build log say which settings came from Fusion.
- **The production plan:** `fto2_plan_exports`, a dataset holding the exports of the Tableau Avances / Retards as files,
  one per download, the date at the end of each name (`Avances_Retards_2026-11-03.csv`), the older ones kept. Not listed:
  the plan stays as it was last read (`src/fto2/settings/0_plan_msn.csv`).

## If the build fails

| The log says | What to do |
|---|---|
| the station list is missing | Step 2 |
| a settings table not found | Step 3: the line `package_data` |
| `No module named 'pandas'` | Step 4 |
| a parameter is missing in `compute` | add the input's name to the line `def compute(` of the transform, like the others |
| out of memory | ask for a bigger container for the transform |
