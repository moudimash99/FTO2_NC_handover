# Front end: how the pages' code works

The front end is three pages, each a Slate application of its own: the **dashboard**, the **MFT page** and the **NC
writer**. The dashboard and the MFT page read the tables the update writes, then filter, add up and draw. The NC writer helps
write an NC to the standard and saves it. This guide explains their code.

The three guides of the code: *The settings, table by table* (the settings), *The update, step by step* (the update's code)
and *The pages, in detail* (this one). The part prices have a guide of their own: *Part prices*.

**Contents**

1. [The big picture](#1-the-big-picture)
2. [How the data reaches a page](#2-how-the-data-reaches-a-page)
3. [The dashboard's code](#3-the-dashboards-code)
4. [Finding and changing a chart](#4-finding-and-changing-a-chart)
5. [The alarms (the bell)](#5-the-alarms-the-bell)
6. [The MFT page's code](#6-the-mft-pages-code)
7. [The NC writer's code](#7-the-nc-writers-code)
8. [Editing a page in Slate](#8-editing-a-page-in-slate)
9. [When a page shows a box](#9-when-a-page-shows-a-box)

---

## 1. The big picture

```
 Postgres (synced from the update's tables)
        |
 Slate queries: q_fto2_nc, q_fto2_def, q_fto2_dis, q_fto2_ref
        |
 the sandbox's state box: links each query to a name the page knows
        |
 the page's code (JS): waits for the data, turns it into lists, then
     filters  ->  adds up  ->  draws (SVG charts, tables)
```

Each page is a Slate application with one **code sandbox**, in four parts:

| Part | What it holds |
|---|---|
| CSS | the look: colours, sizes, spacing |
| HTML | the frame: header, filter bar, tabs, one empty box per chart |
| JS | the code: plain JavaScript, no outside library |
| State | the links to the queries, e.g. `{"nc": "{{q_fto2_nc}}", ...}` |

Changing a page means changing its JS (or its CSS, its HTML) in the sandbox of its Slate application (section 8). The
functions and variables named in this guide are those of the page's JS: search for them there.

**The rule of the split:** the update decides and calculates (which NC counts, what each defect is, what it costs; see *The
update, step by step*). The pages only filter, add up and draw. A number wrong everywhere is an update question; a number
wrong on one chart only is a page question.

## 2. How the data reaches a page

1. **The queries** read the four tables in Postgres (`foundry_sync` schema). Their SQL only lists the columns.
2. **The state box** gives each query result a name: `nc` (one row per NC), `def` (one row per defect line), `dis` (the aléas
   with no NC, dashboard only), `ref` (the reference data).
3. **The loader**, at the very end of the JS, watches those four names. When all have arrived, it starts the page. If one is
   missing for too long, it shows a box saying which one (section 9).
4. **The reference data** comes in pieces of text (`partie`, `morceau`, `texte`). `fto2RefBlocks`, at the top of the JS, glues
   each part's pieces back together and reads them as one block: the production plan, the comparison year, the cable
   requests, the MFT actions, the cost settings, the cause tree, and the page settings (target, filters at opening, colours,
   alarm settings, the working weight of each week).
5. **The adapter** `fto2FromTables` (between `ADAPTER START` and `ADAPTER END`) turns the two tables into the page's data `D`.
   The tables hold two years, the comparison year and the year followed: the dashboard keeps the year followed (the adapter
   drops the rest), the MFT page keeps both.
6. **Two optional keys.** `reglages`, the query `q_fto2_set_targets` (the Fusion sheet "Target and pages"), on the dashboard
   and the MFT page: `fto2Reglages`, near the top of the JS, writes its lines into the page settings before the page starts
   (the target's cut, the filters at opening, the target of an MFT action), so a change in the sheet shows at the next
   opening, without waiting for the update. A line missing or wrongly written keeps the update's value; the browser's
   console says which. `store`, on the MFT page only: section 6. Without these keys in the state box, the pages work as
   before.

**The data inside the page.** `D.ncs` is a list of NCs, each one a list of values by position:

| | | | |
|---|---|---|---|
| `[0]` NC number | `[1]` creation date | `[2]` week | `[3]` line |
| `[5]` 1 if FTO2 is liable | `[6]` cost decision | `[8]` where found | `[12]` cost |
| `[21]` defect lines | `[22]` title | `[23]` serie / client / autre | `[24]` phase |
| `[25]` MSN | `[26]` product | `[27]` station | `[29]` days to close |
| `[30]` open | `[33]` NC type | `[39]` data source | `[40]` cost steps (minutes...) |
| `[41]` origin | `[42]` plant | | |

`D.defects` is a list of defect lines: `[0]` NC number, `[1]` line number, `[11]` category, `[12]` cause, `[13]` sub-category,
`[14]` minor, `[15]` cable, `[17]` share of the cost, `[18]` text, `[22]` sub-code, `[23]` FIN.

The full list, position by position, is in `fto2FromTables`, next to the column of the table each value comes from.

## 3. The dashboard's code

### The layout of its JS

Search for these markers to find your way, from top to bottom:

| Marker | What is there |
|---|---|
| `fto2RefBlocks` | glues the reference data back together |
| `ADAPTER START` … `ADAPTER END` | `fto2FromTables`: the tables become `D` |
| `function main()` | the page itself starts here |
| `var STR = {` | every text of the page, in French (`fr`) and English (`en`) |
| `MODEL START` … `MODEL END` | the calculations, with no drawing (see below) |
| `the calculations: here, or in Slate` | small functions the charts call for the targets, the alarms and the cost explanation; the page computes them itself |
| `// ---- 1. Overview`, `2. Pareto`, `4. Cost`... | one section per tab, with that tab's charts |
| `5. Insights`, `6. Chart texts`, `7. NC rates` | the charts several tabs share: the `a:` charts, the chart texts and drawing helpers, the numbered charts |
| `Drawing a chart by its key` | `rvDraw`: draws an `a:` chart or a numbered chart from its key |
| `ALARM ENGINE START` … `END` | the alarm statistics (section 5) |
| `Dashboard v2 (main page)` | which charts appear on which tab, and their drawing functions (section 4) |
| `filter bar` | the filters and what happens when they change; the CSV download (`csvOf`) |
| `language, tabs, minor switch` | the language switch, the tabs, `renderAll` |
| `Simple mode` | the Essentiel mode (Synthèse and Détail) |
| the end of the file | the loader (section 2) and the error box |

### The calculations (`MODEL START` … `MODEL END`)

The part of the page that computes without drawing, in eight numbered sections:

1. **helpers**: read a defect line or an NC, group the NC types, the categories (`CAT_ORDER`, from the settings);
2. **selection**: the filters (`GF`) and `select()`, which makes the lists of NCs on screen;
3. **production**: the production plan matched to the selected NCs: MSN built per product and month (`pData`, `pAgg`);
4. **targets and forecast**: the comparison year under the same filters (`y25Sel`), the target line by line (`v2Tgt`), the
   forecast to December (`v2Series`, `v2Fc`);
5. **cost explanation**: the minutes and euros of each step of an NC, for "Expliquer le calcul";
6. **alarms**: what the bell follows (`alCompute`);
7. and 8. the same results packed as plain data (used only by an optional Slate set-up).

### The year

The page holds no year of its own. The two years come with the settings (`SET.annee`, the year followed, and
`SET.annee_ref`, the year it is compared with), and are kept at the top of `main()` as two texts, `YEAR` and `PREV`.

- **In the code**, a chart that names a year uses `YEAR` or `PREV`.
- **In the texts** (`STR`, `GX`, `GSTR`), the years are written `{YEAR}` and `{PREV}`, and the target's percentage `{CUT}`
  (from `objectif_baisse`). `withYears(...)`, wrapped around each table of texts, writes the real values in once. A new
  text that names a year: write `{YEAR}` or `{PREV}`, inside a table that `withYears` wraps.
- **The names** `y25`, `r25`, `v26`... date from the first year followed (2026, compared with 2025): read "25" as the
  comparison year and "26" as the year followed. `D.y25` is the comparison year's block, whatever the year.
- **The alarm engine** reads the year from `window.FTO2_YEAR`, set by the page just before it: its week 0 is ISO week 1 of
  the year followed, and a date outside that year has no week (-1).
- **The forecast's name** ("Prévision (oct. à déc.)") is made by `fcLeg` from the months the forecast really covers.
- **The calendar:** a week under `semaine_faible_moins_de` of a normal week is a closure week, left out of the averages
  (`calW`); the month in progress counts the share of its working time gone (`dayShare`), not of its calendar days.

So a new year needs no change in the pages: the update sends the new year, and everything above follows.

### What happens when someone clicks

1. **A filter changes** (the filter bar, or a click on a chart). The filters are kept in `GF`: dates (`from`, `to`), period
   (`preset`: since 1 January, the last 30 days, the last full month, the last 3, 6 or 12 months, all dates, or dates
   chosen), line, phase, Responsabilité boxes (`liab`), plant switch (`fto2`), data source (`src`: one list, "Source des
   données": all the data, Skywise only, GPS register, Test list), cost mode, and a clicked value (`pick`).
2. `setGF` stores the change and calls `select()`, which makes the lists of NCs on screen:
   - `SEL_NC`: every NC the filters keep;
   - `SER_NC`: FTO2's own NCs, without customer returns;
   - `CLI_NC`: the customer returns.
3. `renderAll()` redraws every tab. Each chart counts from those lists, so every chart follows the filters.

**A click on a chart** works through `data-pick="kind|value"` on the drawn element (`pk()` writes it). The page catches the
click (`pickSet`), sets `GF.pick`, and every tab follows. A chip in the filter bar shows it; ✕ removes it.

**A tooltip** works through `data-tip="title|line|line"` on the drawn element (`tip()` writes it).

**A tab change** (`setTab`) shows the tab and draws what that tab needs.

**The ⓘ panel** ("Comment la sélection est faite", section `the ⓘ panel`) replays the same filters one by one and says what
each removes.

### Downloads: CSV and images

- **CSV:** at the bottom of every tab, the NCs of the selection download as a CSV file, as a short extract or a full one
  (`csvOf`: its two column lists, the most useful first).
- **Image:** every chart card has an **⤓ Image** button that saves the chart as a PNG picture (`pngBtn`, `pngOf`); a card
  with no chart drawn (a table) hides it.

### Texts and languages

Every text is in `STR`: `STR.fr` and `STR.en`, by key. The code uses `S('key')`, with values filled in where `{n}`, `{v}`...
appear. The HTML uses `data-t="key"`, filled in by `applyText()`. The chart titles are in `GSTR` (section 4). To change a
text, change it in both languages.

### Essentiel and Deep dive

`MODE` is `simple` (Essentiel) or `expert` (Deep dive). Essentiel shows two tabs (Synthèse, Détail) made of charts taken
from the Deep dive tabs (`V2L.syn`, `V2L.det`). Détail's charts run from January to the end of the period (`ytd`).

## 4. Finding and changing a chart

### Where each chart is placed

In the section `Dashboard v2 (main page)`, **`V2L`** lists the chart cards of each tab, by key:

```
ov:     top: ['VT', 'VN', 'VB', 'a:lead', 'VX'], fold: ['a:cal']
pareto: top: ['a:bump', '78', 'a:flow', 'a:bub', '53', '76', 'VM', 'VQ', 'a:cmo'] ...
where:  top: ['VP', '61', 'a:prod', '54', 'a:msn', 'VF', 'a:station'] ...
```

`top` is shown, `fold` is in the "more" fold. Move a key to move a chart; remove it to hide the chart.

### Which code draws a chart

There are three kinds of keys:

| Key | Drawn by | Title from |
|---|---|---|
| `VT`, `VN`, `VB`... | the function named in `V2F` (e.g. `VT: v2Target`, `VN: v2Trend`) | `GSTR.VT.fr` / `.en`: [short name, title, subtitle, data used] |
| a number (`53`, `78`...) | the function given for that number in `PSPEC` | `GSTR['53']` |
| `a:name` (`a:lead`, `a:bump`...) | `RV_ANA.name` | `STR`: `k_name`, `t_name`, `s_name` |

The cards of the numbered charts and of the `a:` charts are first made in two boxes of the HTML that are never shown
(`#pg2` and `#ag`); `v2Build` then places each one in its tab.

**To find a chart's code from the page:** take a few words of its title, search them in the JS: they lead to its `GSTR` or
`STR` entry, whose key leads to its function.

### Three charts of the Pareto tab

- **"Classement mensuel des causes"** (`a:bump`): the rank of each of the top 8 causes, month by month. A click on a line
  follows that cause.
- **The followed cause per MSN, month by month** (`78`, for example "Inversion par MSN"), beside the ranking: the cause
  clicked in the ranking, else the first cause of the last month. Its two limits, 2σ and 3σ, are straight lines: the
  period's rate plus two and three times the usual spread of its monthly values (the month in progress left out; no limits
  with fewer than three months). `pTrend` draws it.
- **"Les causes mois par mois"** (`a:cmo`, function `vCmo`): one bar per month, the causes stacked. A switch shows the causes
  or the categories of the Pareto; the card's − / + sets how many of the first ones are shown (3 at first), and others can be
  added by hand: Déverrouillage and FOD are added from the start, for safety (`CMO`). The measure is the tab's (defects or
  cost), or NCs with the card's other switch.

### The drawing helpers

A chart function counts from `SEL_NC` (or `D.defects` filtered the same way), then draws SVG with:

| Helper | Does |
|---|---|
| `svg(w, h, inner, label)` | the frame of a chart |
| `tx(x, y, text, class, anchor)` | a text |
| `tip(title, lines)` | a tooltip on an element |
| `pk(kind, value)` | a click that filters the dashboard |
| `gSet(key, html, legend)` | puts the chart and its legend in its card |
| `pEmpty(key)` | "no data" in a card |
| `num`, `eur`, `pct`, `f1`, `f2` | number formats, in the page's language |
| `lineCol(line)`, `catFill(category)` | the colour of a line, of a category (from the settings) |

**Changing a chart:** change what it counts or how it draws in its function; keep reading from `SEL_NC` so the filters
apply; put any new text in `STR` (both languages).

**Adding a chart:** copy a similar chart's function under a new key, add the key to `V2F` and its titles to `GSTR`, then add
the key to `V2L` on the tab you want. Its card gets the ⤓ Image button by itself.

### Values still written in the code

A few values are written in the dashboard's JS, not in a setting: `OPS_MSN` (the connection operations per aircraft of the
MIP A350, 5,572, for the errors per million operations), `CONN_LINES` (the lines whose cable defects count as connector
defects: A330, A350) and `CMO` (the causes added at first on "Les causes mois par mois"). To change one, change the JS.

### The colours

Colours are CSS variables at the top of the CSS (`--ink`, `--s1`, `--up`, `--down`...). The colours of the lines and of the
categories come from the settings (`2_lignes.csv`, `2_categories.csv`). Every style rule starts with `.fto2`, so the
dashboard's styles stay inside its sandbox: keep that on new rules.

## 5. The alarms (the bell)

**What it does:** line by line, it compares the defects of the last 4 finished weeks with the 12 weeks before, per MSN built.
It rings when the rise is too big to be chance: minor or major. It also catches slow rises over several months and aircraft
with far more NCs than usual. The settings (weeks, thresholds, how many shown) come from `3_alarmes.csv`.

**The code:**

| Part | Where |
|---|---|
| The statistics | between `ALARM ENGINE START` and `ALARM ENGINE END`: `run` (the test), `seen` (an alarm marked as seen), `spark` (the small curve) |
| What is followed | `alCompute` (in `MODEL`, section 6): all defects, categories, causes, sub-codes, stations, where found, products, cable requests, aircraft, per line |
| The bell on screen | `alRender` (the list), `alGo` (a click opens the problem), `alText` / `alName` (the wording) |

**The MFT page has its own copy of the alarm engine.** If you change one, change the other the same way, or the two pages will
ring differently.

**Early in the year the bell is quiet.** It compares 4 weeks with the 12 before, inside the year followed: until the year
has 16 finished weeks (late April) it says "Pas encore assez de semaines pour comparer". This is by design, not a fault.

## 6. The MFT page's code

One line at a time: the week's Pareto, the analysis, and the follow-up of the MFT actions. It keeps both years, so that a
week, a month or an action is compared with the weeks before it across the new year. Like the dashboard, it has a
**Responsabilité** list (FTO2, Suppliers, Others), and every count, chart and the bell follow the groups ticked. Its JS, from
top to bottom:

| Section | What is there |
|---|---|
| `the two Slate tables -> the page's data` | its own adapter (simpler than the dashboard's) |
| `the store` | where actions typed on the page are kept without the key `store`: **in this browser only** |
| `the shared store` | with the state key `store`: the actions kept for everyone (`fto2SharedStore`, below) |
| `data`, `weeks (ISO)`, `state`, `helpers` | the data, the week numbers, what the user chose (line, phase, period) |
| `controls` | the line, phase and period buttons |
| `tab 1: the week's Pareto` | the Pareto of the week against the weeks before |
| `tab 2: analysis` | what goes up, what goes down, recurring FINs |
| `tab 3: actions` | the action follow-up: each action against its target |
| `the action form` | adding or editing an action on the page |
| `the bell` | the alarm engine (its own copy) and its list |
| `events` | the clicks |
| `Slate: wait for the two queries` | the loader |

**Where the actions come from:** `1_actions_mft.csv` in the settings, through `ref`. They replace the browser's copy at every
load. With no saved actions (below), the page starts from the table's.

**The actions kept for everyone** (state key `store`, the query `q_fto2_mft_store`). The actions are kept in one object of
the NC writer's object type, *a30 Nc Writer Dataset*: its Msn is `MFT-ACTIONS`, its Texte Sap holds the whole list as JSON
(`{page, saved_at, actions}`). `fto2SharedStore` has the same calls as the browser store, so the rest of the page does not
change. At each change it updates its own copy at once, then puts the whole list as one row in the state key `store_row` and
fires the event `save` with it, as the NC writer does with an NC. A Slate event puts the row into a variable, and the
variable's change submits the object type's Action widget: one click on the page saves the list for everyone. Each save
adds an object; the page takes the one saved last. The alarms' "Vu" marks stay in the browser.

**Not settled yet: reading the saves back.** The query `q_fto2_mft_store` reads the Postgres copy of the object type's data,
which lags behind the Ontology; Slate's "foundry" HTTP source did not reach the API that reads the objects directly. Until a
way is found, an action changed on the page is not kept: the table `1_actions_mft.csv` is what everyone sees, and the
dashboard's bell knows only the actions of the table.

**Its thresholds** ("what goes up", "what goes down", recurring FINs: the `mft_` rows) come from `2_reglages_pages.csv`,
the action targets (the `action_` rows) from `1_reglages_pages.csv` (the sheet *Target and pages*).

## 7. The NC writer's code

A page of its own, which helps write an NC to the standard: the person picks the product and the place of detection, then
each defect from the official code sheet (nature, object, sub-code, quantity, location), and the page writes the SAP text.
It reads no query. Its JS, from top to bottom:

| Section | What is there |
|---|---|
| `CONFIG` | the state key (`submission`) and the event (`submit`) used to hand the NC to Slate, and the message shown once it is sent |
| `NATURES` | the official code sheet: each nature (Q01, Q03... T08) with its objects, sub-codes, severity and RPN |
| `PRODUITS`, `DETECTIONS`, `FIN_MAPPING` | the products, the places of detection, the FINs suggested for each nature |
| `CTX_OPTIONS`, `ACT_OPTIONS` | the ready-made sentences for the context and the action asked |
| `buildSapText`, `buildRow` | the SAP text, and the row saved: date, MSN, product, place of detection, number of defects, SAP text, defects as JSON |
| `sendToSlate` | the only place that talks to Slate |

**Saving an NC.** On "Soumettre la NC", `sendToSlate` puts the NC as one row in the state key `submission` and fires the
event `submit` with it (the sandbox's state is not seen by the other widgets: the NC leaves with the event). In the Slate
application, that event sets the variable `v_submission` with the row; the Action widget of the object type *a30 Nc Writer
Dataset* takes its values from that variable (Detection, Produit, Msn, Texte Sap, Total Defauts; the key, Timestamp, is
filled by the action), and the variable's change submits it. So the NC is saved in one click. To change a list (a product,
a FIN), change it at the top of the JS.

## 8. Editing a page in Slate

1. Open the page's Slate application in edit mode, and its code sandbox.
2. **Keep a copy of the current JS** (or CSS, HTML) as it is: it is your way back.
3. Make the change in the sandbox. The dashboard's JS is long, and Slate's editor is slow with it: a search for the
   function's name is the quickest way in.
4. Check the page: both languages, Essentiel and Deep dive, a few filters, the chart you changed with ⤢ **Enlarge**. Note the
   headline figures before and after: only what you meant to change should move. Check the MFT page too when the change
   touches the bell or the tables.
5. If the page breaks, paste the previous version back.

**Three rules for code in Slate:**

- **Never two `{` in a row** in the JS. Slate reads them as a link to a query and breaks the code.
- **Every CSS rule starts with `.fto2`**, so the styles don't leak into the rest of the Slate page.
- **No data in the code.** Data and settings come from the queries. A list or a value that someone may want to change belongs
  in a setting (*The settings, table by table*), read by the update and passed to the page through `ref`.

**A new column from the update** (*The update, step by step*, section 6): add it to the query's SQL in Slate, read it in the
adapter (`fto2FromTables`: add it to the NC's or the defect line's list), then use it in a chart.

## 9. When a page shows a box

| The box says | What it means | Where to look |
|---|---|---|
| Still waiting for a query, with its name | The query doesn't exist under that name, or fails | The query's name and SQL in Slate |
| "La requête … n'a renvoyé aucune ligne" | The query works but the table is empty | The sync, then the update's last run |
| "aucune NC lisible … colonnes reçues : …" | The query returns columns the page doesn't expect | Compare them with the table's columns |
| "exactement N lignes reçues" | Slate probably cut the result | A row limit on the query |
| The shared actions are not read yet (MFT page) | The query `q_fto2_mft_store` did not answer | The query, its table and its column names (section 6) |
| An error with a line of code | The JS has a mistake | Paste the previous JS back |
| The HTML part is missing | The HTML tab is empty | Paste the HTML part |

An empty page with no box at all is usually a rights problem: the person can open the application but not the four tables.
