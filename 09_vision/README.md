# 09_vision: where the dashboard can go next

A working prototype of the next dashboard, built overnight on 19–20 Oct 2026 on its own branch (`claude/vision-wow`)
so it does not touch the dashboard work on `claude/funny-johnson-q41xki`. Nothing in `build/`, `03_reports/` or
`05_outputs/` is changed.

| File | What it is |
| --- | --- |
| `FTO2_Vision.html` | The prototype page (one file, opens offline; plain JavaScript and SVG, no library, so it can go into a Slate code box like the current dashboard) |
| `VISION.md` | The write-up: what the data says that the dashboard does not show yet, what to change visually, the roadmap and the data to ask for |
| `build_vision.py` | Packs the dashboard outputs and the 2025 NCs into the page; writes `expected.json` |
| `template.html` | The page: CSS, HTML and the script that computes every figure from the rows |
| `check_vision.js` | Opens the page headless, sets four filter settings and compares the page's figures with `expected.json`; also checks presentation mode, phone width and script errors |
| `prep_2025.py` | 2025 NCs from the 19 Oct archive (`06_input_data/work_orders_disruptions_nc2025.rar`, branch `main`) with the 2026 scope rules and parser v4.8; writes `data/nc_2025.csv`, `data/defects_2025.csv` (no NC text) |
| `pins.py` | Reads the two pins of a swapped-wire defect from the text (`... ENTRE LES BORNES 41 ET 42`) |

## Rebuild

```
unar -o <W> 06_input_data/work_orders_disruptions_nc2025.rar      # from branch main; only to refresh 2025
python3 -I 09_vision/prep_2025.py <W>/wo .
python3 09_vision/build_vision.py                                  # reads 05_outputs/fto2_nc.csv, fto2_defects.csv
NODE_PATH=$(npm root -g) node 09_vision/check_vision.js            # all checks passed
```

## Rules the page follows

- Same scope as the dashboard: FTO2 = raised at FTO2, FTO2 liable, not deleted; customer returns = raised elsewhere,
  FTO2 liable. Default filters: all lines, Série, all defects (722 NCs, 2,704 defects, 165,744 EUR on the 28 Sep extract).
- 2025 is counted the same way (FTO2 liable, not deleted, no ERMA, same phase rule) and up to the same calendar date.
  Check: January 2026 is in both files; 83 of the 86 January NCs of the 2025 file are in the 2026 extract.
- Causes: the root-cause labels for 2026 everywhere, except the 2025 → 2026 comparisons, which use parser v4.8 on both
  years (the only labels 2025 has). Cable year-on-year uses the parser's cable flag on both years.
- Every sentence that states a finding is computed from the filtered rows; the "Noms / Names" button turns titles back
  into plain chart names (the current dashboard's rule).
- Alerts ("À regarder"): a cause is listed when its last four weeks are above the rate of the other weeks of the year
  (shutdown weeks with fewer than 10 defects left out) with a Poisson probability below 5 % (amber) or 1 % (red),
  at least 8 defects and 25 % above expected; a location (FIN) on 3 or more aircraft within four weeks; 2 or more
  customer returns within four weeks; NCs open for more than 30 days.
