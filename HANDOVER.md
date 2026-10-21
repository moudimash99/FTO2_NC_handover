# FTO2 NC analysis — full handover

Written 12 Oct 2026 for the agent taking over this work; updated 19 Oct 2026 (CNQ model, work orders, MES aléas, 2025 NCs: see `CNQ_CHANGES.md`). Owner: Mohammad Machaka (intern, Quality, Airbus Operations electrical centre FTO2 / OLME, Toulouse). Manager: Emmanuelle.

Read sections 1, 2 and 9 first. Everything else is reference. Every number below was computed on the files in this bundle; scripts to reproduce the recent ones are in `07_scripts/`.

---

## 1. How to work with Mohammad

- **Talk before doing.** He asked explicitly: "try to not do a lot of stuff and only talk to me before doing stuff… you can do your analysis before answering." Do the analysis, answer, then ask before building anything big.
- **Direct, data-grounded, honest.** He pushes back when assumptions are wrong and prefers being told when something is weak.
- **Language:** talk to him in English. Deliverables for internal presentation are wanted in **French and English** (toggle) and must look professional (no "thinking" shown on slides, one label per item, no debug elements).
- **You cannot touch the pipeline or Slate.** "U can't work on the pipeline or Slate. U gotta give them the info and work is done there." Deliverables for Skywise are packs + instructions he installs himself.
- **Data constraint:** NC texts must not be sent to an outside AI API (e.g. Gemini) without checking with Emmanuelle / IT. Any LLM labelling so far was done inside the Claude session only, as a one-off check.
- **Current pressure (Oct 2026):** he is "under fire" over cable problems and is preparing an internal defence of how cable NCs are categorised (section 6).

---

## 2. State of play (12 Oct 2026)

