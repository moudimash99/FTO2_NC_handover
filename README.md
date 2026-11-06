# FTO2 NC dashboard

Three pages on the non-conformities (NC) of plant FTO2: the **dashboard** (Essentiel and Deep dive), the **MFT page** (weekly
Pareto, analysis, action tracking) and the **Tableau Elizabeth**. They run in Skywise (Slate) and as files on a laptop.

New here? Start with **`docs/handover.md`**: what the pages are, how to keep them running, what is still open.

## How it fits together

```
Skywise data (NCs, work orders, aléas)          config/  (the settings, one table each)
              \                                    /
               fto2/  the backend (Python): rules, costs, plan, 2025, alarms settings...
                 |
   tables: fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions, fto2_dash_ref
                 |
   the pages (JavaScript): filter, add up, draw
```

- **`config/`**: everything someone may want to change. One `;` table per subject, opens in Excel. The first character of
  the name is the level: `1_` everyday (anyone), `2_` rules (someone careful), `3_` expert (technical).
  `config/lisez_moi.csv` lists every table, what it changes and who should edit it. **`config/README.md`** is the full guide:
  how the tables are built and how to fill each one.
- **`scripts/`**: turn a raw file into its everyday table (Avances / Retards, EqMSN, cable tracker, MFT trackers).
  A row corrected by hand (source = manuel) is kept when the script runs again.
- **`fto2/`**: the backend. One file per subject; the same code runs on the laptop and in the Skywise notebook.
- **`build/templates/`**: the dashboard page (`dashboard.html`) and its calculations (`model.js`, shared with the optional
  Slate functions).
- **`build/`**, **`07_scripts/mft/`**, **`07_scripts/elizabeth/`**: build the pages and their Skywise files.
- **`tests/`**: the checks, and the reference snapshot of every number the pages show.
- **`03_reports/skywise/`**: what goes into Skywise, and `README.md` there: how to set it up.

The other folders hold the inputs (`06_input_data/`, `04_reference/` for the AI labels), earlier work and documents.

## Run it on the laptop

```
python3 -I build/build_all.py                    # the backend, the dashboard and the Skywise files
python3 -I 07_scripts/mft/build_mft.py           # the MFT page
python3 -I 07_scripts/elizabeth/build_elizabeth.py   # the Tableau Elizabeth
python3 -m unittest discover -s tests -t .       # the checks (seconds)
```

The pages are written to `03_reports/` (`FTO2_NC_Dashboard.html`, `FTO2_MFT.html`, `FTO2_Elizabeth.html`).
Needs Python 3 with pandas, numpy and openpyxl (`requirements.txt`); the page checks need Node and Playwright.

## Change something

See `docs/comment_faire.md`: change a rule (e.g. what counts as REC), a rate, a target, a product, update the production plan,
add an MFT action, and check that nothing else moved.

How the pages themselves work (to change a chart or add one): `docs/front_end.md`.

For the team in Skywise: `docs/code_guide.md` (where to look, by type of question) travels in the notebook kit as
`CODE_GUIDE.md`, and `config/README.md` (every settings table) travels with the settings as `data/config/README.md`.
Both are written for someone who only sees the Code Workspace and the Slate app.
