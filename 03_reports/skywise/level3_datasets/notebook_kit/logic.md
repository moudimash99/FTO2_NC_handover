# Logic: how the notebook's code works

The logic is everything the notebook does: it reads the NCs from Skywise, decides which ones count, reads their defects,
labels them, works out their cost, and writes the tables the pages read. This guide explains that code.

The three guides: `config.md` (the settings tables; in the Code Workspace also as `data/config/README.md`), `logic.md` (the
notebook's code) and `front_end.md` (the pages' code); these two are also in `notebook_kit/`.

**Contents**

1. [The big picture](#1-the-big-picture)
2. [Where the code is](#2-where-the-code-is)
3. [The run, step by step](#3-the-run-step-by-step)
4. [Each file explained](#4-each-file-explained)
5. [The tables it writes](#5-the-tables-it-writes)
6. [Changing the logic](#6-changing-the-logic)
7. [When the notebook stops](#7-when-the-notebook-stops)

---

## 1. The big picture

```
 Skywise datasets                          data/config/ (the settings)
   non_conformity        (the NCs)                 |
   fto2_ai_labels        (the AI labels)           |
   work_order_operation  (rework orders)           |
   mes_disruptions       (aléas)                   |
            \                                      /
             THE NOTEBOOK  ->  notebook_kit/fto2/  (the code)
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

In the Code Workspace:

| What | Where |
|---|---|
| The notebook | `fto2_pipeline_notebook`: three short cells. It only calls `skywise.run(...)`. |
| The code | `notebook_kit/fto2/`: plain Python, one file per subject. |
| The settings | `data/config/` (see `config.md`). |
| Files read besides the datasets | `data/`: the station list, the GPS register, the Test list (names in `data/config/2_sources.csv`). |

The files of `notebook_kit/fto2/`:

| File | In one sentence |
|---|---|
| `skywise.py` | The run: reads the datasets, calls everything else in order, writes the tables. **Start reading here.** |
| `config.py` | Reads the settings tables and stops with a clear message when one is badly filled. |
| `rules.py` | The rule engine: applies a rule table (`2_regle_*.csv`) to the NCs. |
| `selection.py` | Which NCs count, and the labels each NC gets from the rule tables. |
| `manual_lists.py` | Reads the GPS register and the Test list. |
| `parser/` | The defect reader: turns an NC's long text into defect lines. |
| `core.py` | From the NCs to the dashboard's tables: defects, labels, rework orders, aléas, cost, scope. |
| `cost/` | The cost model, with the rework orders, the aléas and the part prices. |
| `reference.py` | Everything the pages need besides the NC tables (production plan, comparison year, cables, actions, settings). |
| `everyday_tables.py` | Writes a level-1 table from a raw file while keeping the rows a person corrected. |

## 3. The run, step by step

`skywise.py`, function `run`. The notebook prints each step while it runs, so the last line printed says where it is.

**A. The standard selection** (`select_ncs`, then `selection.apply_rules`)

1. Reads the NCs of the plant created in the year followed (`2_parametres.csv`: `usine`, `annee`), plus the NCs of
   other plants where the plant is liable. Skywise is asked for the NCs created from 1 January (`config.first_day`); the
   NCs created after 31 December are cut in Python (`skywise._until`), because Skywise's filter fails on three conditions
   joined with `&`.
2. Leaves out the excluded ones (`2_regle_exclusion.csv`: ERMA, NCs deleted at another plant).
3. Adds the labels from the rule tables, in this order: phase (`2_regle_phase.csv`), decision label (`2_decisions.csv`),
   origin (`2_regle_origine.csv`), type (`2_regle_type_nc.csv`, which uses the origin), product (`2_regle_produit.csv`).

**B. The manual lists** (`manual_lists.py`): the NCs of the GPS register and the Test list that step A missed are fetched by
number, then go through the same rules.

**C. The old outputs**: while `garder_anciennes_sorties` is `oui`, the old Slate app's four tables are written as before.

**D. The dashboard tables** (`core.build`, which calls `core.prepare` then `core.tables`):

1. **Defects:** the defect reader splits each NC's long text into defect lines (`parser/`). A400M NCs have no long text: one
   line is made from the title (`core.title_lines`, `3_a400m_titres.csv`).
2. **Rework orders:** the NC's rework orders, their state and planned time (`cost/orders.py`).
3. **Aléas:** the quality aléa that led to each NC and its declared time, and the aléas that led to no NC
   (`cost/disruptions.py`).
4. **Labels:** each defect line takes its AI label from `fto2_ai_labels`, **only if the line's text is still the same as when
   it was labelled**. Otherwise it keeps the defect reader's label and is listed "to label". Then the category, cause,
   "minor" flag and official sub-code follow from the label.
5. **Part prices:** the NC data names the part each NC is about (column `material`); its price comes from
   `1_prix_pieces.csv` (`cost/parts.py`). The materials still without a price are written to `fto2_parts_to_price.csv`.
6. **Cost:** the cost model runs on every NC (`cost/model.py`, section 4).
7. **Scope:** where each NC was raised: `serie`, `client` (customer return), `autre` (`2_regle_perimetre.csv`).
8. **Tables:** `core.tables` puts it all into the two tables, column by column, and `core.dis_table` makes the aléa table.
9. **Lines to label:** `core.lines_to_label` writes `fto2_lines_to_label.csv` next to the notebook: the lines without a
   usable AI label, with their full text, ready for the next labelling pass.

**E. The reference data** (`reference.py`): the production plan, the comparison year (the year before the one followed,
unless `annee_comparaison` names another: its NCs are read from Skywise, from 1 January and cut at the year's end as in
step A; they go through the same rules, defect reader, part prices and cost model, then are summed per month), the cable
requests, the MFT actions, the cost settings, the cause tree and the page settings. They are packed into `fto2_dash_ref`
(section 5).

**The year.** Every date of the run comes from one line, `annee` in `2_parametres.csv`, through four functions of
`config.py`: `year()`, `comparison_year()`, `first_day()` (1 January), `year_end()` (1 January of the next year) and
`aleas_since()` (1 December of the year before: an NC of early January can follow an aléa of late December). No year is
written in the code: `tests/test_config.py` fails if one is. When the year followed is over, the last lines of the run say
so and name the line to change.

## 4. Each file explained

### `config.py`: reading the settings

- `table(name, columns)`: a settings table as text, after checking that it exists, that every line has the right number of
  columns, and that the expected columns are there.
- `parameter(name, table)`: one value of a name-and-value table (`2_parametres.csv` by default). `parameter_list` splits it on
  `|`; `parameter_yes` reads `oui` / `non`.
- `rule_table(name, columns)`: a rule table, checked by `rules.check`.
- `mapping(name, key, value)`: a two-column table as a lookup, with its `(autre)` row as the default.
- `folder()`: where the settings are (`data/config/` in the Code Workspace).

### `rules.py`: the rule engine

One function applies every rule table, so they all behave the same way (the way is explained in `config.md`, section 4.3).

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

Reads both files (`2_sources.csv` says where they are, how many lines to skip and which columns hold the NC number and the
date; `{annee}` in a file name stands for the year followed), keeps the NCs dated in the year followed, and marks each NC with the list it is on (`Ext_Source`: `GPS`,
`Test`, or none).

### `parser/`: the defect reader

- `nc_defect_parser.py`: reads an NC's long text. It finds the defects written in it (numbered lists, the writing standard's
  template, a line joining two defects with "+"), then gives each defect a **sub-category** from the official codes written in
  the text, or from keywords. Expert rules, with priorities (cable first, then connection, then unlocked contact).
- `fto2_logic.py`: wraps the reader for the rest of the code: `build_defects` (one row per defect), `build_nc` (one row per
  NC with its defect counts), `line_of` (the aircraft line of a programme, `2_regle_ligne.csv`), and the cause names
  (`2_causes_noms.csv`).

### `core.py`: from the NCs to the dashboard tables

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
- `year_baseline`, `year_causes`: the comparison year through the same rules, summed per month.

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
3. **Euros:** each step's minutes at its rate, plus engineering, material and part value (the price of the part, from
   `1_prix_pieces.csv`, for the decisions that count it).
4. **Customer returns:** a flat extra, or the real amount when it is known.
5. **Two comparison levels:** "global" (average times for every NC) and "Airbus standard" (the official cost per decision).
6. **Back to the lines:** each line gets its share of the NC's cost (its own work and material, plus an equal part of the rest).

The other files:

| File | What it does |
|---|---|
| `params.py` | Turns the cost tables of `data/config/` into the model's settings |
| `orders.py` | Reads the rework orders' operations and their planned time; gives each NC's orders a state (used, open, no_time, not_found) |
| `disruptions.py` | Links the aléas to NCs (same work order, from 2 h before to 72 h after) and builds the block of aléas with no NC |
| `parts.py` | The part's value: `part_values` gives each NC the unit price of its material (`1_prix_pieces.csv`, matched on the material number without leading zeros) × its quantity; `to_price` lists the materials that still need a price. Guide: `part_prices.md` |
| `explain.py` | Writes each NC's cost explanation as a table (only for an optional Slate set-up, not used) |

The model runs twice: once on the AI labels (the dashboard's figures) and once on the defect reader's own labels (kept for
comparison).

### `reference.py`: what the pages need besides the NC tables

| Function | Gives the pages |
|---|---|
| `eqmsn`, `working_day_volume`, `production_msn` | The production plan: MSN built per product and month of the year followed (counted on working days, `1_calendrier_production.csv`), and each aircraft's build dates |
| `weekly_volume` | MSN built per line and week of the year: the alarms' denominator |
| `comparison_year` | The comparison year, summed per month, line, product. The pages know this block as `y25`, its name since the first year followed (2026, compared with 2025) |
| `deliveries` | The products delivered in the comparison year, month by month: `1_livraisons_<year>.csv` when it exists, else counted in the production plan (a product is delivered in the month of its Départ OTA) |
| `cable_requests` | The cable team's requests (`1_demandes_cables.csv`) |
| `mft_actions`, `mft_actions_page` | The MFT actions (`1_actions_mft.csv`), each tied to its problem |
| `cnq_explain` | The cost settings, for "Expliquer le calcul" |
| `rca_reference` | The cause tree for the Définitions tab, with real examples |
| `page_settings` | The pages' settings: target, filters at opening, categories, colours, alarm settings |
| `dashboard_block`, `mft_block` | All of the above, packed per page |
| `ref_table` | The packs, cut into rows of text for `fto2_dash_ref` |

### `everyday_tables.py`: tables filled from a raw file

`write(name, rows, key)` writes a level-1 table from new rows marked `auto`, and keeps every row marked `manuel` (a person's
row wins over a new row with the same key). `read(name)` reads one back.

## 5. The tables it writes

| Table | One row per | Columns |
|---|---|---|
| `fto2_dash_nc` | NC | Listed with their meaning in `core.py`, `NC_COLUMNS`: number, dates, line, plant, liability, cost decision and levels, cost per step, phase, MSN, product, station, NC type, source, rework orders, aléas... |
| `fto2_dash_defects` | defect line | `core.py`, `DEF_COLUMNS`: NC, line number, category, cause, sub-category, minor, cable, cost share, quantity, text, sub-code, FIN, where the label comes from (`ai`, `titre`, `parser`) |
| `fto2_dash_disruptions` | quality aléa with no NC | `core.py`, `DIS_COLUMNS`: number, date, line, station, work order, minutes, counted or not, reason, status, comment |
| `fto2_dash_ref` | piece of text | `partie` (dashboard, mft, elizabeth), `morceau` (0, 1, 2... in order), `texte`. The pages glue the pieces of a part back together and read them as one block of data. Cut into pieces because one cell can't hold it all. |

Also written: `fto2_lines_to_label.csv` (next to the notebook), and, while `garder_anciennes_sorties` is `oui`, the old app's
four tables.

## 6. Changing the logic

**First check it isn't a setting.** Most changes (a rule, a rate, a product, a date) are a table in `data/config/`, not code:
see `config.md`.

**Where to change what:**

| You want to change... | File |
|---|---|
| Which NCs are read from Skywise | `skywise.py`, `select_ncs` |
| A new kind of label on each NC | a rule table, plus a line in `selection.add_columns` |
| How defects are read from the text | `parser/nc_defect_parser.py` (expert) |
| A new column in the dashboard tables | `core.py`: add it to `NC_COLUMNS` / `DEF_COLUMNS` and fill it in `tables`; then add it to the query in Slate and read it in the page (`front_end.md`) |
| How the cost is calculated | `cost/model.py` |
| How a part is found and priced | `cost/parts.py` (the prices themselves: `1_prix_pieces.csv`) |
| What the pages receive besides the tables | `reference.py` |

**Testing a change in the Code Workspace:**

1. Note the figures the notebook prints at the end (number of NCs, defect lines, cost) and the dashboard's headline figures.
2. Change the code in `notebook_kit/fto2/` and keep a copy of the file as it was.
3. Restart the notebook's kernel (Python keeps the old code in memory until then) and run all cells.
4. Compare: only what you meant to change should move.

## 7. When the notebook stops

| The message | What it means | What to do |
|---|---|---|
| Names a file of `data/config/` and a line | A settings table is badly filled | Fix that line (`config.md`, section 1) |
| "settings table … not found" | A table was renamed, moved or deleted | Put it back in `data/config/` |
| A dataset name that isn't found | The dataset isn't in the notebook's Data panel, or was renamed | Add it, or change its name in `2_sources.csv` |
| "1_prix_pieces.csv: '…' is not a price" | A price in the parts price list has text in it | Fix that line |
| "fto2_dash_cout not written" | Normal: that table is only for an optional set-up | Nothing |
| Any other error | The last step printed says where it was | The file of that step (section 3) |
