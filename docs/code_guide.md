# Code guide: where to look, by type of question

This guide is for anyone who has a question about how the FTO2 NC tool works inside Skywise. Find your type of question in
the table below, then go to its section. Each section answers the usual questions and names the file to open.

## The whole thing in one picture

The tool has two halves.

```
 Skywise datasets: NCs, work orders, aléas, AI labels        data/config/  (the settings: 43 small tables)
                         \                                    /
                    THE NOTEBOOK  (Code Workspace: fto2_pipeline_notebook)
                    its code: notebook_kit/fto2/
                         |
             four tables: fto2_dash_nc       one row per NC
                          fto2_dash_defects  one row per defect line
                          fto2_dash_disruptions  the quality aléas with no NC
                          fto2_dash_ref      the reference data (production plan, 2025, settings for the pages...)
                         |   (synced to Postgres, schema foundry_sync)
                    THE SLATE APP
                    four queries: q_fto2_nc, q_fto2_def, q_fto2_dis, q_fto2_ref
                    three code sandboxes: the dashboard, the MFT page, the Tableau Elizabeth
                    (they filter, add up and draw)
```

**The notebook does the thinking** (which NCs count, their labels, their cost). **The pages do the showing** (filters,
totals, charts, alarms).

## Find your type of question

| Your question is about... | Example | Go to |
|---|---|---|
| A setting: a rule, a rate, the target, a product | "How do I make this workflow count as REC?" | `data/config/README.md` |
| Where a number comes from | "Why are there 868 NCs and not 900?" | [A. Data](#a-data-where-a-number-comes-from) |
| The notebook's code | "Where is the NC selection done?" | [B. The notebook](#b-the-notebook-backend) |
| The cost | "How is the cost of this NC worked out?" | [C. Cost](#c-the-cost-of-non-quality) |
| Defects, causes, labels | "Why is this defect called an inversion?" | [D. Defects and causes](#d-defects-causes-and-labels) |
| The dashboard's code | "How do I change this chart?" | [E. The pages](#e-the-pages-front-end) |
| The bell (alarms) | "Why did this alarm ring?" | [F. Alarms](#f-the-alarms-the-bell) |
| The MFT page or the Tableau Elizabeth | "Where do the MFT actions come from?" | [G. MFT and Elizabeth](#g-the-mft-page-and-the-tableau-elizabeth) |
| How Slate is wired | "What does the state box do?" | [H. Slate](#h-how-slate-is-wired) |
| Something broke | "The notebook stopped with an error" | [I. When something breaks](#i-when-something-breaks) |

---

## A. Data: where a number comes from

**Why this many NCs?** On the dashboard, click the **ⓘ** under the filter bar ("Comment la sélection est faite"). It lists
every filter in order, how many NCs each one removes, and how many are left.

**Which NCs are behind this bar?** Click the bar: the whole dashboard filters on it. The **Localisation** tab then lists those
NCs with their numbers.

**Which NCs does the notebook take in?** The NCs of the plant created since the start date (`data/config/2_parametres.csv`,
`date_debut`), plus NCs of other plants where FTO2 is liable, plus the NCs of the GPS register and the Test list. Minus the
exclusions (`2_regle_exclusion.csv`). The code: `notebook_kit/fto2/skywise.py` (`select_ncs`) and `fto2/selection.py`.

**What is in each column of the tables?** `notebook_kit/fto2/core.py`, at the top: `NC_COLUMNS` (the NC table) and
`DEF_COLUMNS` (the defect table) give every column with its meaning.

**Where does the reference data come from** (production plan, 2025 figures, cables, MFT actions, page settings)?
`notebook_kit/fto2/reference.py`. It reads the level-1 tables of `data/config/` and the 2025 NCs, and writes it all into
`fto2_dash_ref` as pieces of text (columns `partie`, `morceau`, `texte`). The pages join the pieces back together.

## B. The notebook (backend)

The notebook itself has three short cells: it only calls `skywise.run(...)`. All the work is in `notebook_kit/fto2/`, plain
Python, one file per subject.

**The run, step by step** (`fto2/skywise.py`, function `run`; the notebook prints each step as it goes):

| Step | What it does | Main file |
|---|---|---|
| A | Reads the NCs from Skywise and keeps the ones that count; adds the labels from the rule tables (phase, product, type...) | `skywise.py`, `selection.py`, `rules.py` |
| B | Fetches the NCs of the GPS register and the Test list that the selection missed | `manual_lists.py` |
| C | While the old Slate app is in use, writes its old tables too | `skywise.py` |
| D | Reads each NC's text into defect lines, adds the AI labels, the rework orders, the aléas, the cost, and writes the three dashboard tables | `core.py`, `parser/`, `cost/` |
| E | Builds the reference data and writes `fto2_dash_ref` | `reference.py` |

**Every file of `notebook_kit/fto2/`:**

| File | What it does |
|---|---|
| `skywise.py` | The run above: reads the datasets, calls the other files, writes the tables. Start here. |
| `config.py` | Reads the tables of `data/config/`. When one is badly filled, it stops with a clear message (file, line, what to fix). |
| `rules.py` | The rule engine: applies a rule table (`2_regle_*.csv`) to the NCs. How the tables are read is explained at its top. |
| `selection.py` | Which NCs count, and the labels each NC gets from the rule tables. |
| `manual_lists.py` | Reads the GPS register and the Test list (files in `data/`). |
| `core.py` | From the NCs to the dashboard's tables: defect lines, labels, scope, cost, then the two tables. |
| `parser/` | The defect reader: turns an NC's long text into defect lines (see section D). |
| `cost/` | The cost model (see section C). |
| `reference.py` | The reference data for the pages (production plan, 2025, cables, MFT actions, settings). |
| `everyday_tables.py` | Writes a level-1 table from a raw file while keeping the rows corrected by hand (`source` = `manuel`). |

**How a rule table becomes code:** it doesn't. `rules.py` reads the table each run and applies it, so changing a rule never
needs a code change.

## C. The cost of non-quality

**How is an NC's cost made, in plain words?** Each NC goes through up to six steps: the operator's alert, writing the NC,
technical support, preparing the job, the hands-on work, and the re-check. Each step takes some minutes, paid at the hourly
rate of whoever does it (production, quality or ME). Engineering hours (design queries) and material are added. The work
minutes depend on the type of each defect line, or on the planned time of the NC's rework order when there is one.

**See it for one NC:** dashboard, cost tab, **Expliquer le calcul**: type the NC number, every step is shown.

**The code:** `notebook_kit/fto2/cost/`

| File | What it does |
|---|---|
| `model.py` | The calculation itself, NC by NC and defect line by defect line. |
| `params.py` | Reads the cost settings (`2_cout_*.csv`, `3_cout_*.csv` in `data/config/`). |
| `orders.py` | The planned time of each NC's rework orders, from the work-order operations. |
| `disruptions.py` | The aléas: the declared time of the aléa behind an NC, and the aléas that led to no NC (shown beside the cost). |
| `explain.py` | The cost explanation of each NC as a table (only used by an optional set-up; the page works it out itself). |

**The numbers** (rates, minutes, which decision charges what) are all in `data/config/`: see its README, section "The cost of
non-quality".

## D. Defects, causes and labels

**How does an NC become defect lines?** The defect reader (`notebook_kit/fto2/parser/nc_defect_parser.py`) reads the NC's
long text and splits it into lines, each with a sub-category, a cause and a category. `parser/fto2_logic.py` wraps it for the
rest of the code (and gives each NC its line, A350, A330...). A400M NCs have no long text: their line is read from the title
(`3_a400m_titres.csv`, used in `core.py`).

**Why is this defect labelled with this cause?** Each defect line has an **AI label** (dataset `fto2_ai_labels`), made from
the full text. A line added since the last AI pass gets the defect reader's label until the next pass. The defect table's
column `label_src` says which: `ai`, `titre` (A400M title) or `parser`.

**Where are new lines to label?** Each run writes `fto2_lines_to_label.csv` next to the notebook: the lines with no AI label
yet, with their full text. Once labelled (same columns as `fto2_ai_labels`), they are added to that dataset. **NC texts must not
go to an outside AI tool without IT's approval.**

**What do the categories and causes mean?** The dashboard's **Définitions** tab. Their names, order and colours are in
`data/config/` (`2_categories.csv`, `2_causes_noms.csv`, `2_causes_definitions.csv`, `3_sous_categories.csv`).

## E. The pages (front end)

Each page is one Slate **code sandbox** with three parts: CSS (the look), HTML (the layout), JS (the code). The JS is plain
JavaScript, no outside library.

**How the dashboard's JS is laid out**, from top to bottom (search for these markers):

| Marker | What is there |
|---|---|
| `ADAPTER START` / `ADAPTER END` | `fto2FromTables`: turns the query results into the page's data `D` |
| `function main()` | the page itself, everything below until the end of the loader |
| `var STR = {` | every text of the page, in French (`fr`) and English (`en`) |
| `MODEL START` / `MODEL END` | the calculations, with no drawing: selection (filters), production per MSN, targets and forecast, cost explanation, alarm list |
| `the calculations: here, or in Slate` | small functions the charts call to get the targets, the alarms and the cost explanation |
| `// ---- 1. Overview`, `2. Pareto`, `4. Cost`... | one section per tab, the charts of that tab |
| `ALARM ENGINE START` / `END` | the alarm statistics (section F) |
| `filter bar`, `language, tabs` | the filter bar, the tabs, the language switch |
| `Simple mode` | the Essentiel mode (Synthèse and Détail) |
| the end of the file | the loader: waits for the four queries, then starts the page; shows a box if something is missing |

Sections marked "local page only", the Gallery, the Review and the Mock-up pages are not shown in Skywise: leave them.

**What happens when someone clicks a filter?** The filters live in `GF`. A change calls `select()`, which makes the list of NCs
on screen (`SEL_NC`), then `renderAll()` redraws every tab. Each chart counts from `SEL_NC`, so every chart follows the filters.
A click on a chart works through `data-pick="kind|value"` on the drawn element: it sets `GF.pick` and every tab follows.

**The data inside the page:** `D.ncs` is a list of NCs, each a list of values by position. The most used:

| | | | |
|---|---|---|---|
| `[0]` NC number | `[1]` creation date | `[3]` line | `[5]` 1 if FTO2 is liable |
| `[6]` cost decision | `[8]` where found | `[12]` cost | `[23]` serie / client / autre |
| `[24]` phase | `[25]` MSN | `[26]` product | `[27]` station |
| `[33]` NC type | `[39]` data source | `[40]` cost steps | `[42]` plant |

`D.defects` is a list of defect lines: `[0]` NC number, `[1]` line number, `[11]` category, `[12]` cause, `[13]` sub-category,
`[14]` minor, `[17]` share of the cost, `[18]` text, `[22]` sub-code, `[23]` FIN. The full list is in `fto2FromTables`.

**How do I find the code of a chart?** Take a word of its title on the page, search it in `STR` to find its key (e.g.
`v2TgtR`), then search that key: it leads to the function that draws the chart.

**How do I change a text?** In `STR`, change it in `fr` and in `en`.

**How do I change a chart?** Its function counts from `SEL_NC` and draws SVG with small helpers: `svg()` (the frame), `tx()`
(a text), `tip()` (a tooltip), `pk()` (a click that filters), `gSet()` (puts the chart in its box).

**Editing in practice.** The dashboard's JS is long. Copy it out of the sandbox into a text editor, change it, paste it back.
**Keep a copy of the previous JS first**, to go back if the page breaks.

**Three rules for the code in Slate:**

- **No two `{` in a row** anywhere in the JS. Slate reads them as a link to a query and breaks the code.
- **The styles are prefixed with `.fto2`**, so they don't leak into the rest of the Slate page. Keep that prefix on new rules.
- **No data in the code.** The data and the reference data come from the queries; the code only computes and draws.

## F. The alarms (the bell)

**Why did this alarm ring?** The bell compares, line by line, the defects of the last 4 finished weeks with the 12 weeks
before, per MSN built. It rings when the rise is too big to be chance (a minor or a major alarm). Click the alarm: the
dashboard opens on the problem.

**The settings** (weeks compared, thresholds, how many alarms shown): `data/config/3_alarmes.csv`.

**The code:**
- the statistics: between `ALARM ENGINE START` and `ALARM ENGINE END` in the dashboard's JS;
- what is followed (categories, causes, sub-codes, stations, products, cable requests): `alCompute`, in `MODEL START … END`,
  section "6. alarms";
- the bell's list on screen: `alRender`.

**The MFT page has its own copy of the alarm engine** in its JS. If you change one, change the other the same way, or the two
pages will ring differently.

## G. The MFT page and the Tableau Elizabeth

**The MFT page** (one sandbox) shows one line at a time: the week's Pareto, the analysis, and the action follow-up. Its JS is
laid out in sections: `data`, `weeks`, `controls`, `tab 1: the week's Pareto`, `tab 2: analysis`, `tab 3: actions`, `the
action form`, `the bell`, `events`.

**Where do the MFT actions come from?** From `data/config/1_actions_mft.csv`: every row is an action, shown to everyone after
the next notebook run. An action typed directly on the page stays in that browser only, until it is added to the table.

**The Tableau Elizabeth** (one sandbox, optional): the NC count of a line, three families of problems, a Pareto and the weeks
over a threshold. Same layout: CSS, HTML, JS, state.

## H. How Slate is wired

**The queries** read the four tables in Postgres (`foundry_sync` schema). Their SQL only lists the columns.

**The state box** of each sandbox links the queries to the page:

```
{"nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}", "dis": "{{q_fto2_dis}}", "ref": "{{q_fto2_ref}}"}
```

The page waits until each key holds its query's result, then starts. The MFT page and the Tableau Elizabeth use `nc`, `def`
and `ref`.

**The sync:** the notebook writes the tables as datasets; the sync copies them to Postgres. The pages only see new data once
the sync has run.

## I. When something breaks

| What you see | What it means | Where to look |
|---|---|---|
| The notebook stops with a message naming a file of `data/config/` and a line | A settings table is badly filled (a `;` in a text, a wrong test name, a missing column) | Fix that line; `data/config/README.md` section 1 lists the rules |
| The notebook stops with another error | The last step it printed says where it was | The file of that step (section B) |
| The page says it is still waiting for a query | The query doesn't exist under that name, or fails | The query's name and its SQL in Slate |
| "La requête … n'a renvoyé aucune ligne" | The query works but the table is empty | The sync, then the notebook's run |
| "aucune NC lisible … colonnes reçues" | The query returns columns the page doesn't expect | Compare the columns it lists with the table's |
| "exactement N lignes reçues" | Slate probably cut the result | A row limit on the query |
| A figure looks wrong | Check the selection first | The ⓘ panel, then **Expliquer le calcul** for a cost |
| The page broke after a code change | The new JS has a mistake | Paste the previous JS back, then retry the change |
