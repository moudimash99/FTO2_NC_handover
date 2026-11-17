# FTO2 NC dashboard

Pages on the non-conformities (NC) of plant FTO2: the **dashboard** (Essentiel and Deep dive), the **MFT page** (weekly
Pareto, analysis, action tracking), and the **NC writer** (writing an NC with the official codes). They run in Skywise
(the update: a Code Repository transform or the Code Workspace notebook; the pages: a Slate application); this folder
builds them and checks them.

New here? Start with **Start here – Developers** (`docs/guides/pdf/developers/en/1 Start here.pdf`; in French in
`developers/fr/`): a few short documents, one subject each. The users' documents are in `docs/guides/pdf/users/`.

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
  the name is the group: `0_` data (filled from the downloaded files, or history: not edited), `1_` the manager's settings
  (year, target, rates, shutdowns, part prices, MFT actions), `2_` rules and names, `3_` expert.
  `config/lisez_moi.csv` lists every table, what it changes and who should edit it.
- **Downloads**: the production plan (exports of the Tableau Avances / Retards) and the cable requests (the cable team's
  tracker) are read from the files saved beside the notebook as they were downloaded (`fto2/downloads.py`).
- **`fto2/`**: the backend. One file per subject; the same code runs here, in the Skywise notebook and in the Code
  Repository's transform (`fto2/transform_io.py`, `build/repository/`).
- **`build/templates/`**: the dashboard page (`dashboard.html`) and its calculations (`model.js`, shared with the optional
  Slate functions).
- **`build/`**, **`07_scripts/mft/`**: build the pages and their Skywise files. **`07_scripts/elizabeth/`**: an optional
  page (the Tableau Elizabeth), built the same way.
- **`08_tools/nc_writer_slate/`**: the NC writer, with its own checks and its Slate set-up (`README.md` there).
- **`tests/`**: the checks, and the reference snapshot of every number the pages show.
- **`03_reports/skywise/`**: what goes into Skywise, and `README.md` there: how to set it up.

- **`docs/`**: the four reference documents below (in French in `docs/fr/`), and the short documents for the users and
  the developers (`docs/guides/`: their sources in `users/` and `developers/`, the PDF in `docs/guides/pdf/`).

The data of a reference day is in `06_input_data/` (extracts), `04_reference/` (the cause labels) and `05_outputs/` (what
the build writes from it).

## Build and check

```
python3 -I build/build_all.py                    # the backend, the dashboard and the Skywise files
python3 -I 07_scripts/mft/build_mft.py           # the MFT page
python3 -I 07_scripts/elizabeth/build_elizabeth.py   # the Tableau Elizabeth
python3 -m unittest discover -s tests -t .       # the checks (seconds); the others: tests/README.md
```

The pages are written to `03_reports/` (`FTO2_NC_Dashboard.html`, `FTO2_MFT.html`, `FTO2_Elizabeth.html`).
Needs Python 3 with pandas, numpy and openpyxl (`requirements.txt`); the page checks need Node and Playwright.

## Change something

See `docs/comment_faire.md`: change a rule (e.g. what counts as REC), a rate, a target, a product, update the production plan,
add an MFT action, and check that nothing else moved.

## The reference documents

| Guide | Explains |
|---|---|
| `docs/config.md` | the settings tables: how they are built, how to fill each one, how the code reads them |
| `docs/logic.md` | the notebook's code: the run step by step, every file, the cost model, the tables it writes |
| `docs/part_prices.md` | the price list of rejected, scrapped and exchanged parts: set-up and how to fill it |
| `docs/front_end.md` | the pages' code: how the data arrives, the dashboard's layout, finding and changing a chart, the MFT page, Elizabeth |

They are written for someone who only sees the Code Workspace and the Slate app, and the build puts them there: `logic.md`
and `front_end.md` in the notebook kit, `config.md` as `data/config/README.md`.
