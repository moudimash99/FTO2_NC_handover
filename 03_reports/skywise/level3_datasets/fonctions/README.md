# Slate functions: the calculations outside the page

The dashboard works without anything in this folder: the page computes everything itself. This folder is an option to try:
three calculations move out of the page into Slate functions, so that the page only draws.

| Calculation | Slate function | What it gives the page |
|---|---|---|
| Targets and forecast | `f_fto2_objectifs` | NCs and cost month by month, the forecast to December, the target line by line |
| Alarms (the bell) | `f_fto2_alarmes` | the list of problems for the filters on screen |
| Cost explanation ("Expliquer le calcul", cost tab) | `f_fto2_cout` | for every NC: euros of each step, and the minutes and material of each defect line |

There are two ways to set it up. Try one, then the other if you want to compare.

- **Way 1, three functions.** All three calculations run in Slate.
- **Way 2, two functions and a table.** Targets and alarms run in Slate. The cost explanation is worked out by the notebook,
  which writes it as a table (`fto2_dash_cout`). The page reads that table. This makes sense because the cost explanation does
  not change with the filters.

Both give the same figures as the page. This was checked on the laptop with a stand-in for Slate, on 36 views of the dashboard.
The cost explanation from the function and from the notebook's table agree on every NC and every defect line.

## How it works

When a chart needs a target or the alarms, the page writes the filters into its state and fires the event `fto2Filtres`. The
event copies them into the variable `v_fto2_filtres`. The two functions that read that variable run again and send back their
answer, and the page draws it. While it waits, the chart says **"Calcul dans Slate…"**. On the laptop this round trip takes
about half a second.

If a function fails, or gives no answer within 15 seconds, the page computes that calculation itself and says so in a yellow
box at the top. The dashboard keeps working either way.

## Set it up

Start from a dashboard page that already works (the main set-up guide, `../../README.md`, step 3).

**Both ways**

1. Rename the dashboard's code sandbox `w_fto2_dashboard` (the event below uses that name).
2. Add a variable `v_fto2_filtres`, type object, default value `{}`.
3. Add a function `f_fto2_objectifs`: paste the whole of `f_fto2_objectifs.js`.
4. Add a function `f_fto2_alarmes`: paste the whole of `f_fto2_alarmes.js`.
5. Add an event: trigger **w_fto2_dashboard › fto2Filtres**, action **set variable `v_fto2_filtres`**, with the code of
   `event_fto2Filtres.js` (one line: `return {{w_fto2_dashboard.state.filtres}};`).

**Way 1: three functions**

6. Add a function `f_fto2_cout`: paste the whole of `f_fto2_cout.js`.
7. Paste `state_3_fonctions.json` into the sandbox's state box, in place of the old state.

**Way 2: two functions and the notebook's table**

6. In the notebook's Data panel, add the dataset `fto2_dash_cout` (write). Run the notebook: its last lines say
   "fto2_dash_cout: … rows". Sync `fto2_dash_cout` to Postgres like the other tables.
7. Add a query `q_fto2_cout` on `postgate-airbus-2`, with the text of `q_fto2_cout.sql`.
8. Paste `state_2_fonctions.json` into the sandbox's state box, in place of the old state.

**To go back** to the page computing everything, paste `../state.json` into the state box again. The functions, the variable
and the event can stay; nothing uses them then.

## Check that it works

- Open the dashboard, Deep dive, Vue d'ensemble. The cumulative NC chart and the bell show after a short "Calcul dans Slate…".
  The figures are the same as with `../state.json`.
- Change the aircraft filter. The charts with targets say "Calcul dans Slate…" for a moment, then redraw.
- A yellow box saying "La fonction Slate f_fto2_… n'a pas répondu" or "a échoué" means that function is not working. The page
  then computes it itself, so the figures stay right. Open the function in Slate's editor to see its error.

## What could not be tested before Slate

These parts were only checked with the laptop stand-in. Watch them on the first try:

- **The state written by the page.** The page writes the filters with `SlateFunctions.setState`. It accepts both forms (an
  object, or a key and a value). If the filters never reach the variable, look at the sandbox's state in Slate's inspector after a
  filter change: the key `filtres` should hold `{"demandes": [...]}`.
- **The timing of the event.** The page fires `fto2Filtres` once the state shows the new filters, or after 0.4 s at the latest
  (an event fired too early can read the old state).
- **How long the functions take in Slate.** On the laptop: targets 0.1 s, alarms 0.2 s, cost explanation 0.1 s. Slate will be
  slower; how much is what this test is for.
- **The size of the cost explanation's answer** (about 370 KB for the whole year). Way 2 avoids it.

## Changing a calculation

Do not edit these files: the build writes them again. The calculations are in `build/templates/model.js`. The page and these
functions share that file, so they cannot drift apart. After a change, run `python3 -I build/build_all.py` and paste the
function files again. For the cost explanation in way 2, also change `fto2/cost/explain.py`: `tests/test_slate_functions.py`
fails if it no longer gives the same figures as the function.
