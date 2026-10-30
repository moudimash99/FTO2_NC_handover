# Synthèse et Détail in Skywise (Slate): two ways

The views page (`03_reports/FTO2_Vues.html`: the Synthèse and Détail tabs, the dashboard's header and filter bar, the bell)
packaged for a Slate app in two ways. Both show the same figures as the dashboard: they were checked against each other on
several filter sets (see "Checked here").

| | Way 1: JavaScript only in the page | Way 2: pre-computed by a Slate function |
|---|---|---|
| Folder | `way1_js_in_page/` | `way2_precomputed/` |
| Slate pieces | 3 queries, 1 code sandbox | 2 queries, 1 function, 1 variable, 1 event, 1 code sandbox |
| Who computes | the sandbox's JavaScript, in the browser, from the two tables | the function `f_fto2_views`; the sandbox only draws |
| What the sandbox receives | the two tables (about 1.4 MB) | the model for the filters chosen (about 750 KB for the whole year, 90 KB for one aircraft and one month) |
| A filter change | redrawn at once in the page | the filters go to Slate, the function re-runs (about 0.2 s here), the model comes back |
| Code to maintain | none: it is the dashboard template itself | the model follows the dashboard by itself; the drawing of the 7 charts is a copy (see below) |
| Set-up effort | low | medium |

**Which one:** way 1 first. It is the simplest and is the dashboard itself, so it never drifts. Take way 2 when the logic has
to live in Slate apart from the page: to reuse the model elsewhere (another widget, an export, a check), to keep the page
light, or to have the numbers computed in one place for several pages.

Everything in this folder is written by the build. Do not edit the files by hand; change the template or the build and rebuild.

## Build

```bash
python3 -I build/views_pack.py
```

`build/build_all.py` runs it too, after the dashboard pages. Input: the dashboard template (`build/templates/dashboard.html`)
and the main page's data block (`03_reports/FTO2_NC_Dashboard.html`: the two tables and the fixed references), so build the
dashboard first when the data changes. Way 1 is written by `build/views_pack.py`, way 2 by `build/views/build_way2.py`, which
reads these sources:

| Source | What it is |
|---|---|
| `build/views/model_core.js` | the computing part of each chart (in the dashboard it is mixed with the drawing) and the shape of the model |
| `build/views/render_core.js` | the sandbox page: header, filter bar, tabs, the 7 charts, the Pareto boards, the tables, the bell, the complete-chart animation |
| `build/views/sandbox_boot.js` | the Slate glue of the sandbox: model in, filters out |
| `build/views/slate_function.js` | the frame of the function `f_fto2_views` |
| `build/views/precompute_node.js` | the Node command that runs the model outside Slate |

The rest is copied from the dashboard template at each build, unchanged: the table adapter, the alarm engine, the selection,
production plan, forecast, target and 2025 functions (for the model); the strings in French and English, the colours, the
number formats and the SVG helpers (for the page). A function the build looks for and no longer finds stops the build with its
name (`PULL_FN`, `RENDER_FN` in `build_way2.py`).

## Way 1: JavaScript only in the page

Same set-up as the dashboard's level 3 (`../README.md`), with this page's files:

1. Add the queries `q_fto2_nc`, `q_fto2_def` and `q_fto2_dis` (`q_fto2_*.sql`, the dashboard's level-3 queries, unchanged; the
   third is optional).
2. Add a **Code Sandbox**, full width, about 1,400 px high. Paste `fto2_views.css` into its CSS tab, `fto2_views.html` into
   its HTML tab, `fto2_views.js` into its JS tab (or copy each part of `FTO2_Views_Slate.html` between its START and END
   lines).
3. Put `state.json` in its state: `{"nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}", "dis": "{{q_fto2_dis}}"}`.
4. Or, in a new empty app, try importing `FTO2_Views_way1.slate.json` (same caveat as the dashboard's level 4: not tried).

## Way 2: pre-computed by a Slate function, separation of concerns

```
  data                         logic                                    display
  q_fto2_nc  ─┐
              ├──▶  f_fto2_views (fto2_views_model.js) ──▶ state "model" ──▶  w_fto2_views (draws only)
  q_fto2_def ─┘           ▲                                                        │
                          │                                                        │ a filter changes:
                  v_fto2_filters ◀── event w_fto2_views.fto2Filters ◀── state "filters"
```

The function returns every number, series and table the page shows, for one set of filters. The page computes nothing: it
draws the model, keeps what is local to it (open tab, Pareto level, measure, cable shading, table search, the bell open) and
sends the filters of the bar back.

1. **Queries.** Add `q_fto2_nc` and `q_fto2_def` (`q_fto2_nc.sql`, `q_fto2_def.sql`, the same as level 3). No aléa query: the
   views show none.
2. **Variable.** Add a variable `v_fto2_filters`, type object, default value `{}` (the defaults: all aircraft, since 1
   January, Série, FTO2 plant, minor defects included, French).
3. **Function.** Add a function named `f_fto2_views` and paste the whole of `f_fto2_views.js` (330 KB: the references, the
   model, then the call that reads `{{q_fto2_nc}}`, `{{q_fto2_def}}` and `{{v_fto2_filters}}`). It returns `null` while a query
   runs, and `{error: "..."}` when the computation fails (the page shows it).
4. **Code sandbox.** Add a Code Sandbox named `w_fto2_views`, full width, about 1,400 px high. Paste
   `fto2_views_sandbox.css`, `fto2_views_sandbox.html` and `fto2_views_sandbox.js` into its three tabs (or copy each part of
   `FTO2_Views_way2_Slate.html`). Put `state.json` in its state: `{"model": "{{f_fto2_views}}"}`.
5. **Event.** Add an event: trigger `w_fto2_views.fto2Filters`, action "set variable `v_fto2_filters`", with the code of
   `event_fto2Filters.js`: `return {{w_fto2_views.state.filters}};`.

Expected: "Calcul des vues dans Slate…", then the default view: 910 NC (forecast end Dec. 1 298, target 898), 2,10 NC per MSN
(+49 % against 1,41), 347 k€, 34 customer returns. Aircraft A350 and "Dernier mois": 64 NC and 296 defects (period before 25
and 93), 7,21 NC per MSN since January (+51 % against 4,78), 27,3 k€.

If it does not work, the box at the top of the page says why: no Slate state (the sandbox's state is not set), no model after
30 s (check that `f_fto2_views` runs without error in the function editor, and the two queries), no readable NC (it lists the
columns `q_fto2_nc` sent).

### The model outside Slate

`precompute_node.js` runs the same model file in Node (no Slate, no browser):

```bash
node 03_reports/skywise/views/way2_precomputed/precompute_node.js 03_reports/FTO2_NC_Dashboard.html '{"line": "A350", "preset": "m1"}' model.json
```

The filters are `line` (`''`, `A350`, `A330`, `A320`, `A400M`), `preset` (`ytd`, `m1`, `m3`, `m6`, `m12`, `all`, or `custom`
with `from` and `to` as `YYYY-MM-DD`), `phase` (`SERIE`, `REC`, `FTI`, `''` for all), `fto2` (true: FTO2 plant only), `minor`
(true: minor defects included), `src` (`all`, `sky`, `man`, `gps`, `test`), `org` (`''`, `normal`, `missing_ids`), `lang`
(`fr`, `en`). Use it to check the numbers, or to compute models on a schedule for other uses.

### What way 2 does not do (way 1 does)

- The ⓘ panel "Comment la sélection est faite" (the count left after each filter).
- A click on a chart mark does not filter the page (the dashboard's chip "pick").

### Keeping way 2 in step with the dashboard

The numbers follow by themselves: the model calls the dashboard's own functions, copied at each build. The drawing of the
seven charts (cumulative trend, each line against its target, ranking of causes, causes 2025 against 2026, volume or unit
cost, connection errors per MSN, top three causes per product) and of the Pareto boards is a copy in `render_core.js`, as of
30 October 2026. When the dashboard changes one of these drawings, copy the change there, or say so and it will be done. The
words need nothing: they are the dashboard's, copied at each build.

## Checked here

- Way 2's model in Node against the dashboard: every figure above, the target of each line (A350 7,21 / 4,78, A330 6,28 /
  4,32, A320 0,15 / 0,02, A400M 4,73 / 4,20), the causes 2025 / 2026, the connection errors per MSN (mean 11,27, 2025 10,87),
  the top causes per product (MIP A350 38,99), the 4 alarms.
- The function file run as Slate would (its bindings replaced by values): same model; `null` while a query is missing;
  the error message for unreadable columns; rows instead of columns.
- Both local previews in a browser, side by side: same figures, sums and empty-chart messages for the default view, A330 ·
  3 derniers mois, A400M · all production types, 1 March to 31 May, A350 without minor defects; same look for every chart.
- Way 2 in the browser: filters through the stand-in for Slate (state, event, variable, function), the Pareto one level at a
  time, volume and cost, cable shading, table search, the bell and its alarm opening Détail, the complete chart and its
  skip, English, reset, a phone (no sideways scroll), no error in the console.

Not testable here, to watch on the first try of way 2:

- `SlateFunctions.setState`: the page accepts both forms (an object merged into the state, or a key and a value) and keeps
  the other keys. If the filters do not reach the variable, look at the state in Slate's inspector after a filter change.
- The order of the event and the state: the page fires `fto2Filters` once the state shows the new filters, at the latest after
  0.4 s (a known Slate pitfall: an event fired at once can read the old state).
- The size of the function (330 KB of code) and of the model in the state (up to about 750 KB for a whole year).
- The local previews (`preview_local_only.html`) carry the real tables and a stand-in for Slate: never paste them into Slate.
