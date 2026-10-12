# Cost of non-quality (CNQ) for Airbus Electric Center - handover

Version `cnq-2026.10`, updated 7 October 2026.

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

Only NCs where AEC is liable are counted (595 NCs, 5 Jan to 6 Jul 2026, parser v4.7 data).

| Level | What it does | Total | Per NC | Column |
|---|---|---|---|---|
| 1. Airbus transnational | Each NC at the official Airbus standard cost for its decision. No material. | 280,004 EUR | 471 EUR | `cnq_cost_airbus` |
| 2. Global average | Each NC at AEC's average times: 30 min to write the NC, 1 hour of work for a rework. Plus material. | 102,500 EUR | 172 EUR | `cnq_cost_global` |
| 3. Per defect | AEC's steps, with the work built from each defect found. Plus material. | 134,206 EUR | 226 EUR | `cnq_cost_total` |

Level 3 is the reference. Levels 1 and 2 are there to compare: what the general Airbus model would
say, and what a flat average would say. NCs on other plants or suppliers (131 NCs, 15,746 EUR of
handling at level 3) are shown aside and are in none of the totals.

## 3. How one NC is costed, with examples

### Level 3, per defect

For a reworked NC:

| Step | Time | Charged |
|---|---|---|
| Operator raises the alert | 30 min | once per NC |
| Quality inspector writes the NC | 30 min, 60 at final inspection | once per NC |
| Technical support checks, estimates, creates the work order | 60 min | once per NC |
| Around the work: badging, fetching, setting up | 50 min | once per NC |
| Hands-on work | minutes of each defect line | per defect |
| Re-check and closing | 30 min | once per NC |

Cost = total minutes / 60 x 50 EUR, plus the material of each defect line.

The work (around the job + hands-on) is never under 1 hour. If the defects add up to less than
10 minutes, the time around the job is raised so the work reaches 60 minutes.

**Example A - one defect, found in-process (NC 216135746).** One defect, "bonding protection badly
applied", 10 minutes.
30 + 30 + 60 + 50 + 10 + 30 = 210 minutes. 210 / 60 x 50 = **175.00 EUR**. No material.

**Example B - nine defects, found at final inspection (NC 216224176).**
Hands-on: 6 connection errors x 35 min + 2 wrong electrical references x 30 min + 1 component out
of order x 30 min = 300 minutes.
30 + 60 (final inspection) + 60 + 50 + 300 + 30 = 530 minutes. 530 / 60 x 50 = 441.67 EUR, plus
0.36 EUR of material = **442.03 EUR**.

**Example C - a one-minute defect.** Hands-on 1 minute. 50 + 1 = 51 minutes of work is under the
minimum, so the time around the job becomes 59 minutes. The NC costs the same 175.00 EUR as
example A. This applies to 130 AEC NCs.

Other decisions:

| Decision | What is charged | Example |
|---|---|---|
| Rejection, scrap | Alert, writing, technical support, closing. No work. Plus the value of the part. | NC 16995857: 30 + 30 + 60 + 30 = 150 min = **125.00 EUR**. Part: 0 EUR, no price in the data. |
| Deleted (any decision) | Alert and writing only | NC 216123618: 30 + 30 = 60 min = **50.00 EUR** |
| Design query | Alert, writing, technical support, closing, plus 8 h of engineering at 78.16 EUR/h | NC 216733534: 125.00 + 625.28 = **750.28 EUR** |
| Exchange | Same as rework, plus the value of the swapped part | |
| Accept as is, potential NC | Alert, writing, technical support, closing | 125.00 EUR |
| No decision | Alert and writing | 50.00 EUR |

Only the rework process was described by the team. The other rows are assumptions.

### Customer returns

A customer return on AEC (45 NCs, 8,089 EUR) is in the total and is costed like any NC of its
decision: only the handling of the NC is estimated. Two ways to go further, both already built:

- `CUSTOMER_RETURN_EXTRA` in `cnq_params.py`: a flat amount added to every customer return
  (analysis, reply to the customer, logistics). It is 0 EUR until the team sets a figure.
- A `customer_return_cost` column in the NC dataset: the real amount of a return, when known. It
  replaces the estimate for that NC.

In the dashboard, the "Retours client" tab lists every return with its estimate and a field for the
real amount. Amounts typed there stay in that browser only; to make them permanent, put them in the
`customer_return_cost` column.

### Level 2, global average

The same steps, but every NC gets the average times whatever its defects: 30 minutes to write the
NC and 1 hour of work for a rework. Material is added as in level 3.

