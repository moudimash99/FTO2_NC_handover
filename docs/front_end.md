# How the pages work (front end)

This is for the person who changes how a page looks or adds a chart. To change a rule, a rate or a target, you don't need
any of this: see `comment_faire.md`.

## The short version

- Each page is one HTML file built from a template. The template holds the page's look (CSS), its layout (HTML) and its code
  (plain JavaScript, no framework, no outside library).
- The page receives tables (one row per NC, one row per defect line) and a block of reference data. It filters them, adds them
  up and draws the charts as SVG.
- The same code runs on the laptop (an HTML file) and in Skywise (pasted into a Slate code sandbox).
- The calculations that are more than adding up (targets and forecast, alarms, cost explanation) are in a separate file,
  `build/templates/model.js`. It can also run as Slate functions (see the end).

## The files

| Page | Template | Built by | Output |
|---|---|---|---|
| Dashboard (Essentiel and Deep dive) | `build/templates/dashboard.html` and `build/templates/model.js` | `build/build_all.py` | `03_reports/FTO2_NC_Dashboard.html` |
| MFT page | `07_scripts/mft/mft_template.html` | `07_scripts/mft/build_mft.py` | `03_reports/FTO2_MFT.html` |
| Tableau Elizabeth | `07_scripts/elizabeth/elizabeth_template.html` | `07_scripts/elizabeth/build_elizabeth.py` | `03_reports/FTO2_Elizabeth.html` |

The build also writes the Skywise versions into `03_reports/skywise/` (the CSS, HTML and JS to paste into Slate).
**Never edit the files in `03_reports/`**: the next build overwrites them. Edit the templates, then build again.

The MFT page shares the dashboard's alarm engine: the build copies the block between `ALARM ENGINE START` and `ALARM ENGINE END`
of `dashboard.html` into it. So both pages always raise the same alarms.

## How the dashboard template is laid out

`build/templates/dashboard.html`, from top to bottom:

1. **CSS** (`<style>`): colours are variables at the top (`--ink`, `--s1`, `--up`, `--down`...), then one block per part of the
   page. In Slate every rule is prefixed with `.fto2` by the build, so the dashboard's styles don't leak into the Slate page.
2. **HTML** (`<div class="wrap">`): the header, the filter bar, the tabs, and one panel per tab (`id="p-ov"`, `p-pareto`...).
   Most charts are empty boxes that the code fills.
3. **The data block** (`<script id="fto2-data">`): filled by the build on the laptop. In Skywise the data comes from the
   queries instead.
4. **The adapter** (between `ADAPTER START` and `ADAPTER END`): `fto2FromTables` turns the tables into the page's data `D`.
5. **The page's code**, one big function. In order:
   - the texts in French and English (`STR`), and the settings (`SET`, from `config/`);
   - the calculations: `model.js` is put in at the line `/*@@MODEL@@*/`, then the layer that takes them either from the page
     or from Slate;
   - then one section per tab, each starting with a comment line `// ---- 1. Overview`, `2. Pareto`, `4. Cost`...;
   - the alarm engine (`ALARM`), the filter bar, the tabs, and at the end the Essentiel mode.

## The data inside the page

`D.ncs` is a list of NCs, each one a list of values by position. The positions most used:

| | | | |
|---|---|---|---|
| `[0]` NC number | `[1]` creation date | `[3]` line (A350...) | `[5]` 1 if FTO2 is liable |
| `[6]` cost rule | `[8]` where found | `[12]` cost (level 3) | `[23]` serie / client / autre |
| `[24]` phase (SERIE, REC, FTI) | `[25]` MSN | `[26]` product | `[27]` station |
| `[33]` NC type | `[39]` data source | `[40]` cost steps (minutes...) | `[42]` plant |

`D.defects` is a list of defect lines: `[0]` NC number, `[1]` line number, `[11]` category, `[12]` root cause, `[13]`
sub-category, `[14]` minor, `[17]` share of the cost, `[18]` text, `[22]` sub-code, `[23]` FIN.

The full list is in the adapter (`fto2FromTables`), next to the table columns it reads. The columns themselves are described
in `fto2/core.py` (`NC_COLUMNS`, `DEF_COLUMNS`).

## What happens when someone clicks

1. A filter changes (filter bar, or a click on a bar or a point of a chart).
2. The page updates its filters `GF` and calls `select()`. `select()` makes the list of NCs on screen: `SEL_NC` (everything
   the filters keep), `SER_NC` (FTO2's own, without customer returns), `CLI_NC` (customer returns).
3. `renderAll()` redraws every tab. Each chart reads `SEL_NC`, counts, and writes its SVG into its box.

A click on a chart value works through `data-pick="kind|value"` on the SVG element. The page catches the click, sets
`GF.pick`, and every tab follows. Tooltips work the same way: `data-tip="title|line|line"`.

## Adding or changing a chart

1. Find a chart that looks like what you want, and its function (search for its title's text key in `STR`, then for that key).
2. Copy the function, change what it counts. Keep reading the NCs from `SEL_NC`, so the filters apply.
3. Draw with the helpers: `svg()`, `tx()` (a text), `tip()` (a tooltip), `pk()` (a click that filters), `gSet()` (put the
   chart and its legend in its box).
4. Put every text in `STR.fr` and `STR.en`, and use it with `S('key')`. The dashboard stays in French by default.
5. Build, open `03_reports/FTO2_NC_Dashboard.html`, check it in both languages, then run the checks (`tests/README.md`).
   The snapshot will show the new chart as a difference: that is expected. Check it, then update the reference.

## In Skywise

The dashboard is a Slate **code sandbox**. Its JavaScript is the same page code, wrapped by a small piece of "glue" (written
by `build/skywise_pack.py`). The glue:

- waits for the queries (`q_fto2_nc`, `q_fto2_def`, `q_fto2_dis`, `q_fto2_ref`) through the sandbox's state, then starts the page;
- shows a box with a plain message if something is missing (a query that doesn't answer, no rows, a cut result).

Things to know when you change the page for Skywise:

- **No double braces** (two `{` in a row) in the JavaScript. Slate would read them as a binding.
- **No outside resources.** Only the Google font is imported; if Slate blocks it, the page falls back to standard fonts.
- **No data in the code.** Data and reference data come from the queries. `tests/test_pages.py` fails if a big block of data is
  written in the JavaScript.
- **Light mode only** in Slate. The dark-mode styles are dropped by the build.

## The calculations, here or in Slate

`build/templates/model.js` holds the calculations that are more than adding up: the selection, production per MSN, the
targets and forecast, the cost explanation of an NC, and the alarm list. It draws nothing.

The page reaches three of them through small functions: `objectif()` and `lignes()` for the targets, `alarmesNow()` for the
bell, `cxOf()` for the cost explanation. Each one either computes in the page or takes the answer from Slate:

- **On the laptop, or in Skywise without functions:** the page computes everything.
- **In Skywise with the Slate functions** (`03_reports/skywise/level3_datasets/fonctions/`): the page sends its filters to
  Slate, the chart says "Calcul dans Slate…" for a moment, and the page draws the answer. If Slate doesn't answer within 15 s,
  the page computes it itself and says so.

Because the page and the functions use the very same file, they can't give different numbers. `tests/test_slate_functions.py`
runs the functions as Slate does, and the snapshot of the Skywise page with the functions is compared with the laptop page.

## Checking a change

```
python3 -I build/build_all.py
python3 -m unittest discover -s tests -t .
```

then the full comparison of every number the pages show (about 30 minutes): `tests/README.md`. A change that should not move
any number must give "identical". A change that should move some numbers: check that only those moved.
