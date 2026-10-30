# MFT Qualité FTO2 in Slate

The MFT page (Pareto de la semaine, Analyse, Suivi des actions, the alarm bell) in a Slate code sandbox, fed by the same
datasets as the dashboard's level 3. Same setup as level 3: two queries, one code sandbox, its state.

## Setup (in the new Slate app)

1. **Two queries** on the Postgres source the dashboard uses (`postgate-airbus-2`):
   - `q_fto2_nc` with the text of `q_fto2_nc.sql` (dataset `fto2_dash_nc`),
   - `q_fto2_def` with the text of `q_fto2_def.sql` (dataset `fto2_dash_defects`).

   They are the dashboard's level-3 queries, unchanged: if the app already has them, use them as they are.
2. **One Code Sandbox**, full width, about 1,400 px high. Paste:
   - `fto2_mft.css` into its CSS tab,
   - `fto2_mft.html` into its HTML tab,
   - `fto2_mft.js` into its JS tab.

   (Or open `FTO2_MFT_Slate.html` and copy what sits between the START and END lines of each part.)
3. **Its state**: the content of `state.json`:

   ```json
   { "nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}" }
   ```

Expected: "Chargement des données Slate…", then the page on A350, week S39 (21–27 sept.): 10 NC, 73 défauts, first category
MEO Facteur humain (27 défauts); the bell shows 2 alarms; "Suivi des actions" lists the 5 A350 actions of the MFT tracker
(9 on all lines).

If something is wrong, the box at the top of the page says what: a query it is still waiting for (check its name), a query
with no row, or the columns it received when no 2026 FTO2 NC could be read.

## What to know

- **Data**: the NCs raised at FTO2 (plant FTO2 or FT02) created in 2026 and their defect lines, read from the two queries each
  time the page opens. When the notebook rewrites the datasets, the page follows; nothing to rebuild.
- **Fixed references, written in the JS** (as the dashboard's): sub-code names, the production plan's products, MSN built
  per week, end of build per MSN (for the alarms), and the MFT trackers' actions. To update them: change the files in
  `04_reference` / `06_input_data`, rebuild, paste the new `fto2_mft.js`.
- **Actions are saved in the browser**, on the computer where they are entered: a Slate code sandbox has no shared store.
  The first time, the page shows the trackers' actions; new actions, edits, weekly points and the alarms' "Vu" marks stay on
  that computer and are not shared with the other users of the app. The note above the actions says so. If Slate's sandbox
  blocks the browser's storage, the note says that instead: edits then last until the page reloads. Sharing them needs a
  table Slate can write to (or a Foundry action), to be set up.
- The action form saves without a form submission (Slate's sandbox allows none), with its button or Enter, and opens where
  the click was when the widget is taller than the screen.
- **A press on a bar filters the whole page**, as on the dashboard: the figures, the other lists, the defect table and the
  Analyse tab. One value per list (category, cause, sub-code, FIN), several lists can be combined; the chips above say what
  is picked (✕ removes one, "Tout retirer" all). Picks stay when the period changes and are cleared when the line changes.
- **The comparison "vs …"** is per week and names its weeks: the period against the working weeks just before it, as many as
  the period has (4 at least). Closure weeks and low-production weeks (the line under 60 % of its usual MSN per week, from the
  production plan: the summer holidays) are left out, so a month after August is compared with normal weeks.
- `preview_local_only.html` opens on a laptop with a frozen copy of the data, to look at the page: never paste it into Slate.

## Build

```bash
python3 -I 07_scripts/mft/build_mft.py
```

It writes `03_reports/FTO2_MFT.html` and this folder (`07_scripts/mft/build_mft_slate.py`, from the same template
`07_scripts/mft/mft_template.html`). Checked here: the page's data computed in the browser from the two tables are exactly
those of `FTO2_MFT.html` (988 NCs, 2,968 defect lines, same sub-code names, weekly volumes and build ends); same Pareto
view; tabs, bell and actions work; a new action is saved and still there after a reload; no error in the console.
