# 09_vision: where the dashboard can go next

A working prototype of the next dashboard, built overnight on 19–20 Oct 2026 on its own branch (`claude/vision-wow`)
so it does not touch the dashboard work on `claude/funny-johnson-q41xki`. Nothing in `build/`, `03_reports/` or
`05_outputs/` is changed.

| File | What it is |
| --- | --- |
| `FTO2_Vision.html` | The prototype page (published at https://claude.ai/artifact/KmELL2B43ksMwXPcEGdFov; one file, opens offline; plain JavaScript and SVG, no library, so it can go into a Slate code box like the current dashboard) |
| `FTO2_Vision_Notes.html`, `img/` | The notes page (published at https://claude.ai/artifact/W4Y6wLvN772mzHnxwYNvKu): findings, what to keep and change with crops of the 19 Oct dashboard, connections diagram, roadmap with a Now / Later / No choice per line saved in the page's store (collection `choices`) |
| `VISION.md` | The same in short, for the next session: findings, changes, roadmap ids `r01`–`r13`, where the choices are stored |
| `FTO2_Visual_Lab.html`, `template_lab.html` | The visual lab (published at https://claude.ai/artifact/KoTPorviVHFcDvEfkn6n8F): five other ways to draw the same rows (a defect's journey line → cause → station → decision, the year's rain, aircraft lifelines, connector faces, the river of causes with 2025 at equal production), each with a Keep / Later / No choice saved in the page's store (collection `lab`, documents `v1`–`v5`) |
| `build_vision.py` | Packs the dashboard outputs and the 2025 NCs into both pages; writes `expected.json` |
| `template.html` | The page: CSS, HTML and the script that computes every figure from the rows |
| `check_lab.js` | The same for the lab: defects, aircraft, NC dots, river and its equal-production outline for all lines, A350 and A320; the animation, phone width and script errors |
| `check_vision.js` | Opens the page headless, sets four filter settings and compares the page's figures with `expected.json` (counts, costs, every equal-production comparison by quarter and year to date); also checks presentation mode, phone width and script errors |
| `prep_2025.py` | 2025 NCs from the 19 Oct archive (`06_input_data/work_orders_disruptions_nc2025.rar`, branch `main`) with the 2026 scope rules and parser v4.8; writes `data/nc_2025.csv`, `data/defects_2025.csv` (no NC text) |
| `pins.py` | Reads the two pins of a swapped-wire defect from the text (`... ENTRE LES BORNES 41 ET 42`) |

## Rebuild

```
unar -o <W> 06_input_data/work_orders_disruptions_nc2025.rar      # from branch main; only to refresh 2025
python3 -I 09_vision/prep_2025.py <W>/wo .
python3 09_vision/build_vision.py                                  # reads 05_outputs/fto2_nc.csv, fto2_defects.csv
NODE_PATH=$(npm root -g) node 09_vision/check_vision.js            # all checks passed
NODE_PATH=$(npm root -g) node 09_vision/check_lab.js               # all checks passed
```

## Rules the page follows

- Same scope as the dashboard: FTO2 = raised at FTO2, FTO2 liable, not deleted; customer returns = raised elsewhere,
  FTO2 liable. Default filters: all lines, Série, all defects (722 NCs, 2,704 defects, 165,744 EUR on the 28 Sep extract).
- 2025 is counted the same way (FTO2 liable, not deleted, no ERMA, same phase rule) and up to the same calendar date.
  Check: January 2026 is in both files; 83 of the 86 January NCs of the 2025 file are in the 2026 extract.
- Years are compared at equal production: on each line the 2025 count is multiplied by aircraft 2026 ÷ aircraft 2025
  in the same window (quarter or year to date). Aircraft = MSNs with at least one FTO2 NC in the window (any defect
  type) until a 2025 production file exists; a line with fewer than 8 aircraft in 2025 (A320) is left out. The hero
  says the gap narrowed or widened only when the recent count is unlikely at the early gap (Poisson, 5 %).
- Causes: the root-cause labels for 2026 everywhere, except the 2025 → 2026 comparisons, which use parser v4.8 on both
  years (the only labels 2025 has). Cable year-on-year uses the parser's cable flag on both years.
- Every sentence that states a finding is computed from the filtered rows; the "Noms / Names" button turns titles back
  into plain chart names (the current dashboard's rule).
- Alerts ("À regarder"): a cause is listed when its last four weeks are above the rate of the other weeks of the year
  (shutdown weeks with fewer than 10 defects left out) with a Poisson probability below 5 % (amber) or 1 % (red),
  at least 8 defects and 25 % above expected; a location (FIN) on 3 or more aircraft within four weeks; 2 or more
  customer returns within four weeks; NCs open for more than 30 days.
