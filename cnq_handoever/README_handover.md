# Cost of non-quality (CNQ) for Airbus Electric Center - handover

Version `cnq-2026.10.20b`, updated 20 October 2026 (rates per step: production 123 EUR/h, quality 107 EUR/h, ME 76 EUR/h; engineering stays at the Airbus 78.16 EUR/h). Section 2 totals: this model on the current Skywise exports (856 AEC NCs, rebuilt 20 October 2026); the build recomputes them at every refresh (`build/build_report.json`, section 13). The worked examples in section 3 come from the 19 October CNQ pack.

## 1. What this is

A calculation that puts a cost in euros on every non-conformity (NC), so the quality team can see
where non-quality costs the plant money. It is a modelled estimate built from process times, not
measured hours, and it is not the official Airbus CNQ declaration.

It is delivered in the same shape as the NC dashboard:

```
Skywise NC source
      |
defect parser step          (exists)   -> FTO2 NC dataset + FTO2 defects dataset
      |
CNQ step                    (new)      -> fto2_nc_cnq + fto2_defects_cnq
      |
Slate queries               (new)      -> bar charts
```

All the logic is in the pipeline step. The Slate queries only add up cost columns, so changing a
time or a rate never means touching Slate. A standalone HTML dashboard
(`dashboard/cnq_dashboard.html`) shows the same figures in French or English, works offline with no
server, and lets the team change a time and see the effect, to validate the rules before they go
into Slate.

## 2. Three levels, for the same NCs

Only NCs where AEC is liable are counted (856 NCs, created 15 Dec 2025 to 28 Sep 2026). Defect lines come from parser v4.8 and are
classified by root cause from the full NC text (`04_reference/llm_labels_longtext.csv`); with the parser v4.8 labels instead, level 3 is 182,887 EUR.

| Level | What it does | Total | Per NC | Column |
|---|---|---|---|---|
| 1. Airbus transnational | Each NC at the official Airbus standard cost for its decision. No material. | 403,489 EUR | 471 EUR | `cnq_cost_airbus` |
| 2. Global average | Each NC at AEC's average times: 30 min to write the NC, 1 hour of work for a rework. Plus material. | 143,298 EUR | 167 EUR | `cnq_cost_global` |
| 3. Per defect | AEC's steps, with the work built from each defect found, or the planned time of the NC's closed rework order; the alert at the declared time of the aléa that led to the NC. Plus material. | 178,847 EUR | 209 EUR | `cnq_cost_total` |

Level 3 is the reference. Levels 1 and 2 are there to compare: what the general Airbus model would
say, and what a flat average would say. NCs on other plants or suppliers (271 NCs, 37,728 EUR of
handling at level 3) are shown aside and are in none of the totals.