- Example A: 30 + 30 + 60 + 60 + 30 = 210 min = 175.00 EUR. Same as level 3.
- Example B: 210 min = 175.00 EUR + 0.36 EUR material = **175.36 EUR**, against 442.03 EUR at level 3.
  This is what the flat average hides: an NC with nine defects costs the same as one with one.

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
| Reject, scrap, potential NC | 252.27 EUR | assumed: creation, assessment, decision |
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

## 5. What is in the package

| File | What it is |
|---|---|
| `cnq/cnq_params.py` | Every time, rate and rule. The only file to edit when a number changes. |
| `cnq/cnq_core.py` | The calculation, in pandas. No Foundry dependency. Tested. |
| `cnq/foundry_transform.py` | Wrapper to run it as a Foundry transform. Template, not yet run in Foundry. |
| `slate/slate_queries.sql` | 18 queries for the charts. Tested in SQLite on the sample outputs. |
| `dashboard/cnq_dashboard.html` | Standalone dashboard, French / English, fully offline. One page: summary, how an NC is costed (steps, rules per decision, any real NC line by line), breakdown, customer returns, editable times, limits. |
| `dashboard/build_dashboard.py` | Rebuilds the check sheet from the output datasets. |
| `params/*.csv` | The parameters as three tables, for review. Generated from `cnq_params.py`. |
| `sample_output/*.csv` | The two output datasets computed on the v4.7 data. |
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
python tests/run_local.py fto2_nc_v4_7.csv fto2_parsed_defects_v4_7.csv nc_with_counts.csv
python tests/test_queries.py
python dashboard/build_dashboard.py
node tests/test_dashboard.js
```

The third file of the first command is a stopgap: it supplies the columns the v4.7 NC export does
not have yet.

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
| `perimetre` | flags customer returns | yes |
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
| ASSUMED | Not confirmed by anyone at AEC |

Nothing is measured. Two research reports looked for published benchmarks and found none that
confirms or rejects any of these times. The only way to firm them up is to time them on the floor.

## 9. Known gaps, most important first

1. **Parts have no price.** 97 AEC NCs are rejects, scraps or exchanges, and the lost part counts
   as 0 EUR. To fix: add a `part_value` column (the SAP price of the rejected part, not of the
   assembly). The calculation already uses it when present.
2. **Customer returns are under-estimated.** Only the handling of the NC is counted. Analysis,
   reply to the customer, transport and penalties are not, until the flat extra or the real
   amounts are filled in (section 3).
3. **Connection errors rest on a borrowed time.** Swapped and wrong connections are the two most
   frequent defects and cost 18,375 EUR of hands-on work, all at 35 minutes from a 2021 study.
4. **57 AEC NCs are missing from the NC dataset.** They are in the Skywise export but not in the
   v4.7 NC dataset, most likely because the parser found no defect line for them. They still cost
   handling time. To fix: keep NCs with zero defect lines in the NC dataset.
5. **150 NCs have no master data** (no status, programme or date). They cannot be costed and are
   counted in the data-gap query.
6. **The class-to-time mapping is one person's judgement.** Each of the 40 parser classes was
   matched by meaning to one line of the team's code table. Someone who knows the work should
   review `params/cnq_defect_times.csv`, or the class table in the check sheet.
7. **Two material figures look too high**: 45.20 EUR for a badly positioned identification plate
   and 63.77 EUR for unfinished wiring. Together they drive about 3,500 EUR.
8. **Routing and printing defects** are open points from the team's notes (section 4).
9. **Other processes are assumptions.** Reject, exchange and design query have not been described
   by the team, and their level 1 match to the Airbus model is assumed too.
10. **One rate for everyone.** 50 EUR/h is the official France rate. Finance should supply AEC rates
   for operators, inspectors and technical support.
11. **The final-inspection flag is approximate.** The two type columns in the Skywise export often
    disagree.
12. **The Foundry wrapper has not been run.** The calculation is tested on CSV files; the
    transform file is a template. Spark cannot guess the type of an all-empty column (such as
    `sub_code` in v4.7), so the wrapper drops those.

## 10. Recommended next step: time the work

Ten classes cover most defect lines. Timing a handful of each on the floor would replace the
weakest numbers. A starting plan from the International Labour Organization table: about 5 timings
for a 35-minute job, 10 for a 10-minute job, 15 for a 3 to 5 minute job, 30 for a 1-minute job, then
let the spread of the results decide how many more are needed. Time the fixed 50 minutes around the
work separately from the hands-on part.

## 11. Why level 3 differs from the Excel workbook

The workbook `CNQ_model_AEC_2026.xlsx` gave 148,200 EUR on the earlier export. Level 3 gives
134,206 EUR. The differences:

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
