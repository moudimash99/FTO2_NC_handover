# Logic: how the update's code works

The logic is everything the update does: it reads the NCs from Skywise, decides which ones count, reads their defects,
labels them, works out their cost, and writes the tables the pages read. It runs as a transform of the Code Repository, on a
schedule. This guide explains that code.

The three guides of the code: *The settings, table by table* (the settings), *The update, step by step* (this one) and
*The pages, in detail* (the pages' code). The part prices have a guide of their own: *Part prices*.

**Contents**

1. [The big picture](#1-the-big-picture)
2. [Where the code is](#2-where-the-code-is)
3. [The run, step by step](#3-the-run-step-by-step)
4. [Each file explained](#4-each-file-explained)
5. [The tables it writes](#5-the-tables-it-writes)
6. [Changing the logic](#6-changing-the-logic)
7. [When the update stops](#7-when-the-update-stops)

---

## 1. The big picture

```
 Skywise datasets                          the settings
   non_conformity        (the NCs)           Fusion: FTO2 NC Dashboard - Settings
   fto2_ai_labels        (the AI labels)     src/fto2/settings/ (the tables)
   work_order_operation  (rework orders)     src/fto2/files/ (stations, production plan)
   mes_disruptions       (aléas)                   |
            \                                      /
             THE UPDATE: fto2_update.py  ->  src/fto2/  (the code)
                                   |
   fto2_dash_nc           one row per NC
   fto2_dash_defects      one row per defect line
   fto2_dash_disruptions  the quality aléas that led to no NC
   fto2_dash_ref          everything else the pages need (production plan, comparison year, settings...)
                                   |
                         synced to Postgres -> read by the Slate pages
```

**The rule of the split:** the logic decides and calculates (which NC counts, what each defect is, what it costs). The pages
only filter, add up and draw. So a number that is wrong on every view of the dashboard is a logic question; a number that is
wrong only on one chart is a page question.

## 2. Where the code is

In the Code Repository:

| What | Where |
|---|---|
| The transform | `src/myproject/datasets/fto2_update.py`: it lists the inputs (the four Skywise datasets, six sheets of the Fusion spreadsheet) and the outputs (the four tables, two work lists), then calls the code. Skywise runs it on a schedule; to run it at once, build `fto2_dash_nc`. |
| The code | `src/fto2/`: plain Python, one file per subject. |
| The settings | The Fusion spreadsheet *FTO2 NC Dashboard - Settings*, and the tables of `src/fto2/settings/` (see *The settings, table by table*). |
| The files kept with the code | `src/fto2/files/`: the station list (`fto2_station_mapping.csv`) and the exports of the production plan (`Avances_Retards_<date>.csv`). |

**The fallback.** The pipeline notebook, in a Code Workspace, runs the same code (`notebook_kit/fto2/`, its settings in
`data/config/`). It is only a fallback: change the code in the Code Repository only, or the two copies drift apart.

The files of `src/fto2/`:

| File | In one sentence |
|---|---|
| `skywise.py` | The run: reads the datasets, calls everything else in order, writes the tables. **Start reading here.** |
| `transform_io.py` | Links the transform's inputs and outputs to the run, so that the transform and the notebook run the same steps. |
| `fusion.py` | Reads the sheets of the Fusion spreadsheet, before anything else. |
| `config.py` | Reads the settings tables and stops with a clear message when one is badly filled. |
| `rules.py` | The rule engine: applies a rule table (`2_regle_*.csv`) to the NCs. |
| `selection.py` | Which NCs count, and the labels each NC gets from the rule tables. |
| `manual_lists.py` | Reads the GPS register and the Test list. |
| `parser/` | The defect reader: turns an NC's long text into defect lines. |
| `core.py` | From the NCs to the dashboard's tables: defects, labels, rework orders, aléas, cost, scope. |
| `cost/` | The cost model, with the rework orders, the aléas and the part prices. |
| `reference.py` | Everything the pages need besides the NC tables (production plan, comparison year, cables, actions, settings). |
| `downloads.py` | Reads the production plan's exports and the cable team's tracker, as they come. |

## 3. The run, step by step

`skywise.py`, function `run`. The run prints each step in the build's log while it runs, so the last line printed says where
it is.

**0. The settings** (`fusion.py`, then `check_settings`)

1. The sheets of the Fusion spreadsheet first: each sheet filled by hand replaces its settings table for this run, and each
   sheet pasted whole becomes the list the run reads (section 4). The first lines of the log say which sheets were used
   (*Settings from Fusion: …*, *Fusion sheet GPS register: header on row 4, 812 rows*), and which were not, and why.
2. Every setting is then read and checked, before anything is fetched: a mistake stops the run here, in seconds, with
   nothing written. The cause tree of the Définitions tab is checked against the code, and a missing closure in the blackout
   days is reported.

**A. The standard selection** (`select_ncs`, then `selection.apply_rules`)

1. Reads the NCs of the plant created since 1 January of the comparison year, so both years (`2_parametres.csv`: `usine`;
   `1_parametres.csv`: `annee`), plus the NCs of other plants where the plant is liable. Skywise is asked for the NCs created
   from that day (`config.first_day_read`); the NCs created after 31 December of the year followed are cut in Python
   (`skywise._until`), because Skywise's filter fails on three conditions joined with `&`.
2. Leaves out the excluded ones (`2_regle_exclusion.csv`: ERMA, NCs deleted at another plant).
3. Adds the labels from the rule tables, in this order: phase (`2_regle_phase.csv`), decision label (`2_decisions.csv`),
   origin (`2_regle_origine.csv`), type (`2_regle_type_nc.csv`, which uses the origin), product (`2_regle_produit.csv`).

**B. The manual lists** (`manual_lists.py`): the NCs of the GPS register and the Test list, dated in the year followed, that
step A missed are fetched by number, then go through the same rules.

**C. The former outputs**: the scheduled update never writes the former Slate app's four tables. Only the pipeline notebook
still writes them, while `garder_anciennes_sorties` is `oui`.

**D. The dashboard tables** (`core.build`, which calls `core.prepare` then `core.tables`):

1. **Defects:** the defect reader splits each NC's long text into defect lines (`parser/`). A400M NCs have no long text: one
   line is made from the title (`core.title_lines`, `3_a400m_titres.csv`).
2. **Rework orders:** the NC's rework orders, their state and planned time (`cost/orders.py`).
3. **Aléas:** the quality aléa that led to each NC and its declared time, and the aléas that led to no NC
   (`cost/disruptions.py`).
4. **Labels:** each defect line takes its AI label from `fto2_ai_labels`, **only if the line's text is still the same as when
   it was labelled**. Otherwise it keeps the defect reader's label and is listed "to label". A code written in the NC by a
   person wins over the label: written with the NC writer, the whole sub-code (Q03-006) decides the line; typed by hand, the
   code counts by its family (Q03), and a label from another family gives way to it. Then the category, cause, "minor" flag
   and official sub-code follow from the label.
5. **Part prices:** the NC data names the part each NC is about (column `material`); its price comes from the sheet *Part
   prices*, else `1_prix_pieces.csv` (`cost/parts.py`). The materials still without a price make the work list
   `fto2_parts_to_price`.
6. **Cost:** the cost model runs on every NC (`cost/model.py`, section 4).
7. **Scope:** where each NC was raised: `serie`, `client` (customer return), `autre` (`2_regle_perimetre.csv`).
8. **Tables:** `core.tables` puts it all into the two tables, column by column, and `core.dis_table` makes the aléa table.
9. **Lines to label:** `core.lines_to_label` makes the work list `fto2_lines_to_label`: the lines without a usable AI label,
   with their full text, ready for the next labelling pass.

**E. The reference data** (`reference.py`): the production plan; the comparison year (the year before the one followed,
unless `annee_comparaison` names another), summed per month from the NCs processed in step D, so both years go through the
same rules, defect reader, part prices and cost model; its volume, measured as the year followed's (section 4, `deliveries`);
the cable requests, the MFT actions, the cost settings, the cause tree, the page settings, and the working weight of each day
and week of both years (from the blackout days). They are packed into `fto2_dash_ref` (section 5).

**The year.** Every date of the run comes from one line, `annee` in `1_parametres.csv` (empty: the current year), through six
functions of `config.py`: `year()`, `comparison_year()`, `first_day()` (1 January of the year followed), `first_day_read()`
(1 January of the comparison year, the first day read), `year_end()` (1 January of the next year) and `aleas_since()`
(1 December before the first year read: an NC of early January can follow an aléa of late December). No year is written in
the code: keep it that way. When the year followed is over, the last lines of the run say so and name the line to change.

## 4. Each file explained

### `fusion.py`: the Fusion sheets

Runs first, before the rest of the code is read. For each sheet the update is given (the inputs `fto2_set_…` of the
transform):

- a sheet filled by hand (*Cost rates and times*, *Blackout days*, *Part prices*) replaces its table of `src/fto2/settings/`
  for this run, on a working copy: the table itself is not changed, and stays the fallback;
- a sheet pasted whole (*Cable tracker*, *GPS register*, *Test list*) is read as the sheet it comes from: its header row is
  the first of its first rows that holds every column the run reads; the title rows above it, the other columns and the
  empty rows are left out.

Column names are matched loosely (case, accents, spaces, signs). A sheet with a column missing, or with its first row only,
is not used: the run says which, and why, and keeps the table or the list it had. A pasted sheet it cannot use is said
loudly, at the start and again at the end of the run (*⚠️ Fusion sheet … NOT USED*). The seventh sheet, *Target and pages*,
is not an input of the update: the pages read it themselves.

### `transform_io.py`: the transform and the run

Gives the run its inputs and outputs, so that the same steps run in the transform and in the notebook. It also puts the files
of `src/fto2/files/` where the run looks for them, and stops with "the station list is missing" when
`fto2_station_mapping.csv` is not there.

### `config.py`: reading the settings

- `table(name, columns)`: a settings table as text, after checking that it exists, that every line has the right number of
  columns, and that the expected columns are there.
- `parameter(name, table)`: one value of a name-and-value table (`2_parametres.csv` by default). `parameter_list` splits it on
  `|`; `parameter_yes` reads `oui` / `non`; `optional` gives `''` for a line that is empty or left out.
- Two of these tables are in two parts (`SPLIT`): the manager's lines are in `1_parametres.csv` and `1_reglages_pages.csv`,
  the technical ones in the `2_` table of the same name. `parameter` looks in both; `held_by` says which part holds a line,
  so that an error names the right table.
- `path(name)`: where a table is. A settings folder made before the tables were regrouped holds some under their former
  names: a table not found under its name is taken under its former one (`FORMER`).
- `year`, `comparison_year`, `first_day`, `first_day_read`, `year_end`, `aleas_since`: the year followed and the dates tied
  to it.
- `number`, `day`: a number or a date as a person types it (`0,25`; `31/01/2026`).
- `rule_table(name, columns)`: a rule table, checked by `rules.check`.
- `mapping(name, key, value)`: a two-column table as a lookup, with its `(autre)` row as the default.
- `folder()`: where the settings are (`src/fto2/settings/` in the Code Repository; a working copy of it once the Fusion
  sheets are read).

### `rules.py`: the rule engine

One function applies every rule table, so they all behave the same way (the way is explained in *The settings, table by
table*, section 4).

- `check(table, name, columns)`: lists every problem in plain words (an unknown test, a missing default rule, a bad regular
  expression, a column that isn't in the NC data).
- `apply(df, table, name)`: for each NC, tries the rules in `ordre`; the rows of one rule must all be true; the first rule that
  holds gives the result; `toujours` gives the default. The tests themselves are in `_condition`.

### `selection.py`: which NCs count, and their labels

- `exclusions(df)`: True for the NCs to leave out.
- `add_columns(df)`: adds `Programme_auto` (the phase), `Statut_decision_auto`, `Origin_auto`, `Type_NC_auto` (which uses the
  origin) and `Produit_auto`.
- `apply_rules(raw, station_desc)`: both, on a raw NC extract. It also adds each station's description (from the station
  list), which the product rules read.

### `manual_lists.py`: the GPS register and the Test list

Reads both lists, as their Fusion sheets give them (`2_sources.csv` names the columns that hold the NC number and the date,
and the list used when a sheet cannot be read; `{annee}` in a name stands for the year followed), keeps the NCs dated in the
year followed, and marks each NC with the list it is on (`Ext_Source`: `GPS`, `Test`, or none).

### `parser/`: the defect reader

- `nc_defect_parser.py`: reads an NC's long text. It finds the defects written in it (numbered lists, the writing standard's
  template, a line joining two defects with "+"), then gives each defect a **sub-category** from the official codes written in
  the text, or from keywords. Expert rules, with priorities (cable first, then connection, then unlocked contact).
- `fto2_logic.py`: wraps the reader for the rest of the code: `build_defects` (one row per defect), `build_nc` (one row per
  NC with its defect counts), `line_of` (the aircraft line of a programme, `2_regle_ligne.csv`), and the cause names
  (`2_causes_noms.csv`).

### `core.py`: from the NCs to the dashboard tables

- `check_cause_tree`: the cause tree of the Définitions tab (`3_sous_categories.csv`) says what the code decides; the run
  stops if the two differ.
- `prepare`: steps D1 to D7 above.
- `official_subcode`: the official sub-code of each defect line, from its label.
- `title_lines`: the A400M lines read from the NC title.
- `nc_extras`: the NC fields the charts need (MSN, product, station, creation hour, days to close, open or not, age, NC type,
  liability, SAP codes, data source, the cost steps).
- `customer_return_extras`: the customer-return tab's fields (damage type, moment of detection, observed symptom).
- `tables`: the two tables, in the order of `NC_COLUMNS` and `DEF_COLUMNS` (the column lists at the top of the file, each with
  its meaning).
- `lines_to_label`: the defect lines that need an AI label.
- `liab_cat`: the three "Responsabilité" groups (`2_regle_responsabilite.csv`).
- `year_rows`, `year_causes`: the comparison year, from the NCs of the same run, summed per month.

### `cost/`: the cost model

**In plain words:** each NC goes through up to six steps: the operator's alert, writing the NC, technical support, preparing
the job, the hands-on work, and the re-check. Each step takes minutes, paid at the hourly rate of whoever does it
(production, quality or ME). Engineering hours (design queries), material, and the price of a rejected, scrapped or
exchanged part are added. The decision (rework, scrap, design query...) says which steps are charged, and whether the part
counts.

`model.py`, function `compute_cnq`, in this order:

1. **Each defect line:** minutes and material from its type of defect (`3_cout_temps_defauts.csv`); for connection errors,
   only the first one of the NC takes the full time, each next one less (`minutes_branchement_suivant`).
2. **Each NC, its minutes per step:** alert (or the declared time of the aléa behind the NC), writing (longer at final
   inspection), support, hands-on work (the sum of its lines, times a factor for internal NCs), preparation (never letting the
   work fall under the minimum), re-check, engineering hours. When the NC has a closed rework order with a planned time, that
   planned time replaces the model's preparation and hands-on minutes, and the logistics minutes (`minutes_logistique`) are
   added to the preparation when a part has to be supplied (the NC names a material).
3. **Euros:** each step's minutes at its rate, plus engineering, material and part value (the price of the part, from the
   sheet *Part prices*, for the decisions that count it).
4. **Customer returns:** a flat extra, or the real amount when it is known.
5. **Two comparison levels:** "global" (average times for every NC) and "Airbus standard" (the official cost per decision).
6. **Back to the lines:** each line gets its share of the NC's cost (its own work and material, plus an equal part of the rest).

The other files:

| File | What it does |
|---|---|
| `params.py` | Turns the cost settings (the sheet *Cost rates and times* and the cost tables) into the model's settings |
| `orders.py` | Reads the rework orders' operations and their planned time; gives each NC's orders a state (used, open, no_time, not_found) |
| `disruptions.py` | Links the aléas to NCs (same work order, from 2 h before to 72 h after) and builds the block of aléas with no NC |
| `parts.py` | The part's value: `part_values` gives each NC the unit price of its material (the sheet *Part prices*, else `1_prix_pieces.csv`, matched on the material number without leading zeros) × its quantity; `to_price` lists the materials that still need a price. Guide: *Part prices* |
| `explain.py` | Writes each NC's cost explanation as a table (only for an optional Slate set-up, not used) |

The model runs twice: once on the AI labels (the dashboard's figures) and once on the defect reader's own labels (kept for
comparison).

### `reference.py`: what the pages need besides the NC tables

| Function | Gives the pages |
|---|---|
| `eqmsn`, `working_day_volume`, `production_msn` | The production plan: MSN built per product and month of the year followed (each aircraft spread over the days the plant works, from the blackout days), and each aircraft's build dates |
| `weekly_volume` | MSN built per line and week of the year: the alarms' denominator |
| `calendar_weights`, `calendar_notes` | The working weight of each day and week of both years; the warning when the year, or its Christmas, has no closure |
| `comparison_year` | The comparison year, from the NCs of the same run, summed per month, line, product, with its defects by cause and its volume. The pages know this block as `y25`, its name since the first year followed (2026, compared with 2025) |
| `deliveries` | The comparison year's volume, month by month: `0_livraisons_<year>.csv` when that table exists (2025: the plan does not reach back to it), else measured from the production plan as the year followed's (the products built, spread over the working days) |
| `cable_requests` | The cable team's requests (`downloads.cables`: the sheet *Cable tracker*, else `0_demandes_cables.csv`) |
| `mft_actions`, `mft_actions_page` | The MFT actions (`1_actions_mft.csv`), each tied to its problem; `_actions` checks the table first (ids, kind of problem, dates) |
| `cnq_explain` | The cost settings, for "Expliquer le calcul" |
| `rca_reference` | The cause tree for the Définitions tab, with real examples |
| `page_settings` | The pages' settings: target, filters at opening, categories, colours, alarm settings |
| `dashboard_block`, `mft_block` | All of the above, packed per page |
| `ref_table` | The packs, cut into rows of text for `fto2_dash_ref` |

### `downloads.py`: the production plan's exports and the cable tracker

Two things reach the run as they come, with no table to fill: the production plan, as the exports of the Tableau Avances /
Retards kept in `src/fto2/files/`, and the cable team's tracker, pasted whole in the sheet *Cable tracker*. `2_sources.csv`
names them: `exports_plan`, `suivi_cables`.

| Function | What it does |
|---|---|
| `files`, `file_day` | The files a line of `2_sources.csv` names, oldest first. An export's day is the date at the end of its name (`Avances_Retards_2026-11-18.csv`) |
| `plan_of_export` | One export of the Tableau Avances / Retards as plan rows: one per aircraft and product, with the planned and the real date of its 8 milestones; an MSN shown as `#N/A` is taken from the older exports |
| `merge_plan`, `plan` | The plan from every export, oldest first: the newest row of each aircraft wins; an aircraft delivered before a new export keeps its last row; a row that left the export before its delivery is dropped. `0_plan_msn.csv` is read as one more export |
| `cables_of_export`, `cables` | The cable tracker as request rows (origin from `2_cables_origines.csv`, proposed cause from `2_regle_cause_cable.csv`); without it, `0_demandes_cables.csv` |
| `report` | Two lines for the run's log: which exports were read |

An export that is not the one expected stops the run with a message that says which file and what was looked for.

## 5. The tables it writes

| Table | One row per | Columns |
|---|---|---|
| `fto2_dash_nc` | NC | Listed with their meaning in `core.py`, `NC_COLUMNS`: number, dates, line, plant, liability, cost decision and levels, cost per step, phase, MSN, product, station, NC type, source, rework orders, aléas... |
| `fto2_dash_defects` | defect line | `core.py`, `DEF_COLUMNS`: NC, line number, category, cause, sub-category, minor, cable, cost share, quantity, text, sub-code, FIN, where the label comes from (`ai`, `titre`, `parser`) |
| `fto2_dash_disruptions` | quality aléa with no NC | `core.py`, `DIS_COLUMNS`: number, date, line, station, work order, minutes, counted or not, reason, status, comment |
| `fto2_dash_ref` | piece of text | `partie` (one per page: dashboard, mft), `morceau` (0, 1, 2... in order), `texte`. The pages glue the pieces of a part back together and read them as one block of data. Cut into pieces because one cell can't hold it all. |

The tables hold both years, the comparison year and the year followed: each page chooses what it shows.

Also written, as datasets beside the tables: the two work lists, `fto2_lines_to_label` (the defect lines to label) and
`fto2_parts_to_price` (the materials still without a price).

## 6. Changing the logic

**First check it isn't a setting.** Most changes (a rule, a rate, a product, a date) are a Fusion sheet or a table of
`src/fto2/settings/`, not code: see *The settings, table by table*.

**Where to change what** (in `src/fto2/`):

| You want to change... | File |
|---|---|
| Which NCs are read from Skywise | `skywise.py`, `select_ncs` |
| A new kind of label on each NC | a rule table, plus a line in `selection.add_columns` |
| How defects are read from the text | `parser/nc_defect_parser.py` (expert) |
| A new column in the dashboard tables | `core.py`: add it to `NC_COLUMNS` / `DEF_COLUMNS` and fill it in `tables`; then add it to the query in Slate and read it in the page (*The pages, in detail*, section 8) |
| How the cost is calculated | `cost/model.py` |
| How a part is found and priced | `cost/parts.py` (the prices themselves: the sheet *Part prices*) |
| What the pages receive besides the tables | `reference.py` |
| A new input (a dataset, a Fusion sheet) | the transform `src/myproject/datasets/fto2_update.py`, under the name the code reads |

**Checking a change in the Code Repository:**

1. Note the figures the update prints at the end of its log (number of NCs, defect lines, cost) and the dashboard's headline
   figures (Essentiel › Synthèse, with the filters as the page opens).
2. Change the code in `src/fto2/`. The repository keeps every earlier version: it is your way back.
3. Commit, wait for the checks, then build `fto2_dash_nc` (press Build with `fto2_update.py` on screen).
4. Compare: only what you meant to change should move. If something else moved, go back to the earlier version and build
   again before looking further.

## 7. When the update stops

| The message | What it means | What to do |
|---|---|---|
| Names a settings table and a line | A setting is badly filled. A `1_` table may be its Fusion sheet, which replaces the table for the run | Fix that line, in the sheet or in `src/fto2/settings/` (*The settings, table by table*, section 1) |
| "settings table … not found" | A table was renamed, moved or deleted | Put it back in `src/fto2/settings/` |
| A dataset name that isn't found | The dataset is not an input of the transform, or was renamed | Add it to the inputs of `fto2_update.py`, or change its name in `2_sources.csv` |
| "the station list is missing" | `fto2_station_mapping.csv` is not in `src/fto2/files/` | Put it back there |
| "⚠️ Fusion sheet … NOT USED" | A pasted sheet could not be read (usually its header row: a column missing or renamed at the source). The run keeps what it had and says why | Empty the sheet, paste the whole source again at A1, and build |
| A list "could not be read" | The GPS register or the Test list is missing or changed shape | Its NCs run without the list's information: paste the list again |
| "1_prix_pieces.csv: '…' is not a price" | A price in the sheet *Part prices* has text in it | Fix that line |
| "fto2_dash_cout not written" | Normal: that table is only for an optional set-up | Nothing |
| Any other error | The last step printed says where it was | The file of that step (section 3) |