Without the changes of 20 October (section 4: rework orders' planned time, declared aléa time) level 3 is 175,663 EUR; with the orders only, 177,436 EUR. Before the changes of 19 October 2026 (section 4), on the same exports, level 3 was 181,405 EUR and level 2 144,265 EUR; on the smaller 19 October CNQ pack the changes took level 3 from 134,206 to 128,741 EUR.

## 3. How one NC is costed, with examples

### Level 3, per defect

For a reworked NC:

| Step | Time | Charged |
|---|---|---|
| Operator raises the alert (aléa) | 41 min | once per NC, only when an operator raises one: not for NCs found at test or at final inspection. Customer returns always get it (the customer's operator raises it). |
| Quality inspector writes the NC | 30 min, 60 at final inspection | once per NC |
| Technical support checks, estimates, creates the work order | 60 min | once per NC |
| Around the work: badging, fetching, setting up | 50 min | once per NC |
| Hands-on work | minutes of each defect line; connection errors: the first one of the NC at its class time (35 min), each following one 15 min | per defect |
| Re-check and closing (quality line service) | 30 min | once per NC |

For internal NCs, the work (around the job + hands-on) is multiplied by 2.

Cost = each step's minutes / 60 x the hourly rate of who does it, plus the material of each defect line:

| Step | Who | Rate |
|---|---|---|
| Alert, setup (around the job), hands-on work, time lost on a declared aléa | Production | 123 EUR/h |
| Writing the NC, re-check and closing | Quality | 107 EUR/h |
| Technical support | ME | 76 EUR/h |
| Engineering (design query) | Airbus engineering | 78.16 EUR/h |

Before version `cnq-2026.10.20b` every step was at one rate of 50 EUR/h. The rates are in
`cnq/cnq_params.py` (`RATES`, `STEP_WHO`) and can be changed on the check sheet.

The work (around the job + hands-on) is never under 1 hour. If the defects add up to less than
10 minutes, the time around the job is raised so the work reaches 60 minutes.

**Example A - one defect, found in-process, internal NC (NC 216135746).** One defect, "bonding
protection badly applied", 10 minutes. Work (50 + 10) x 2 = 120 minutes.
41 + 30 + 60 + 120 + 30 = 281 minutes. Production 41 + 120 = 161 min x 123 = 330.05, quality 30 + 30 = 60 min x 107 = 107.00,
ME 60 min x 76 = 76.00: **513.05 EUR**. No material.

**Example B - nine defects, found at final inspection (NC 216224176).** No operator alert.
Hands-on: 6 connection errors (35 + 5 x 15 = 110 min) + 2 wrong electrical references x 30 min +
1 component out of order x 30 min = 200 minutes.
60 (final inspection) + 60 + 50 + 200 + 30 = 400 minutes. Production 250 min = 512.50, quality 90 min = 160.50,
ME 60 min = 76.00: 749.00 EUR, plus 0.36 EUR of material = **749.36 EUR**.

**Example C - a one-minute defect, cable NC (NC 216573781).** Hands-on 1 minute. 50 + 1 = 51
minutes of work is under the minimum, so the time around the job becomes 59 minutes.
41 + 30 + 60 + 59 + 1 + 30 = 221 minutes. Production 101 min = 207.05, quality 60 min = 107.00, ME 60 min = 76.00:
**390.05 EUR**. This applies to 128 AEC NCs.

Other decisions:

| Decision | What is charged | Example |
|---|---|---|
| Rejection, scrap | Alert, writing, technical support, closing. No work. Plus the value of the part. | NC 16995857 (a customer return): 41 + 30 + 60 + 30 = 161 min = **267.05 EUR**. Part: 0 EUR, no price in the data. |
| Rejection with a rework order | Same as rework, plus the value of the part. A rejection whose NC has a rework order in `linked_document`. | NC 216052773 (internal): 41 + 30 + 60 + (50 + 20) x 2 + 30 = 301 min = 250.83 EUR + 0.85 material = **251.68 EUR** |
| Exchange | Alert, writing, technical support, closing. No work (no rework order at FTO2). Plus the value of the swapped part. | NC 216037622: 161 min = **267.05 EUR** |
| Deleted (any decision) | Alert and writing only | NC 216123618: 41 + 30 = 71 min = **137.55 EUR** |
| Design query | Alert, writing, technical support, closing, plus 8 h of engineering at 78.16 EUR/h | NC 216733534: 267.05 + 625.28 = **892.33 EUR** |
| Accept as is, potential NC | Alert, writing, technical support, closing | 267.05 EUR (183.00 EUR without alert) |
| No decision | Alert and writing | 137.55 EUR |

Only the rework process was described by the team. Rejection and exchange were set from the
September 2026 rework orders; the other rows are assumptions.

### Customer returns

A customer return on AEC (45 NCs, 8,434 EUR) is in the total and is costed like any NC of its
decision, every step included (the customer's alert too): AEC is the direct cause. The repair
itself happens at the customer; the model estimates it at FTO2's times. Two ways to go further,
both already built:

- `CUSTOMER_RETURN_EXTRA` in `cnq_params.py`: a flat amount added to every customer return
  (analysis, reply to the customer, logistics). It is 0 EUR until the team sets a figure.
- A `customer_return_cost` column in the NC dataset: the real amount of a return, when known. It
  replaces the estimate for that NC.

In the dashboard, the "Retours client" tab lists every return with its estimate and a field for the
real amount. Amounts typed there stay in that browser only; to make them permanent, put them in the
`customer_return_cost` column.

### Level 2, global average

The same steps, but every NC gets the average times whatever its defects: 30 minutes to write the
NC and 1 hour of work for a rework. Material is added as in level 3. The alert follows the same
rule as level 3.

- Example A: 41 + 30 + 60 + 60 + 30 = 221 min = 184.17 EUR, against 234.17 EUR at level 3.
- Example B: 30 + 60 + 60 + 30 = 180 min = 150.00 EUR + 0.36 EUR material = **150.36 EUR**, against
  333.69 EUR at level 3. This is what the flat average hides: an NC with nine defects costs no more
  than one with one.

### Level 1, Airbus transnational

The standard cost per NC from the official model (MC.QU.02.01), applied as it is: 66.25 EUR/h,
Airbus standard hours (6.5 h for a rework), +5 % on the creation step, +25 % for NCs sent back.
No material, and no account of how many defects the NC has.

| Decision | Airbus standard | Match |
|---|---|---|
| Rework | 542.42 EUR | official "rework as per design data" |
| Exchange | 542.42 EUR | assumed: taken as a rework |
| Accept as is | 252.27 EUR | official "acceptable as is" |
| Design query | 951.33 EUR | official "engineering assessment", assumed match |
| Reject (with or without rework order), scrap, potential NC | 252.27 EUR | assumed: creation, assessment, decision |
| No decision, deleted | 69.56 EUR | assumed: creation step only |

Examples A and B both cost 542.42 EUR at this level.

## 4. Team rules applied in October 2026

From the team's notes, as I read them:

| Note | What was done |
|---|---|
| Rework minimum / average 1 h | Level 3: the work is never under 60 min. Level 2: every rework gets 60 min. |
| NC average 30 min | Level 2 uses 30 min to write every NC. Level 3 keeps 30 min, 60 at final inspection. |
| Wrong reference = 2 x missing | The five "wrong reference" classes take twice the minutes of the matching "missing" class. |
| Q11 (damaged electrical part) = 2 x missing | Broken or failed component, damaged cable, damaged sleeving, damaged identification: twice the matching "missing" class. |
| Routing depends on access | Not modelled. One time per class cannot capture it. Open point. |
| Q12 (printing): printing time, and maybe a full rework? | Not modelled. The upstream classes stay at 5 min until this is decided. Open point. |

These links are written once in `cnq_params.py` (`DERIVED_TIMES`): change the "missing" time and
the "2 x" classes follow. One line of the notes, "SO3", could not be read; nothing was changed for it.

Effect to be aware of: a damaged cable is now 30 min (2 x missing cable or part, 15 min). The old
code table said 60 min.

### Changes of 19 October 2026, from the SAP rework orders and the MES aléas

The rework orders technical support creates for each NC (SAP order type S03, linked from the NC's
`linked_document` field) carry a planned time per operation (unit IM = 1/100 hour). The MES
disruptions (aléas) carry the time lost declared by the operator. Compared with the model on
September 2026 orders and Jan-Sep 2026 aléas, these rules were changed, approved by Mohammad:

| Change | Evidence | Parameter |
|---|---|---|
| The operator alert is charged only when an operator raises one: not for NCs found at test or at final inspection | Jul-Sep 2026: 0 of 52 test NCs and 4 of 23 final-inspection NCs started with an MES aléa; 42 of 49 cable NCs did | `NO_ALERT_TYPES` |
| Customer returns always get the alert | The customer's operator raises it; AEC is the direct cause | `NO_ALERT_TYPES` (customer returns exempt) |
| The alert is 41 min instead of 30 | Mean time lost declared on the 214 quality aléas that led to an NC (median 30) | `MIN_ALERT` |
| Connection errors: the first one of an NC takes its class time (35 min), each following one 15 min | Rework orders of test NCs plan about 77 min + 15 min per connection error (11 NCs). Before, the model was 79% above the planned time on test NCs. | `CONNECTION_CLASSES`, `MIN_CONNECTION_NEXT` |
| Internal NCs: work (around the job + hands-on) x 2 | 11 complete rework orders of internal NCs: 1,896 planned minutes against 951 in the model; per-NC median ratio 2.0 | `INTERNAL_TYPES`, `INTERNAL_WORK_FACTOR` |
| Exchange: no work, swapped part counted | 0 of 20 exchanges in 2026 had a rework order | `RULES["EXC"]` |
| Rejection with a rework order: work charged (rule `REJ_RW`) | About half of rejections get a rework order (median 1 h 40 planned) | `REWORK_ORDER_PREFIXES`, `RULES["REJ_RW"]` |

Effect on level 3: 134,206 -> 128,741 EUR on this package's data; 151,093 -> 149,824 EUR on 2026
Feb-Sep (parser v4.8, raised at FTO2); 178,170 -> 178,870 EUR on 2025 (raised at FTO2, without
ERMA). The totals move little, but the cost moves between NC types: test NCs down, internal NCs
and rejections with a rework order up. The WO figures come from one month of rework orders and
should be re-checked on a full year. The full list of changes, done and to do, is in
`CNQ_CHANGES.md` at the root of the repository.

### Change of 20 October 2026: the planned time of the NC's rework order (version cnq-2026.10.20)

When the NC dataset carries the planned time of the NC's rework orders, an NC whose orders are all
closed and planned is costed with that time instead of the model's setup and hands-on work:

- setup = the planned time of the orders' preparation, inspection and closing operations; hands-on =
  their work and test operations. No connection rule, no x 2 for internal NCs (the order is the real
  plan). Alert, writing, support, re-check, material and engineering stay as before.
- An order still open (no closing operation yet), closed without planned time, or not in the
  operations keeps the model. A closing operation is one whose text holds "attestation", "clôture" or
  "autoclos".
- `cnq/cnq_orders.py` builds the input from the work-order operations: `nc_order_times(nc, ops)`
  returns, per NC, `rework_orders`, `order_state` (used / open / no_time / not_found),
  `order_minutes_setup` and `order_minutes_work`. Merge it into the NC dataset before
  `compute_cnq`. The output column `cnq_work_source` says `order` or `model`.
- On the dashboard data with the Sept 2026 operations (the only month extracted so far): 800 NCs
  link to a rework order, 71 are costed on its planned time (13 closed without time, 17 still open,
  699 orders outside the extract). Level 3 on AEC: 175,663 -> 177,436 EUR; most of the rise is NC
  218233692 (34 h planned, +1,665 EUR). With the full order history in Skywise, nearly every
  reworked NC would use its order.
- `USE_ORDER_TIME = False` in `cnq_params.py` goes back to the model alone.

### Change of 20 October 2026: the declared time of the aléa that led to the NC (same version)

- An MES aléa leads to an NC when the NC is on the same work order and was created from 2 h before to 72 h after the
  aléa opened (main's study: 214 of 322 quality aléas, Jan-Sep 2026). `cnq/cnq_disruptions.py`,
  `nc_alea_times(nc, ds)`, returns per NC `aleas` (ids) and `alea_minutes` (declared time lost of its quality aléas).
- When `alea_minutes` > 0, the alert step is that time instead of the flat 41 min, and it is charged even on NCs found
  at test or final inspection (an aléa was raised). A declared 0 means not filled: the 41 min stay (25 NCs). Customer
  returns keep the 41 min. Output column `cnq_alert_source`: `alea` or `flat`. `USE_ALEA_TIME = False` goes back.
- On the dashboard data with the Jan-Sep 2026 aléas: 200 NCs have a linked quality aléa, 175 use its time (median 30
  min, mean 50). Level 3 on AEC: 177,436 -> 178,847 EUR.
- The same function returns the disruption block: quality aléas that led to no NC (108), of which 19 on the MIP /
  1101VB (possible ERMA NC) left out until checked: 89 aléas, 66.9 h, 3,347 EUR. The dashboard shows it beside the
  cost, never inside.

## 5. What is in the package

| File | What it is |
|---|---|
| `cnq/cnq_params.py` | Every time, rate and rule. The only file to edit when a number changes. |
| `cnq/cnq_core.py` | The calculation, in pandas. No Foundry dependency. Tested. |
| `cnq/cnq_orders.py` | The planned time of each NC's rework orders, from the SAP work-order operations (input to `cnq_core`). |
| `cnq/cnq_disruptions.py` | The MES aléas: declared time of the aléa that led to each NC (input to `cnq_core`), and the disruption block. |
| `cnq/foundry_transform.py` | Wrapper to run it as a Foundry transform. Template, not yet run in Foundry. |
| `slate/slate_queries.sql` | 18 queries for the charts. Tested in SQLite on the sample outputs. |
| `dashboard/cnq_dashboard.html` | Standalone dashboard, French / English, fully offline. One page: summary, how an NC is costed (steps, rules per decision, any real NC line by line), breakdown, customer returns, editable times, limits. |
| `dashboard/build_dashboard.py` | Rebuilds the check sheet from the output datasets. |
| `params/*.csv` | The parameters as three tables, for review. Generated from `cnq_params.py`. |
| `sample_output/*.csv` | The two output datasets computed on the current exports (parser v4.8 lines, root-cause labels). Rebuilt by `build/build_all.py`. |
| `tests/run_local.py` | Runs the calculation on two CSV files and writes the expected totals. |
| `tests/test_queries.py` | Runs every Slate query and checks the charts add up to the totals. |
| `tests/test_dashboard.js` | Checks the check sheet gives the same cost as the pipeline for every NC. |
| `tests/expected_totals.json` | The totals the first Foundry build should reproduce. |

## 6. How to install

1. Copy the `cnq` folder into the code repository, next to the defect parser.
2. Add the missing columns to the FTO2 NC dataset (section 7). The step refuses to run without
   `decision_status` and `liability`.
3. In `foundry_transform.py`, replace the four `<PATH>` dataset paths, then build.
4. Compare the build with `tests/expected_totals.json`. Totals should match to the cent if the
   data is the same export.
5. In Slate, create one query per block of `slate_queries.sql`, replacing the two table names with
   your dataset references. Each block says which chart it feeds. `q00_three_levels` gives the
   three numbers.

To check anything outside Foundry:

```
python3 build/build_all.py          (from the repository root: rebuilds everything and runs the two checks below)
python tests/test_queries.py
node tests/test_dashboard.js
```

`tests/run_local.py <nc.csv> <defects.csv>` runs the calculation alone on any pair of CSV files, for example the first
Foundry build. The NC file must carry the columns of section 7; `build_all.py` takes them from the Skywise export.

## 7. What the NC dataset must contain

| Column | Needed for | In v4.7 today? |
|---|---|---|
| `notification_number` | key | yes |
| `statut` (open / closed / deleted) | deleted NCs are costed differently | yes |
| `date_creation` | month and week | yes |
| `decision_status` (RWK, REJ, EXC, DQN, ...) | which steps are charged | **no - add from Skywise** |
| `liability` (plant or supplier code, e.g. `[FTO2]`) | whether the NC is on AEC | **no - add from Skywise** |
| `type_nc` (e.g. `CONTROLE FINAL`) | 60 minutes instead of 30 to write the NC; "where found" chart | **no - add** |
| `produit` | product chart only | **no - add** |
| `responsabilite` | splits the aside group into plant / supplier | yes |
| `linked_document`, `work_order` | finds the NC's rework order (a rejection with a rework order is charged its work) | **no - add from Skywise**; without them every rejection is costed without work |
| `order_state`, `order_minutes_setup`, `order_minutes_work` | the planned time of the NC's rework orders (`cnq_orders.nc_order_times`, from the S03 work-order operations) | no - optional; without them the model's times are used |
| `alea_minutes` | declared time of the quality aléas that led to the NC (`cnq_disruptions.nc_alea_times`, from MES Disruptions) | no - optional; without it the flat 41 min are used |
| `customer_return` | 1 for a customer return (pipeline's `Type_NC_auto` = "NC Retour client" with FTO2 in the liability) | yes |
| `part_value` | value of a rejected or exchanged part, in EUR | no - optional, see section 9 |
| `customer_return_cost` | real amount of a customer return, in EUR; replaces the estimate | no - optional |

Two warnings about columns that look right but are not:

- `responsabilite = [PLANT]` does not mean AEC. It includes other Airbus plants. Only
  `liability = FTO2` is AEC.
- In the Skywise export, `Statut_decision_auto` writes "DQN" on NCs whose real code is "no
  decision". Use `decision_status`.

The defects dataset needs `notification_number`, `sous_groupe` and, if present, `qty`.

## 8. How far to trust each number

| Label in `cnq_params.py` | Meaning |
|---|---|
| LOCAL | AEC's own estimate of its process, described by the team in October 2026 |
| TEAM | The team's code table from the old Excel tool. Estimates, never timed. |
| TEAM RULE | A link between classes set by the team (2 x missing) |
| OFFICIAL | Airbus cost model MC.QU.02 |
| BORROWED | From a 2021 time study, because AEC has no figure |
| WO | Planned time on FTO2's SAP rework orders (order type S03), September 2026 only. Planned, not measured; to re-check on a full year |
| MES | MES disruptions (aléas) of plant FTO2, Jan-Sep 2026: time lost declared by the operator |
| ASSUMED | Not confirmed by anyone at AEC |

Nothing is measured. Two research reports looked for published benchmarks and found none that
confirms or rejects any of these times. The only way to firm them up is to time them on the floor.

## 9. Known gaps, most important first

1. **Parts have no price.** 132 AEC NCs are rejects, scraps or exchanges, and the lost part counts
   as 0 EUR. To fix: add a `part_value` column (the SAP price of the rejected part, not of the
   assembly). The calculation already uses it when present.
2. **Customer returns are under-estimated.** Only the handling of the NC is counted. Analysis,
   reply to the customer, transport and penalties are not, until the flat extra or the real
   amounts are filled in (section 3).
3. **Connection errors rest partly on a borrowed time.** Swapped and wrong connections are the two
   most frequent defects (639 costed lines, 9,554 EUR of hands-on work). The first one of each NC
   (94) is at 35 minutes from a 2021 study; the 545 following ones are at 15 minutes from the
   September 2026 rework orders (11 NCs).
4. ~~57 AEC NCs missing from the NC dataset~~ **Solved (12 Oct):** the NC dataset is now built from the Skywise export
   itself, so NCs with no defect line are kept (68 AEC NCs, 11,725 EUR, work at the flat 10-minute estimate).
5. ~~150 NCs with no master data~~ **Solved (12 Oct):** every NC now carries its status, decision and liability from the export.
6. **The class-to-time mapping is one person's judgement.** Each of the 40 parser classes was
   matched by meaning to one line of the team's code table. Someone who knows the work should
   review `params/cnq_defect_times.csv`, or the class table in the check sheet.
7. **Two material figures look too high**: 45.20 EUR for a badly positioned identification plate
   and 63.77 EUR for unfinished wiring. Together they drive about 3,200 EUR.
8. **Routing and printing defects** are open points from the team's notes (section 4).
9. **Other processes are partly assumptions.** Design query has not been described by the team.
   Reject and exchange were set from one month of rework orders; an exchange gets no work, although
   swapping the part may take time that is planned nowhere. Their level 1 match to the Airbus model
   is assumed.
10. **Rates per role (since cnq-2026.10.20b).** Production 123 EUR/h, quality 107 EUR/h, ME 76 EUR/h, given
   by the team on 20 October 2026; engineering stays at the Airbus 78.16 EUR/h. Other EUR figures in this
   document that are not worked examples date from the single 50 EUR/h rate; the build recomputes the
   totals (`build/build_report.json`, section 13).
11. **The final-inspection flag is approximate.** The two type columns in the Skywise export often
    disagree.
12. **The Foundry wrapper has not been run.** The calculation is tested on CSV files; the
    transform file is a template. Spark cannot guess the type of an all-empty column (such as
    `sub_code` in v4.7), so the wrapper drops those.
13. **The WO rules come from one month.** The 15 minutes per following connection error and the
    x 2 on internal NCs come from the September 2026 rework orders (11 NCs each). Re-check them on
    a full year of rework orders.
14. **Exceptional NCs are not visible.** One NC line can cover many items. NC 218233692 ("Câbles
    non lasérisés", Sept 2026) is one defect line in the model (about 1 hour) but its rework order
    plans 34 hours of reprinting cables for six routes. Only the planned time of the rework order
    can show this; the model cannot. Since cnq-2026.10.20 it does, when the order's operations are
    loaded (section 4).

## 10. Recommended next step: time the work

Ten classes cover most defect lines. Timing a handful of each on the floor would replace the
weakest numbers. A starting plan from the International Labour Organization table: about 5 timings
for a 35-minute job, 10 for a 10-minute job, 15 for a 3 to 5 minute job, 30 for a 1-minute job, then
let the spread of the results decide how many more are needed. Time the fixed 50 minutes around the
work separately from the hands-on part.

## 11. Why level 3 differs from the Excel workbook

The workbook `CNQ_model_AEC_2026.xlsx` gave 148,200 EUR on the earlier export. Level 3 gave
134,206 EUR before the changes of 19 October 2026 (128,741 EUR after them). The differences, before
those changes:

| Difference | Effect |
|---|---|
| 57 AEC NCs with no defect line are absent from the pipeline's NC dataset | - 9,375 EUR |
| Times per parser class (40) instead of per sub-code (150), because v4.7 has no sub-code; the team's "2 x missing" rules; the 1-hour minimum | - 4,619 EUR net |

The workbook remains useful as a readable explanation of the earlier logic. The pipeline is the
reference for numbers from now on.

## 12. Changing a number later

Edit `cnq/cnq_params.py`, rebuild, and the datasets and charts follow. If the parser adds a new
`sous_groupe`, it gets a default 10 minutes until a line is added to `DEFECT_TIMES`; the data-gap
query (`q14_data_gaps`) shows how many lines are affected. To try a value before committing it, use
the check sheet: its changes stay in the browser.

## 13. Refresh of 12 October 2026: one dataset for everything

Every output is now rebuilt by one script from the raw Skywise exports:

```
python3 build/build_all.py
```

It reads `06_input_data/fto2_dashboard_data*.csv` (standard export + NCs fetched by number), runs parser v4.8, joins the
root-cause labels, runs this CNQ model, rewrites `sample_output/`, `params/`, `tests/expected_totals.json` and
`dashboard/cnq_dashboard.html`, then runs `tests/test_queries.py` and `tests/test_dashboard.js`. The same figures feed the
FTO2 NC dashboard (`03_reports/FTO2_NC_Dashboard.html`, CNQ tab). `tests/run_local.py` still works on any pair of CSV files.

Changes in the figures against the July version: longer period (to 28 Sep), parser v4.8, root-cause labels, NCs with no
defect line kept, customer returns only when FTO2 is in `liability`. Three classes had no team time and now carry an explicit
10-minute ASSUMED line in `DEFECT_TIMES`: damaged ground braid, measurement out of tolerance, not classified.
Section 11 compares with the workbook on the July export and is kept as history.
