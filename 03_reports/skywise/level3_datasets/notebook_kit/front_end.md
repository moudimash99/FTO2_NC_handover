# Front end: how the pages' code works

The front end is the three pages of the Slate app: the **dashboard**, the **MFT page** and the **Tableau Elizabeth**. They
read the tables the notebook writes, then filter, add up and draw. This guide explains their code.

The three guides: `config.md` (the settings tables; in the Code Workspace also as `data/config/README.md`), `logic.md` (the
notebook's code) and `front_end.md` (the pages' code); these two are also in `notebook_kit/`.

**Contents**

1. [The big picture](#1-the-big-picture)
2. [How the data reaches a page](#2-how-the-data-reaches-a-page)
3. [The dashboard's code](#3-the-dashboards-code)
4. [Finding and changing a chart](#4-finding-and-changing-a-chart)
5. [The alarms (the bell)](#5-the-alarms-the-bell)
6. [The MFT page's code](#6-the-mft-pages-code)
7. [The Tableau Elizabeth's code](#7-the-tableau-elizabeths-code)
8. [Editing a page in Slate](#8-editing-a-page-in-slate)
9. [When a page shows a box](#9-when-a-page-shows-a-box)

---

## 1. The big picture

```
 Postgres (synced from the notebook's tables)
        |
 Slate queries: q_fto2_nc, q_fto2_def, q_fto2_dis, q_fto2_ref
        |
 the sandbox's state box: links each query to a name the page knows
        |
 the page's code (JS): waits for the data, turns it into lists, then
     filters  ->  adds up  ->  draws (SVG charts, tables)
```

Each page is one Slate **code sandbox** with four parts:

| Part | What it holds |
|---|---|
| CSS | the look: colours, sizes, spacing |
| HTML | the frame: header, filter bar, tabs, one empty box per chart |
| JS | the code: plain JavaScript, no outside library |
| State | the links to the queries, e.g. `{"nc": "{{q_fto2_nc}}", ...}` |

**The rule of the split:** the notebook decides and calculates (which NC counts, what each defect is, what it costs; see
`logic.md`). The pages only filter, add up and draw. A number wrong everywhere is a notebook question; a number wrong on one
chart only is a page question.

## 2. How the data reaches a page

1. **The queries** read the four tables in Postgres (`foundry_sync` schema). Their SQL only lists the columns.
2. **The state box** gives each query result a name: `nc` (one row per NC), `def` (one row per defect line), `dis` (the aléas
   with no NC, dashboard only), `ref` (the reference data).
3. **The loader**, at the very end of the JS, watches those four names. When all have arrived, it starts the page. If one is
   missing for too long, it shows a box saying which one (section 9).
4. **The reference data** comes in pieces of text (`partie`, `morceau`, `texte`). `fto2RefBlocks`, at the top of the JS, glues
   each part's pieces back together and reads them as one block: the production plan, 2025, the cable requests, the MFT
   actions, the cost settings, the cause tree, and the page settings (target, filters at opening, colours, alarm settings).
5. **The adapter** `fto2FromTables` (between `ADAPTER START` and `ADAPTER END`) turns the two tables into the page's data `D`.

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
| `// ---- 1. Overview`, `2. Pareto`, `3. Weekly Pareto`, `4. Cost`... | one section per tab, with that tab's charts |
| `ALARM ENGINE START` … `END` | the alarm statistics (section 5) |
| `Dashboard v2 (main page)` | which charts appear on which tab, and their drawing functions (section 4) |
| `filter bar` | the filters and what happens when they change |
| `language, tabs, minor switch` | the language switch, the tabs, `renderAll` |
| `Simple mode` | the Essentiel mode (Synthèse and Détail) |
| the end of the file | the loader (section 2) and the error box |

Sections marked "local page only", the Gallery, the Review and the Mock-up are not shown in Skywise: leave them.

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

So a new year needs no change in the pages: the notebook sends the new year, and everything above follows.

### What happens when someone clicks

1. **A filter changes** (the filter bar, or a click on a chart). The filters are kept in `GF`: dates (`from`, `to`), period
   (`preset`), line, phase, Responsabilité boxes (`liab`), plant switch (`fto2`), data source, cost mode, and a clicked value
   (`pick`).
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

### Texts and languages

Every text is in `STR`: `STR.fr` and `STR.en`, by key. The code uses `S('key')`, with values filled in where `{n}`, `{v}`...
appear. The HTML uses `data-t="key"`, filled in by `applyText()`. The chart titles are in `GSTR` (section 4). To change a
text, change it in both languages.

### Essentiel and Deep dive

`MODE` is `simple` (Essentiel) or `expert` (Deep dive). Essentiel shows two tabs (Synthèse, Détail) made of charts borrowed
from the Deep dive tabs (`V2L.syn`, `V2L.det`). Détail's charts run from January to the end of the period (`ytd`).

## 4. Finding and changing a chart

### Where each chart is placed

In the section `Dashboard v2 (main page)`, **`V2L`** lists the chart cards of each tab, by key:

```
ov:     top: ['VT', 'VN', 'VB', 'a:lead', 'VX'], fold: ['a:cal']
pareto: top: ['a:bub', 'a:bump', 'a:flow', '78', '76', 'VM', 'VQ', '53'] ...
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

**To find a chart's code from the page:** take a few words of its title, search them in the JS: they lead to its `GSTR` or
`STR` entry, whose key leads to its function.

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
| `lineCol(line)`, `catTok(category)` | the colour of a line, of a category (from the settings) |

**Changing a chart:** change what it counts or how it draws in its function; keep reading from `SEL_NC` so the filters
apply; put any new text in `STR` (both languages).

**Adding a chart:** copy a similar chart's function under a new key, add the key to `V2F` and its titles to `GSTR`, then add
the key to `V2L` on the tab you want.

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

One line at a time: the week's Pareto, the analysis, and the follow-up of the MFT actions. Its JS, from top to bottom:

| Section | What is there |
|---|---|
| `the two Slate tables -> the page's data` | its own adapter (simpler than the dashboard's) |
| `the store` | where actions typed on the page are kept: **in this browser only** |
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
load. An action typed on the page stays in that browser until someone adds it to the table.

**Its thresholds** ("what goes up", "what goes down", recurring FINs, action targets) come from `2_reglages_pages.csv`
(the `mft_` and `action_` rows).

## 7. The Tableau Elizabeth's code

A line's NCs, three families of problems, a Pareto, and the weeks over a threshold (10 NCs a week by default). Its JS:

| Section | What is there |
|---|---|
| `the two tables -> the page's data` | `elzFromTables`: its own adapter |
| `families` | how an NC is put in a family (cables first, then the others); `cableWhy` says why an NC counts as a cable problem |
| `weeks (ISO)` | week numbers, shutdown and low weeks |
| `state`, `helpers` | line, phase, period, threshold; remembered in the browser |
| `render` | the drawing |
| `events` | the clicks |
| `start` | the loader |

## 8. Editing a page in Slate

1. **Copy the current JS** (or CSS, HTML) out of the sandbox and keep it as it is: it is your way back.
2. Make the change in a text editor (the dashboard's JS is long; Slate's editor is slow with it), then paste it back.
3. Check the page: both languages, Essentiel and Deep dive, a few filters. Note the headline figures before and after: only
   what you meant to change should move.
4. If the page breaks, paste the previous version back.

**Three rules for code in Slate:**

- **Never two `{` in a row** in the JS. Slate reads them as a link to a query and breaks the code.
- **Every CSS rule starts with `.fto2`**, so the styles don't leak into the rest of the Slate page.
- **No data in the code.** Data and settings come from the queries. A list or a value that someone may want to change belongs
  in a settings table (`config.md`), read by the notebook and passed to the page through `ref`.

**A new column from the notebook** (`logic.md`, section 6): add it to the query's SQL in Slate, read it in the adapter
(`fto2FromTables`: add it to the NC's or the defect line's list), then use it in a chart.

## 9. When a page shows a box

| The box says | What it means | Where to look |
|---|---|---|
| Still waiting for a query, with its name | The query doesn't exist under that name, or fails | The query's name and SQL in Slate |
| "La requête … n'a renvoyé aucune ligne" | The query works but the table is empty | The sync, then the notebook's run |
| "aucune NC lisible … colonnes reçues : …" | The query returns columns the page doesn't expect | Compare them with the table's columns |
| "exactement N lignes reçues" | Slate probably cut the result | A row limit on the query |
| An error with a line of code | The JS has a mistake | Paste the previous JS back |
| The HTML part is missing | The HTML tab is empty | Paste the HTML part |