| Workstream | Status | Where |
| --- | --- | --- |
| Defect parser | v4.8, frozen, validated | `01_parser/nc_defect_parser.py` |
| Pareto taxonomy (9 categories, RCA names) | Approved by Mohammad 7 Oct | section 4, `04_reference/sous_categories.csv` |
| Skywise dashboard pack v4.8 | Delivered, **install not confirmed**; MT → A400M and customer-return scope fixed 12 Oct; A400M chart still to drop | `02_dashboard_pack/`, handover doc (section 10) |
| Real pipeline notebook | Running in Skywise today, uses an older parser; read-only context | `06_input_data/pipeline_notebook.py`, section 5 |
| **One build for everything** | Done 12 Oct: `python3 build/build_all.py` rebuilds every table, page, workbook and the CNQ package from the raw exports | `build/`, section 2b |
| NC dashboard for presentation, six tabs: Pareto · cost Pareto · weekly Pareto · CNQ (series) · customer returns · root causes (RCA); FR/EN, root-cause classification | Done 12 Oct | `03_reports/FTO2_NC_Dashboard.html`, https://claude.ai/artifact/988FNWFkPFRB1aPiBU2Tg1 |
| CNQ model (Mohammad's `cnq_handoever/`) | Refreshed on the same data: 181,405 EUR level 3, 856 NCs; cables 23.6 % | `cnq_handoever/README_handover.md` section 13 |
| Cable defects analysis | Findings done, **decision pending** (options A–D) | section 6, Docs "FTO2 Cable Defects – Findings" |
| REC tagging | Rule + regex proposed, **definition decision and precision check pending** | section 7, Docs "REC NC Tagging – Findings" |
| Full defect table | Done, rebuilt 12 Oct with both classifications and CNQ | `05_outputs/FTO2_defects_detail.xlsx` |
| LLM re-labelling with full long text + root-cause rule (Sonnet, in-session) | Done 12 Oct; it is the main classification since 12 Oct; 330 disagreements with the parser (FTO2 + customer returns) **awaiting Mohammad's verdicts** | labels `04_reference/llm_labels_longtext.csv`, review `05_outputs/FTO2_llm_longtext_review.xlsx`, method `07_scripts/llm_longtext/` |
| H1 2026 deep dive, writing standard, entry-tool spec | Done (Aug–Sep), not deployed | section 8, `03_reports/` |
| CNQ reconciliation (predecessor files vs official method M1888 / UG2600252) | Mentioned by Mohammad, **not started here** | — |
| CNQ model | Version cnq-2026.10.20b: 7 rule changes from SAP rework orders and MES aléas, approved 19 Oct; 20 Oct: the planned time of the NC's closed rework order replaces the model's work, the declared aléa time replaces the flat alert, and each step is priced at the rate of who does it (production 123 EUR/h: alert, setup, hands-on, aléa time; quality 107 EUR/h: writing, re-check; ME 76 EUR/h: technical support; engineering stays at the Airbus 78.16 EUR/h). AEC level 3: 178,847 -> 376,511 EUR |
| Dashboard, 20 Oct round | Tab "Où" renamed **Localisation** (EN "Location") with an NC table (search, newest first); category "MEO Câblage" renamed **MEO Facteur humain** everywhere (pipeline, references, page); the cable-defect tile and chart removed from the Coût tab (Mohammad, 20 Oct: no longer needed; "NC câbles" in the type split = NCs of the Câbles type). **Click to filter**: a bar, point, cell or table value (month, week, day, line, product, MSN, station, NC type, category, root cause, FIN, NC) filters every tab; a chip in the filter bar shows it, ✕ or a second click removes it. The 2025 comparison follows month and product picks and hides for the others; the aléa block follows month, week, day and station | `build/templates/dashboard.html` (`pk`, `pickSet`, `renderWhereTbl`) |
| Dashboard, 20 Oct second round | ⓘ "Comment la sélection est faite" under the filters: every filter in order, how many NCs it removes and how many are left; the plant switch split into customer returns and NCs raised at other plants (with the plants, and how many come from the missing-ID lists); NCs at 0 € because FTO2 is not liable. NCs by programme (pie) moved up beside the lead time; cumulative cost on its own row. Pareto: no cable tile or cable list; the cable shading is a button, off by default; FIN top 10. Cost tab: every NC over time folded. Top 3 causes of each product moved to Localisation, Products. **Waiting for Mohammad:** objective per MSN with the A320/A350 mix, NCs of the missing-ID lists raised at other plants, Pareto layout, 2025 vs 2026 causes, names of the RCA tab and a Production tab | `build/templates/dashboard.html` (`renderInfo`, `cabOn`) | `cnq_handoever/`, `CNQ_CHANGES.md` |
| 2025 baseline and targets (20 Oct) | 2025 NCs through the pipeline's rules: 2025 bar, target = 2025 − 25 %, budget = 2025 cost − 25 %, per-line target from the 2025 deliveries | `06_input_data/nc_2025_skywise_fto2.csv.gz`, `Livraisons_MSN_2025*.csv` |
| Work orders, MES aléas, 2025 NCs (uploaded 19 Oct) | Analysed; investigation checklist for Mohammad, **checks pending** | `05_outputs/CNQ_investigation_checklist.html`, `07_scripts/wo_disruption/` |

---

## 2b. How everything is built (12 Oct)

`python3 build/build_all.py` is the only way outputs are made. It reads the Skywise exports in `06_input_data/fto2_dashboard_data*.csv`
(all files merged; when an NC is in several, the most recently changed row wins) and the root-cause labels in
`04_reference/llm_labels_longtext.csv`, then: parser v4.8 → scope (customer return only with FTO2 in `liability`) → labels
(a line whose text changed or that is new is marked `a_labelliser` and falls back to the parser label) → CNQ model for both
classifications → `05_outputs/`, `03_reports/` pages, `cnq_handoever/` sample outputs, expected totals and its own page, then
the CNQ package's two checks. `build/build_report.json` records the counts. The root-cause labels are the main classification;
the parser v4.8 labels are kept next to them (they are what the Skywise pack produces). To refresh with a new export: drop the
file in `06_input_data/`, run the script, label any `a_labelliser` lines (method in `07_scripts/llm_longtext/`), run again.

Reporting scope, the same on every page (column `scope` in `fto2_nc.csv` / `fto2_defects.csv`): **Série** = raised at FTO2,
FTO2 in `liability`, not deleted (727 NCs, 2,709 defects, 63 NCs without a defect line, all A400M with redacted text);
**Retours clients** = raised elsewhere with FTO2 in `liability` (69 NCs, 69 defects). CNQ: Série 166,428 EUR + Retours 11,877 EUR;
the model total 181,405 EUR also counts 59 deleted NCs (2,975 EUR) and 1 supplier NC (125 EUR), shown aside on the CNQ tab.
On the pages, the scope "Série" is called **FTO2** so it does not clash with the production type "Série".
**Filter bar** (top of both pages, applies to every tab): data source (all / Skywise only = `Ext_Source` "Not in external lists" /
manual lists = GPS or Test / GPS / Test), FTO2 plant only (yes = FTO2 scope; no = FTO2 + customer returns; no effect on the
customer-returns and RCA tabs, which show both apart), production type (all / Série / REC / FTI = `phase`), aircraft (line),
period (year to date, last 1/3/6/12 months, all dates, or two typed dates; presets end on the last NC of the extract; hidden on
the follow-up page, which has its own week picker), minor defects. Defaults: all data, FTO2 yes, Série, all aircraft, year to
date (722 NCs, 2,704 defects on the 28 Sep extract). NC row field [39] carries the data source.
**Look:** every tab uses the Analyses design (Newsreader titles, figures as an editorial row, each breakdown a full-width
band with its name on the left and the chart on the right; the active filters stay under the tabs).
**Galerie (fictif)** tab, local page only (never in the Slate files): 50 chart ideas drawn on **fictitious data** from
`build/dummy_data.py` (seed 7, saved to `05_outputs/dummy/*.csv` with a README). Only the category / RCA / sub-category names
are real; the cause → 5M table in it is a proposal to agree with the team. Each chart says whether the real data can feed it
now (35), partly (8: budget, close dates of actions, list of aircraft built, close-time targets, 5M mapping, last year's NCs,
output per shift) or needs data to collect (7: production volumes, insertions per product, units per station, targets,
station layout, MES rework time, supplier deliveries).
"Garder" marks the ones to build (kept in the viewer's browser only). Remove the tab by dropping `dummy=` in `build_dashboard`.
**Taux de NC** tab, local page only: 30 quality charts (51–80): NCs, defects and cost per unit of volume built. The volume is
only a denominator (the quality team asked for no production charts as such). Input `06_input_data/EqMSN_2026.xlsx`
(EqMSN per product and month, Standard and Adjusted sheets, export Avances/Retards of 07/10/2026; October–December are forecast).
NC product family → EqMSN product in `04_reference/eqmsn_produits.csv`: ~90% of NCs match; 742VU, 743VU, 1211VB and "Other" have
no production row; **MIP A400M ↔ MIP(2) is an assumption to confirm**. Real data follows the filter bar; a switch shows the same
charts on fictitious data (`dummy_eqmsn.csv`). A400M NCs have no defect lines, so their defect-based rates read zero.
**Review page** `03_reports/FTO2_Revue_Proposition.html` (19 Oct, https://claude.ai/artifact/PGsQFUP7YUeBhdexeeWJws): the proposed final layout (37 items in 5 question tabs + proposed removals + low-graded current charts), each drawn with its real chart card, with keep yes/no, priority a–e, now/later, version for the 3 open choices and a note. Choices are saved in the page's store (collection `choix`, one document per item), else in the browser; "Copier le récapitulatif" gives them as text. Built from the same template (`page="review"`), never in Slate.
**Dashboard v2, layout A (19 Oct, from Mohammad's walk-through of the mock-up)**: tabs Vue d'ensemble · Pareto · Où · Coût de non-qualité · Retours clients · Causes (RCA); the Analyses, gallery and rate-exploration tabs left the main page (their charts were spread over the tabs; the gallery stays on the review pages). Overview: NC · défauts · défauts par NC · coût · NC par MSN; target per line; NC trend with 2025 and the year-end forecast; NC par programme; cumulative cost against budget; time to close; volume-then-per-MSN scorecard; control chart (XmR, real weekly NCs); the other NC lists and the calendar in a fold-out. Pareto opens on cost; bubble and flow on top. Où: NC/défauts/coût per MSN by product in one chart, monthly rate, 95 % intervals, forecast by product, FINs that come back (parser FIN), cost per aircraft and product family, stations, fleet icons (fold-out). Coût: line in view, cost components by month, every NC as a bubble, other lists folded. **Placeholders until real figures exist, marked on the page:** 2025 = this year's forecast, target = 2025 − 25 %, budget = forecast − 25 % (`V2CUT` in the template). Forecast = the period's value per planned MSN × MSN planned per month (production file). 'Per 10 EqMSN' is now 'per MSN' everywhere; the production file now goes to every page, Slate included.

**Skywise migration (20 Oct), `03_reports/skywise/` (guide: its README.md):** four levels to try in order: (1) fictitious data written in the JS, visual check; (2) fictitious data made by two Slate queries (`q_fto2_nc`, `q_fto2_def`, no dataset needed) read through the code sandbox's state `{"nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}"}`; (3) real data: the Skywise notebook writes the datasets `fto2_dash_nc` and `fto2_dash_defects` (now in one run with the pipeline, `fto2_pipeline_notebook`, see above), which Slate reads with the level-3 queries; (4) a ready-made Slate app JSON to import (built on the structure of the v106 export, not testable here). The data steps moved from `build_all.py` to `build/fto2_core.py` (unchanged, outputs byte-identical), so the notebook runs the same code as the laptop; the NC selection stays the pipeline's. The page rebuilds its data from the two tables with `fto2FromTables` (the local dashboard is built the same way). Fictitious data: `build/dummy_tables.py` (Postgres SQL; run on a local Postgres it gives the level-1 data). New defect lines get the parser's label until the periodic AI pass (`fto2_lines_to_label.csv` out, rows appended to the `fto2_ai_labels` dataset).

**One forecast and the GPS / Test rule (20 Oct, latest):** every forecast to December is now made the same way (overview cumulative NCs and cost, products chart): product by product, each product's value per MSN built x its MSN planned, plus the NCs out of the production plan at their own monthly pace. Before, the overview used one overall pace x all planned MSN (1,342 NCs) and the products chart left the out-of-plan NCs unforecast (1,244); now both say 1,293 NCs and 496 kEUR. The overall pace over-forecast because A320's planned volume grows at the end of the year while A320 has few NCs per unit. Mohammad: an NC of the GPS register or the Test list is FTO2's only when its plant is FTO2 (plant decides, the list does not). Footnote 2 rewritten (it still described the 12 Oct scope).

**Chart check and the 20 Oct rework (latest):** checked every chart's totals against the two tables (910 NCs, 2,890 defects, 347,064 EUR on the default view): trend, cost, decision, type, line, flow and components reconcile. Fixed: Cost tab squeezed to 3/4 width by an area missing from its grid, and an empty slot (now cost by product, top 10); products chart (Localisation) left out the 134 NCs whose product is not in the production plan, now an "out of plan" row and a total that match the headline; weekly control chart leaves the running (partial) week out and now says so; flow chart labels were cut and its end nodes did not filter; open-time chart legend now filters by decision group and on "still open"; the hundred-squares chart counted the separately tracked group twice. **Targets line by line (Mohammad):** each line's target = its 2025 rate per product delivered - 25 %, x its 2026 volume month by month; all lines = the sum (776 NCs Jan-Sep against 509, +52 %; the pooled rate said +3 % because A320's small parts weigh in the volume); NCs out of the plan: 2025 - 25 %; budget the same with the cost; 2025 and the target as stacked bars by line left of the cumulative charts; one colour per line everywhere (purple, orange, raspberry, brown since the last round, see below). **Pareto:** category Pareto, then volume / unit cost + monthly ranking, the flow (full width), causes vs volume + causes 2025 vs 2026 (2025 by the parser, 2026 by the labels, Mohammad's choice; they agree on 95 % of categories), connection errors with the 2025 average, then the lists (cause | line | FIN, the hundred squares under Line), sub-code; cable per MSN folded. **Tabs:** Causes (RCA) renamed Definitions; new last tab Production: per line and per product, MSN built / planned / delivered 2025, NCs, rates and targets, the monthly plan by line, then how the volumes are made and used. 2025 defects by cause are in the 2025 block of the page (`y25.rca`, built on the laptop).

**Plant switch and customer returns from the pipeline's own columns (20 Oct, latest; Mohammad):** the parser pack's `perimetre` label is no longer used anywhere in the dashboard, the notebook outputs or the cost model (the old v4.8 pack keeps it for its own queries). `fto2_dash_nc` loses the `plant_scope` column. **FTO2 plant only** (on by default) = the `plant` column is FTO2 or FT02 (both spellings, as in the pipeline's `Type_NC_auto`), nothing else checked. **Customer return** (`customer_return`, `scope` = client) = `Type_NC_auto` "NC Retour client" with FTO2 in `liability`: the same 69 NCs as before on the laptop data; used by the customer-returns tab and the cost model. No tab removes customer returns except through the plant switch (their plant is not FTO2). `scope`: serie = plant FTO2/FT02, client = customer return, autre = the rest. Laptop: 1,127 NCs = 988 plant FTO2 + 69 customer returns + 70 other plants (all from the missing-ID lists, FTO2 not liable); default view 910; cost unchanged. Why it mattered: a dataset made by the notebook before 20 Oct had `scope` = serie only for FTO2-liable, not deleted, not supplier NCs, so the switch dropped about 30 % of the FTO2 NCs (Mohammad's 1,099 → 786).

**Totals, colours and clicks (20 Oct, final round; Mohammad):** **Localisation 930 vs Overview 994:** the production plan (EqMSN export of 7 Oct) gives October to December as forecast, so the per-MSN data dropped every NC raised in October: Localisation, the Production tab and the line targets counted fewer NCs than the Overview. Now the month of the last NC counts as built for the share of its days gone (its planned volume × days gone ÷ days in the month); the rest of that month goes to the forecast with the months after. Every total equals the Overview (tested with the NCs moved 16 days later: 910 everywhere; forecast 1,209 NCs and 463 kEUR on both the Overview and Localisation). The out-of-plan count and the forecasts use one test (`v2InPlan`), so the rows always add up. **Colours:** blue = MEO Facteur humain (workmanship), green = Erreur Branchement (connection), as in the hundred squares: category Pareto, cause and sub-code lists (the colour of their category), FIN and line lists cut by category, bubbles, the cause followed in the monthly ranking, causes 2025 vs 2026 (direction shown by arrows). Lines have colours with no blue or green (A350 purple, A330 orange, A320 raspberry, A400M brown, `--l1`..`--l4`, checked for colour-blind separation in light and dark; a first try in slate greys looked dull), products take their line's colour, cost components are shades of the dashboard's green: blue and green mean only the two categories. Under 900 px wide the Pareto lists, the Localisation chapters and the Overview now fall back to one column (the cards were stacked on one another). **Pareto:** the lists (cause | line with the hundred squares | FIN, then sub-codes) come right after the category Pareto, before the charts; in the narrow lists the bar runs under the name and the figures (it had no room left, none at all in cost mode); same fix for the Coût tab's product and decision lists. **Connection errors per MSN** (monthly, by product, and the 2025 average): A330 and A350 only, A320's small parts counted one by one pull the rate down; with A320 in the filter bar the two charts say so. **Overview:** the NCs-by-programme ring now sets the "Avion" filter (before, it filtered only the folded lists and the figures, not the charts); the figures at the top always show the global selection. **Clicks:** a cell of the station x category map filters that station and that category (`stcat`), the row name the station, the column head the category; in the FIN chart the whole row filters the FIN, a square that FIN on that aircraft (`finmsn`). **Chart 64** is now "Fiabilité du taux" with a plain explanation, the MSN count of each product and a legend. **Explain the calculation:** the special rules open on a click; the selection's cost is written as an addition (six steps + engineering + material = total). **Disruptions:** in the Coût tab ("Aléas qualité sans NC"); in Slate they need the `q_fto2_dis` query and the `fto2_dash_disruptions` dataset.

**Causes 2025 vs 2026, A330 and A350 only (21 Oct, Mohammad):** like the connection errors, the 2025 rate per product delivered and the 2026 rate per MSN built count only A330 and A350 products (A320's small parts counted one by one, and A400M, left out). On the repo data Inversion goes 3.69 → 4.19 per MSN (it read 1.51 → 1.09 with every line in). With A320 or A400M in the filter bar the chart says it covers A330 and A350 only.

**Swapped pins (21 Oct, Mohammad; from the vision prototype on `claude/vision-wow`):** Pareto tab, in the closed "Autres graphiques" section beside the cable chart (kept out of sight until checked on the real Skywise data, Mohammad's choice before a presentation; to show it, move `VK` from `V2L.pareto.fold` to `V2L.pareto.top`): "Quelles broches sont inversées". The two pins of a swapped-wire defect are read from its text in the page (`pinPair`, a port of `09_vision/pins.py`: "... ENTRE LES BORNES 41 ET 42", pins of 1 to 3 characters only), so no dataset change. Per connector (FIN), the six with the most aircraft: one arc per swapped pair, thickness = aircraft; figures: swaps with both pins written (390 of 480 on the repo data), share between neighbouring pins (44 %), pairs on more than one aircraft (34). A connector's name or arc filters that FIN. No 2025 comparison: the 2025 defect texts are not in the page's data.

**Open-time filter (21 Oct, Mohammad):** a click on the open-time chart (Overview) at day N keeps, on every tab, the NCs still open N days after their creation: closed after more than N days, or still open and older than N days (pick `age`, `ncAgeOver`; days to a tenth, as the chart). The hover says how many NCs the click keeps; a dashed line marks the day; a second click or ✕ removes it. The 2025 comparisons hide under this filter (2025 has no closing dates here).

**Every NC counts (20 Oct, last):** the reporting scope of 12 Oct is gone (Mohammad: the pipeline's selection is the one). Deleted, supplier-liable and not-liable NCs count like the others, with no filter for them; `scope` now only says where the NC was raised (serie = at FTO2, client = customer return, autre = other plant) for the plant switch and the customer-returns tab. FTO2's cost only where FTO2 is liable: the others cost 0 (footnote: 271 NCs, 37,617 € of handling on the laptop data). Laptop default view: 910 NCs (was 722); every filter open: 1,127, the whole table. 2025 follows the same rule: 1,000 série NCs, 174,529 € (target 750).

**One-step pipeline notebook (20 Oct, latest):** `03_reports/skywise/level3_datasets/fto2_pipeline_notebook.ipynb` replaces the pipeline notebook, the second RUN_MODE run and the missing-ID generator. It is generated by the build from `06_input_data/pipeline_notebook.py` (selection code unchanged): one run fetches the standard selection, computes the missing IDs from the GPS / Test lists (2026 dates, as `missing_id_generator` did) and fetches them by number, then writes the three dashboard tables (and the four former outputs while `KEEP_OLD_OUTPUTS`). The 1,000-row cap is gone (`ROW_CAP = None`, decided by Mohammad): it had dropped 1-19 January (11 NCs lost, 46 recovered only through the lists). Tested on a stand-in Skywise: identical tables on the 1,126 common NCs, +11 January NCs. Fixed on the way: empty text from the pipeline (`''`) now counts as missing (it was taken for a GPS NC type).

**Origin, aléas and the disruption block (20 Oct, later):** each NC carries `origin` (normal = `fto2_dashboard_data`, missing_ids = `fto2_dashboard_data_missing_ids`; the two stay separate datasets) and the filter bar has "Origine (pipeline)". The alert step uses the declared time of the quality aléa that led to the NC (same work order, NC from 2 h before to 72 h after; `cnq/cnq_disruptions.py`): 175 NCs, AEC level 3 177,436 → 178,847 EUR. The Coût tab shows the disruption block beside the cost (quality aléas with no NC: 89, 66.9 h, 3,347 €; 19 possible ERMA aléas left out), from a third table `fto2_dash_disruptions` and a third Slate query `q_fto2_dis` (optional). Inputs: `06_input_data/mes_disruptions_fto2_2026.csv.gz` (2,500 rows, check H7). In Skywise the cell reads Work_Order_Operation and MES Disruptions (aliases `work_order_operation`, `mes_disruptions`). Three January aléas on HARNAIS_MDCD (17 h, "recherche de gamme", training) look like definition problems rather than quality: to check (checklist D).

**2025 and the rework orders (20 Oct):** the overview's placeholders are gone. 2025 = the raw 2025 Skywise extract (from main's upload) run through the pipeline notebook's own rules, copied in `build/fto2_core.py` (`pipeline_rules`: ERMA out, deleted NCs of other plants out, Programme/Type/Produit auto), then the parser and the CNQ model; the port gives main's own figure on main's cut (818 NCs, 178,870 EUR). Dashboard scope (série, raised at FTO2): 732 NCs, 2,931 defect lines, 170,433 EUR. The trend shows the 2025 bar and 2025 at the same date month by month; target 549 NCs (2025 − 25 %); budget 128 k€ (2025 cost − 25 %). Per-line target: 2025 NCs per product delivered (Livraisons 2025 sheet, photo from Mohammad, 343 products / 140 whole MSNs) − 25 %. The 2025 extract has no customer returns, and 2025 is not split by manual list: with the data-source filter on, the placeholders come back, marked. Rework orders: `cnq/cnq_orders.py` reads the S03 operations (`06_input_data/wo_s03_operations_fto2_sep2026.csv.gz`, September 2026 only); an NC whose orders are all closed and planned gets their planned time for setup and hands-on (71 NCs; AEC level 3 175,663 → 177,436 EUR). Three new NC columns: `work_source`, `order_state`, `rework_orders`; the explainer shows the order. In Skywise the notebook reads the work-order operations dataset once its name is set (`WO_OPERATIONS`).

**Merge of main (19 Oct):** the branch now carries main's CNQ model `cnq-2026.10.19` (alert 41 min and only when an operator raises it, connection errors 35 then 15 min, internal NCs x 2, exchange without work, rejection with a rework order) and the CNQ investigation checklist. The build now passes `linked_document` and `work_order` to the model (needed for the rejection-with-rework-order rule: 55 série NCs). On the current exports: AEC level 3 175,663 EUR (was 181,405), level 2 143,298, level 1 403,489. The dashboard's "explain the calculation" follows the new rules (verified line by line on 741 NCs).

**Overview, 19 Oct (later)**: the NC trend is cumulative: a 2025 bar on the left (same scale), the year's curve with the forecast to December (dotted), the year-end target spread month by month (dashed), and each month's dot red when that month was above its share of the target, green when below. July and August count as 0.6 of a month in that share (`V2W` in the template; could later follow the MSN production plan instead). The control chart lost its moving-range panel and now leaves shutdown weeks (fewer than 10 série defects, same rule as the weekly tab) out of the mean and limits. Time-to-close medians moved into the legend. `FTO2_Mises_en_page.html` (local, `page="layouts"`) is the same dashboard with a bar to switch the Overview between the current layout and five others (Grille, Héros, Liste, Colonne, Magazine), so Mohammad could pick one. He chose **5 · Magazine**, which is now the main page's Overview (`data-lay="5"` set in `v2Build`). Phone layout is not a requirement. **Pareto** went back to the shape of the 13 Oct Slate file Mohammad pointed to: cards in a grid (Catégorie and Sous-code across; Cause, Défaut câble + Ligne stacked, and FIN three across), no charts between the lists; the other cause charts (bubble, flow, top causes per product, ranking, waffle, quarters…) sit in one fold-out under the lists. Board option `mag: true` keeps only the `wide` dims across. **Où** is half magazine: cards, full width where the chart needs room, in pairs otherwise (interval + projection, product family + stations). **Coût de non-qualité** is Magazine too: cost components by month (two thirds) beside the Ligne and costing-methods cards, every NC as a bubble across, then the folds (explain the calculation, other breakdowns, table). **Où** uses **Chapitres** (chosen from five layouts on a temporary layouts page, now removed): 01 Produits, 02 Avions, 03 Postes, the chapter title sticky on the left. Its top chart opens on NC, défauts and coût done so far + forecast to December by product (forecast = the period's value per MSN × MSN planned to December); a switch shows the per-MSN view instead. **Coût de non-qualité**: costing methods top-left, beside one 100 % bar of the cost by NC type (field `type_nc`: Câbles, Contrôle final, Test, Interne = INTERNE + NC Interne + Casse interne, Fournisseurs, Autres = the rest); clicking a part filters the tab. Ligne, Défaut câble and Décision below, then cost components by month beside the month columns, then every NC; nothing is folded any more except the explanation and the table.
**Scored mock-up** `03_reports/FTO2_Maquette_Notee.html` (19 Oct, https://claude.ai/artifact/FTHoQ45EoHVYBvtmwuoRnE): layout A on real data (Overview · Pareto · Where · Cost · Customer returns · RCA · weekly Pareto · MFT actions). Every chart has an a–e score at its side; no score = out; "Aperçu final" keeps only scored charts in score order. Overview top: target band (NC per EqMSN against 2025 × 0.75; the 2025 rate is typed in, it is not in the data) and NC / defects / cost per EqMSN side by side instead of a switch. Scores: page store, collection `note`; seeds = review-page grades.
CNQ tab, **Expliquer le calcul** (folded by default, 19 Oct, after the earlier CNQ page `cnq_handoever/dashboard/cnq_dashboard.html`): the six steps with minutes, cost per NC and total over the selection, engineering and material, what each decision charges; then any NC of the selection worked out step by step (example buttons pick the latest NC of each kind) with its defect lines. Figures come from the model (`cnq_min_*` per NC, row [40]; parameters `cnqp` from `cnq_params.py`), nothing is recomputed by hand.
The dashboard is meant to be presented: Vue d'ensemble (headline figures and NC charts), Pareto (volume or cost toggle), Analyses, Coût de non-qualité, customer returns, root causes. The weekly Pareto and the MFT actions are a separate page from the same template (03_reports/FTO2_Suivi_Hebdo.html, Slate file FTO2_Suivi_Hebdo_Slate.html), one classification (root cause), no working notes on the page; the parser labels stay in the files. The separate customer-returns page is retired (`03_reports/archive/`). The RCA tab explains the hierarchy
(123 official sub-codes → 42 sub-categories → 25 RCA → 9 categories); definitions are in `04_reference/rca_definitions.csv`
(FR/EN, written 12 Oct from the code sheet, **to be checked by Mohammad**).
The Analyses tab has 12 charts: six on defects (calendar, flow, volume × unit cost, concentration, line mix, monthly ranking)
and six on NC fields (cost per MSN with customer returns, product family, lead time, hour of creation, station × category,
MFT actions). The MFT actions come from `06_input_data/MFT_actions_A330.csv` / `_A350.csv`; the link from each action to the
problem it targets is in `04_reference/mft_actions_mapping.csv`, **a proposal to confirm with line quality**.
Customer-return costs there are model estimates (no invoices).

---

## 3. The parser (`nc_defect_parser.py`)

Pure-stdlib Python (regex + unicodedata), so `parse_nc()` can become a PySpark UDF. pandas only for `explode_dataframe()`.

**What it does:** splits each NC long text (`description_long_text`) into individual defects, counts them, classifies each to an official sub-code → Pareto sub-category → Pareto category → RCA, and extracts FIN, quantity, cable flags, minor flag.

**Founding finding:** one NC often holds a list of defects ("bundles": test lists `DEF 1-T04 : …`, final-control lists `Def1 :`, MIP lists `1 - FIN xxx :`). Counting NCs hides ~3× the defect volume. Count calibration vs the manual `Ext_Nb_Defauts`: 95% exact, 99% within ±1 (n=314).

**Formats decoded:** `def_list`, `numbered_list`, `narrative`, `dash_list`, `cable_list`, `fal_single` (+ DEF variants). Typos in codes (TO4, QQ01) are rescued; a bad code never drops the defect from the count. Redacted texts ("Removed for classification reason", all A400M / programme MT) give `nb_defauts=None`.

**Version history**

| Version | Date | Change | Validation |
| --- | --- | --- | --- |
| v1–v3 | Aug–Sep | Splitting, counting, 6 families / 26 reporting types from official codes | 2,346 defects from 807 NCs (H1); AUTRE 16% → 8% |
| v4 | 4 Sep | One target = official sub-code (123) → type (26) → mode (6) | `03_reports/classification_v4_definitive.md` |
| v4.1 | Sep | Cable provenance (RECU / LIGNE / NON_PRECISE), spec boilerplate stripped | Agreement with cable team tracker 53% → 81% (text) → 92% (+ tracker) |
| v4.2 | Sep | `defaut_cable` flag ("a cable must be remade/resupplied"), `nc_cable` | Keeps 178/183 tracker NCs; 31/32 extra flags are real |
| v4.3 | Sep | `categorie` (18 "what to fix" categories) | wiring errors 770 → 744 |
| v4.4 | Sep | `famille` (8 + Autres) | — |
| v4.5 | Oct | `groupe` / `sous_groupe` ("the way the line talks") | — |
| v4.6 | Oct | Every official sub-code in exactly one sub-category + RCA; exceptions E1–E4 | — |
| v4.7 | Oct | Fixes from an independent LLM labelling of every defect; no more "Non classé" (`DEVINE` guess); `mineur` flag | LLM vs parser: same sub-category 89%, same category 95% (2,740 defects) |
| v4.8 | 7 Oct | 9 Pareto categories; Mesure hors tolérance → Grounding/Bonding; `split_plus` ("A + B" = two defects); loose plate held by frettes = Frettage | 58/58 Slate query checks passed |

Exceptions to "one sub-code → one sub-category": **E1** cable cut too short on the line = "Câble à refaire (ligne)" (part of Q06-001); **E2** Q11 component split into broken / HS / cause not written; **E3** cable received damaged → Amont · Câble; **E4** cable never supplied → Amont · Câble (E3/E4 only when no code is written). A written code always wins; otherwise text; a cause in the text wins over its consequence.

**Run it locally**

```python
import fto2_logic as L                       # 02_dashboard_pack/1_pipeline
defects = L.build_defects(sap_df)            # sap_df = Skywise NC export (columns as in SAP_COLUMNS)
ncs = L.build_nc(sap_df, defects)
```

or the older entry point the real notebook uses: `explode_dataframe(df, text_col="description_long_text", id_col="notification_number", manual_count_col="Ext_Nb_Defauts")`.

---

## 4. Pareto taxonomy v4.8 (approved)

**9 categories:** MEO Câblage · Erreur Branchement · Élément Manquant · Élément Endommagé · Déverrouillage · Grounding/Bonding · Kitting Factory · FOD · Autre. Kitting Factory, FOD and Autre are shown aside, in grey.

**Charts asked for:** (1) Pareto by category ("Pareto Global" → Emmanuelle); (2) "Pareto Défaut Top 5 par ligne": top 5 RCA per line (A350, A330, A320; A400M dropped), **Déverrouillage always shown** (optional 3rd chart); (3) top RCA per category. Customer returns (`Retour client`) as separate charts beside. Toggle to hide minor defects.

**Minor (`mineur`)** — "really minor, like forgetting a cap": missing tyrap / frette / ficelle, missing cap / cerise / plug. Nothing else.

**Scope (`perimetre`):** FTO2 · Retour client (raised outside FTO2, FTO2 liable) · Fournisseur · Supprimée (deleted) · Autre. Pareto counts FTO2 only.

**RCA names (as renamed by the team):** Inversion · Mauvaise Borne · Déverrouillage · Non Connecté · Frettage Incorrect · Serrage Incorrect · Mauvais Cheminement · MEO Gainage · Finition Inachevée · Défaut de Sertissage sur câble standard / spécifique · Défaut de Métallisation (incl. Mesure hors tolérance) · Erreur Fixation ou Protection · Erreur Composant Électrique · Fixation ou Protection Manquante · Obturateur Manquant · Câble ou Élément Manquant · Identification Manquante · Câble Endommagé · Composant Endommagé · Protection Endommagée · Structure Endommagée · Défaut d'Impression · FOD · Erreur Dossier. "Autre/Indéterminé" removed. English RCA translations in the dashboard are mine and **still need Mohammad's check**.

Full sub-category → category → RCA → official sub-codes: `04_reference/sous_categories.csv` and `reference_souscodes_pareto.csv`. Official code sheet: `official_codes.csv` (123 sub-codes with AMDEC severity/occurrence/detectability).

Decisions on examples (7 Oct): "S/N illisible" → Défaut d'Impression; "plaquette desserrée, reprendre le frettage" → Frettage; "gaine non maintenue + plaquette à l'envers" → split into two defects.

---

## 5. Pipelines: the real one vs the pack

### 5a. The real Skywise notebook (running today; context only, don't edit)

File: `06_input_data/pipeline_notebook.py` (sent as `pipeline.ipynb`, actually plain Python).

- **Fetch:** `non_conformity` where plant = FTO2 and created ≥ 2026-01-01, plus other plants where `FTO2` is in the `liability` array. Excludes `user_department` containing ERMA, and deleted NCs outside FTO2.
- **Station names:** joined from `data/fto2_station_mapping.csv`.
- **`Programme_auto`:** SERIE by default; **REC** if `workflow_list` matches `\bREC\b|-CRE|-PNC|A30-REJ-PVU2`; **FTI** if `constituent_assembly` starts with WY or WA.
- **`Origin_auto`:** Test if `user_department` = OLMEP14/AIRBUS OPERATIONS SAS, else Qualité.
- **`Type_NC_auto`** (priority order): deleted FTO2 → QUALITE; Test; plant ≠ FTO2 → NC Retour client; `[SUPPLIER]` or `responsible_defect_level1` = Y4 → NC Fournisseur; cable workflows → CABLES; REJ-LO-BP or REW-LIGNE+Derichebourg → NC Interne; LIGNE-F-DQN → DEMANDE DE DQN; REW-LIGNE / TEST → CONTROLE FINAL.
- **`Produit_auto`:** regex on article description + station description (E-RUDDER, MDCD, OHP, 300VU, MFRL, PTVU, MIP A400M/A350, else the nnnVU/VB found).
- **`.head(1000)`** on newest creation date → the export is capped at 1,000 NCs (this is why early January is cut).
- Joins Test list (`data/NC TEST - NC.csv`) and GPS register (`data/GPS NC INT_SERIE ELEC 2026 - NC REGISTRE.csv`) → `Ext_*`, `GPS_*` columns.
- Writes `fto2_dashboard_data` and `fto2_parsed_defects` (or `_missing_ids` in MISSING_IDS mode).
- **Scope bug found 12 Oct:** `cond_retour_client` = plant ≠ FTO2 only, and MISSING_IDS mode fetches by number with no liability filter. NCs where FTO2 is not liable (e.g. 25 Saint-Nazaire "DAMAGES", liability VCS…, responsible Y6) were counted as customer returns (90 NCs instead of 65). Fixed in the pack (`_perimetre` now requires FTO2 in `liability`, else "Hors périmètre"); the notebook still needs the same check (pipeline team).
- **Bug to mention to Mohammad when relevant:** in STANDARD mode it writes `fto2_dashboard_data` twice; the second write (`final_df`) overwrites the enriched NC table from `explode_dataframe`.

### 5b. The v4.8 install pack (`02_dashboard_pack/`)

- `1_pipeline/fto2_logic.py`: plain pandas; EDIT block at top holds dataset paths, `SAP_COLUMNS`, `OUR_PLANT`, `PERIOD_START/END`, `LINES`, `RCA_NAMES`. `fto2_transforms.py` wires it into a Code Repository; `code_workbook_fallback.py` for a Code Workbook.
- Outputs `fto2_defects` (one row per defect) and `fto2_nc` (one row per NC, counts per category).
- `2_slate_queries/q01…q08`: Slate SQL on the Postgres syncs `foundry_sync.fto2_defects` / `foundry_sync.fto2_nc`, widgets `w_mineurs`, `w_groupe`.
- `3_check/valeurs_attendues.csv`: expected values on the SAP extract 5 Jan – 6 Jul 2026 (install check).
- Step-by-step install: Docs "Skywise NC Dashboard Handover" (section 10).

**Pack fixes:**
1. ~~`LINES` must map programme "MT" → A400M~~ applied 12 Oct.
2. Customer returns require FTO2 in `liability` (else "Hors périmètre"): applied 12 Oct.
3. Still pending: **drop the A400M chart** (all MT long texts are redacted): remove `q02_top5_A400M.sql`, its preview card, and mentions in the doc and README.

---

## 6. Cable defects (12 Oct) — the current hot topic

Data: 1,127 NCs (dashboard export + missing IDs), 3,098 defects with v4.8, **2,768 in the FTO2 perimeter**. "Cable problem" = `defaut_cable`: the cable itself must be remade or resupplied.

**Headline:** only **243 of 2,768 FTO2 defects (9%)** are cable problems, and only **25** are clearly cable supply (Kitting Factory). Cable problems are a small slice of every category.

| Category | FTO2 defects | Cable | Share |
| --- | --- | --- | --- |
| MEO Câblage | 996 | 77 | 8% |
| Erreur Branchement | 821 | 5 | 1% |
| Élément Endommagé | 304 | 63 | 21% |
| Élément Manquant | 301 | 72 | 24% |
| Kitting Factory | 48 | 25 | 52% |
| Others | 298 | 1 | — |

**Where cable defects land, with codes and RCA**

| Category | Sub-category | Official sub-codes | RCA | Cable defects | Cause stated line / received / not stated |
| --- | --- | --- | --- | --- | --- |
| MEO Câblage | Câble à refaire (ligne) | part of Q06-001 (E1) | Mauvais Cheminement | 58 | 27 / 0 / 31 |
| MEO Câblage | Cheminement – longueur / tension | Q06-001 | Mauvais Cheminement | 16 | 14 / 0 / 2 |
| MEO Câblage | Sertissage | Q07-001…010 | Défaut de Sertissage sur câble standard | 2 | 1 / 0 / 1 |
| Élément Endommagé | Dommage – câble | Q11-001, Q11-014 | Câble Endommagé | 63 | 4 / 0 / 59 |
| Élément Manquant | Manquant – câble / shunt / élément | Q03-004, T01, T03 | Câble ou Élément Manquant | 72 | 0 / 1 / 71 |
| Kitting Factory | Amont · Câble | Q12-001…004, Q12-007/008 | Défaut d'Impression | 25 | 0 / 18 / 7 |

Key points for the defence:
- **Only length problems reach MEO.** Damaged or missing cables stay in Endommagé / Manquant even when the line caused them.
- **The official codes can't separate line vs supply for damage.** Q11-001/014 carry no cause; only length splits (Q12-003 supply vs Q06-001 line).
- **196 of 243 cable defects have no code written**; classification is from text.
- **Provenance is set only from explicit wording** ("coupé trop court", "par l'opérateur"…). "Sur la ligne A350, nous constatons…" is detection, not cause. A few obvious handwork phrases are missed ("coupé par erreur", "à cause des pions de cheminement", ~5 of 59).
- **Routing is mostly not about cables because of inspection lists:** 113 of 146 routing defects come from 45 NCs with >10 defects (101 at station V4V141 "FINITION WF492"), all minor rework (overlength, tension, re-routing). When routing is the only defect in an NC, 16 of 24 are a cable to remake.
- **Counting effect across the Pareto:** 1,824 of 2,768 FTO2 defects (66%) come from inspection lists (>10 defects); only 539 from standalone NCs. Suggest showing Pareto by defect and by NC.
- **LLM vs regex:** the one-off LLM run put 65 cable defects in Kitting Factory vs 25; 40 of the 43 moves came from the cable team tracker saying "print room", not from the text. Tracker overall: 123 production line vs 58 print room.

**Options waiting for Mohammad's decision**
- **A.** Damaged cable not stated "received" → MEO Câblage, new RCA "Câble endommagé (ligne)" (~63 move).
- **B.** Extend cause wording; only explicit cases move (~9).
- **C.** Keep categories; add a cable-origin chart (received / line / not stated).
- **D.** Join the cable team tracker ("Suivi NCs - A30 - NC câbles et analyses", Imputation) where text is silent.
- Open: which definition of "cable problem" the meeting uses ("a cable had to be remade" = 243, or "any harness wiring work").

Deliverables: Docs "FTO2 Cable Defects – Findings"; `05_outputs/FTO2_defects_detail.xlsx` (one row per defect, rebuilt by `build/build_all.py`); `07_scripts/cable_check.py`.

---

## 7. REC tagging (7–8 Oct)

Goal: "accurately tag REC NCs from all the Skywise NCs". REC = team writing NCs at the FAL REC stations; the tracker "Fichier suivi des retouches REC – NC rédigées par le REC" lists NCs written by REC with an Imputation (REC 50 / FAL 55 / QSR 10 / N/A 1; 116 entries with an NC number).

**Why REC is missed today:** scope needs FTO2 in plant or liability; 101 of 115 tracker NCs are at FFF1/FNZ1/DHA1/DBR1/FTO1 with liability [FFF1]/[TO]. Of 94 tracker NCs created 20 Jan – 28 Sep, 17 reach the dashboard (all tagged REC). The current REC tag comes only from `workflow_list`; it also tags ≥25 FAL-written "NC sent to REC/A30" NCs and 5 rows that are in GPS (SERIE-only register).

**Three meanings:** written by REC (taggable from fields) · sent to / fixed by REC (text only, 51 rows, review flag) · caused by REC (tracker Imputation only; REC- vs FAL-imputed look identical in Skywise).

**Proposed rule:** label = FTI (current rule) → REC → SERIE (default). Scope = current FTO2 filter OR REC (no plant condition on the REC side). REC if any of:
1. `station` contains `42RC` (V42RC1 = "REC A350 FAL TLSE"; F42RC1, F42RC2, D42RC1 assumed same). Only 42RC — V42120/V42140 are SERIE production stations.
2. `work_ctr` starts with `RECX` or `SUBR` (adds little: 97/115 tracker NCs have it blank).
3. First author ID in `description_long_text` on the REC list (provisional: ST32873, GALIZ81C, RGAGTM5M, PMAR3D30, CLOP5B4I, TO74350, MCROIP8V).
4. NC number in the REC tracker.

Author regex — extract then compare (using it alone as a filter matched ~1 million rows):
```
\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\(\s*(\S+)\s+[A-Z0-9]+\s*/
```
One-step boolean version:
```
(?s)^(?:(?!\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\(\s*).)*\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\(\s*(?:ST32873|GALIZ81C|RGAGTM5M|PMAR3D30|CLOP5B4I|TO74350|MCROIP8V)\s
```

**Coverage (reproduced by `07_scripts/rec_checks.py`):** tracker NCs in window: station/WC 71 → +FTO2 filter 84 → +authors 90 → +tracker 94. Outside plant FTO2: 89 → 97. Dashboard files: 57 REC under new rule vs 85 today; GPS conflicts 1 vs 5. 38 rows at 42RC, 36 tagged REC, only 3 in tracker → tracker is incomplete; station is the better primary rule. 45% of dashboard rows (32/115 tracker NCs) show author `#UID~` in exports.

**Corrections to the earlier note** (`06_input_data/REC_findings_note_unverified.md`): Finding 1 table wrong (QSR 10/10, "N/A" not blank; table sums to 93/16); 42RC is confirmed by station description; inspector IDs look clean; QSR campaign has 9 SERIE rows not 5; Finding 5's 34 "errors" are mostly FAL "sent to REC" NCs; the 1,000 cap is `.head(1000)`.

**Open:** which REC to tag (written / fixed / both); whether the 25 "sent to REC/A30" NCs are REC or SERIE; precision on all Skywise (count NCs since 20 Jan by station/plant/user_department where station ~42RC or work_ctr RECX/SUBR; read ~20 long texts); REC's real inspector list; whether the pipeline sees real author IDs; F42RC1/F42RC2/D42RC1 confirmation; tracker typo 2181014667 = 218014667 (assumed).

Deliverable: Docs "REC NC Tagging – Findings".

---

## 8. Earlier work (Aug – Sep 2026, H1 data) — still valid background

Full detail: `03_reports/dossier_stage_NC.md` (French master dossier) and `NC_deep_dive_report.md`.

- **Hidden volume ×3:** 807 NCs → 2,346 defects; ~15% of NCs (bundles) carry ~70% of defects; monthly NC counts flat (~110–150) while defects run 310–430/month.
- **Inversions are about confusable pins, not people:** 267 of 269 inversions (99.3%) are between twin/adjacent pins; concentrated on ~10 connectors (3RN, 1WK, 300VT, 3SEA, 9KS, 1608VC…), no learning curve over 6 months (49–81/month). Proposed bounded action: keying / marking one pin of each hot pair / buzz-test, with before/after KPI.
- 82% of defects found at end of line (final control 43%, test 39%); retouch station V42RA1 on 12% of NCs; 90% of wrong-pin errors are off-by-one; 52% of NCs root-caused "[People]"; SAP defect code puts 45% in one bucket.
- March spike traced to one crimping tool (M22520/2-01, s/n DSM 39391135970) on five A320 MSN.
- KPI inflated 11.5% by deleted NCs (half provable duplicates).
- Three writing teams: OLMEP14 test (100% coded `DEF n-CODE :`), QRT Derichebourg final control (`Def1 :`, biggest bundles, 0% coded), QRTE MIP inspection (`1 - FIN`). `user_department` matches the real author only 55% of the time.
- **Supplier attribution:** `responsible_defect_level1` Y4 = supplier (deterministic), Y5 = plant; supplier classifier 97–98.7%; top "supplier" is DUMMY TEST ONE SHOT PO; 12 disputed imputations listed. (`fournisseur_classifier.py`, `fiche_arbitrage_12_NC.csv` and the waterfall PNG came from an earlier session and are not in this bundle; the dossier describes them.)
- Dead columns: `origin` (always Q3), `defect_quantity`, `GPS_Imputation` (constant). `Produit_auto` vs `Ext_Produit` only 66% agreement.
- **Writing standard "DEFAUTS v1"** (`standard_defauts_v1.md`) and **NC entry assistant spec** (`spec_assistant_saisie_NC.md`, tool prototypes `08_tools/*.jsx`, flow `nc_tool_logic_flow.mermaid`).
- **Proactive dashboard roadmap:** parse → reconcile with GPS/Ext → alerts (recurrence by FIN, rate drift SPC, new-symptom detector, data-health tile) → AI only on the residue.
- Tool choice: Skywise over Sheets/Qlik (official direction).
- Management presentation: `03_reports/stage_presentation.pptx`; findings report `FTO2_NC_Findings.pdf/.html`.

---

## 9. Next steps, in priority order

0. **CNQ checks (19 Oct):** go through `05_outputs/CNQ_investigation_checklist.html` with Mohammad (H1-H7 are high). Apply what he decides; the list of changes done, decided and kept for later is `CNQ_CHANGES.md`. Scope decided: REC and ERMA out; disruption block (quality aléas with no NC) shown beside the NC cost.
1. **Cable defence:** get Mohammad's choice among options A–D and the "cable problem" definition; then produce the slide numbers (by defect and by NC). Nothing in the parser has been changed for this yet.
2. **REC:** get the definition decision; ask for the precision query result and REC's roster; then write the final rule spec for the pipeline team (columns `rec_written`, `rec_fixed`, `imputation`).
3. **Pack v4.8:** drop the A400M chart when he asks; confirm whether the pack was installed.
4. **Mohammad to check** the English RCA / category translations in the FR/EN dashboard.
5. Verdicts on the 330 parser vs root-cause disagreements (`05_outputs/FTO2_llm_longtext_review.xlsx`). The old v4.7 review list is in `05_outputs/archive/`.
6. Not started: CNQ reconciliation of predecessor files with the official method (M1888 CNQ, UG2600252 NC cost model / concession MC.QU.02).

---

## 10. Links (Claude artifacts, private to Mohammad's account)

- Skywise NC Dashboard Handover (install guide for pack v4.8): https://claude.ai/code/artifact/691b9b8e-8254-4684-a8db-75a332082083
- FTO2 NC Dashboard (Pareto · weekly · CNQ): https://claude.ai/artifact/988FNWFkPFRB1aPiBU2Tg1
- Superseded (now a tab of the dashboard): FTO2 Customer Returns https://claude.ai/artifact/MqRPgo7bmHEpKv9UTXPJ4C
- Superseded: FTO2 Defect Pareto (July data) https://claude.ai/artifact/M6Ge6BcdZwxPRo3A8LD3dM
- FTO2 Cable Defects – Findings: https://claude.ai/artifact/UNhxy243Yyco6n15hzppNm
- REC NC Tagging – Findings: https://claude.ai/artifact/5H6psRy637FS91KfsKBF4s

---

## 11. Data gotchas

- Programme **MT = A400M**; all its long texts are "Removed for classification reason".
- Exports mask names: `#UID~`, `#PRS~`, `#TEL~`.
- `liability` is an array in Skywise (`[FFF1]`, `[TO]`, `[FTO2]`); `liability_description` is `[PLANT]/[SUPPLIER]/[OTHERS]/[MIXED]`.
- GPS = manual extract, **SERIE only**, cannot be part of the pipeline; useful as a SERIE check.
- Dashboard export = newest 1,000 NCs only (`.head(1000)`); fetch missing IDs with RUN_MODE = "MISSING_IDS".
- `notification_type`: NC / AF / AM. `trigger`: WO (work order, FTO2 shop floor) vs CA (on aircraft, FAL).
- Station prefixes: V4/F4/M4/D4 = FTO2 production stations; 42RC = REC at FAL; F10xx/V10xx = FAL stations.
- Read untrusted CSVs with `python3 -I` from a separate directory (session rule).

---

## 12. Bundle contents

| Folder | Content |
| --- | --- |
| `01_parser/` | `nc_defect_parser.py` v4.8 (current); `archive/` v4.5–v4.7 and the Sep v1 |
| `02_dashboard_pack/` | Install pack v4.8 (pipeline, Slate queries, check values, reference) + zips v1 and v4.8 |
| `03_reports/` | **FTO2_NC_Dashboard.html** (built); H1 dossier, deep dive, classification spec, code-sheet analysis, taxonomy notes, writing standard, entry-tool spec, findings PDF/HTML, presentation (H1 work, kept as is); `archive/` old Pareto page and Slate preview (July data), retired customer-returns page |
| `04_reference/` | Official codes, sub-category reference, mappings, codes to verify, **root-cause labels per defect line** (`llm_labels_longtext.csv`, input of the build) |
| `05_outputs/` | Built by `build/build_all.py`: `fto2_defects.csv`, `fto2_nc.csv` (reference datasets), `fto2_*_cnq.csv`, `FTO2_defects_detail.xlsx`, `FTO2_llm_longtext_review.xlsx`. `archive/`: older snapshots (v4.1–v4.7, NC table v4.7, old LLM sub-codes and review list, cable review files, count disagreements) |
| `06_input_data/` | Inputs Mohammad uploaded: dashboard export, missing IDs, nc-rec, REC tracker, cable team tracker, MFT action trackers (A330/A350), pipeline notebook, earlier REC note, sample NC text, code sheet text |
| `07_scripts/` | `rec_checks.py`, `cable_check.py`, `llm_longtext/` (how the root-cause labels were made) (+ older working scripts in `archive/`) |
| `build/` | `build_all.py` (one script for every output), `templates/dashboard.html` (the dashboard page), `build_report.json` (counts and checks of the last run) |
| `cnq_handoever/` | Mohammad's CNQ model, refreshed on the same data (README section 13) |
| `08_tools/` | NC entry tool prototypes (JSX), logic flow (Mermaid), old Slate SQL and preview |
| `cnq_handoever/` | CNQ model (pipeline step, Slate queries, offline dashboard, tests); README_handover.md section 4 lists the 19 Oct changes |
| `CNQ_CHANGES.md` | Every CNQ change: applied, decided, kept for later, needed from the pipeline team |
| `05_outputs/CNQ_investigation_checklist.html` | Offline checklist of open CNQ checks; click a check to open its list; answers kept in the browser, CSV export |
| `06_input_data/work_orders_disruptions_nc2025.rar` | Upload of 19 Oct: SAP work-order operations (Sept 2026), MES aléas (Jan-Sep 2026), Skywise NCs 2025 |
| `07_scripts/wo_disruption/` | Scripts behind every number of the 19 Oct analysis, README with run order |
