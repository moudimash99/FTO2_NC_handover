# Tableau Elizabeth in Slate

The NC count and three families (Branchement, Déverrouillage, Câbles): figures, a Pareto, and week by week against a
threshold (by default a family over 10 % of the week's NCs). Its own Slate app, set up as the MFT: two queries, one code sandbox, its state.

## Setup (in a new Slate app)

1. **Two queries** on the Postgres source the dashboard uses (`postgate-airbus-2`):
   - `q_fto2_nc` with the text of `q_fto2_nc.sql` (dataset `fto2_dash_nc`),
   - `q_fto2_def` with the text of `q_fto2_def.sql` (dataset `fto2_dash_defects`).
2. **One Code Sandbox**, full width, about 1,400 px high. Paste `fto2_elizabeth.css` into its CSS tab, `fto2_elizabeth.html`
   into its HTML tab, `fto2_elizabeth.js` into its JS tab (or copy each part of `FTO2_Elizabeth_Slate.html`).
3. **Its state**: the content of `state.json`:

   ```json
   { "nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}" }
   ```

Expected (data of 28 September 2026): all lines, Série, 4 weeks S36 to S39: **118 NC; Branchement 13, Déverrouillage 8,
Câbles 25**; over 10 % of the week's NCs: Branchement in S36, S37, S39; Déverrouillage in S36, S37; Câbles in S36, S37, S39.

## What the page counts

- **Scope**: NCs raised at FTO2 (plant FTO2 or FT02) created in 2026, as the MFT page; line, production type (Série by
  default) and period (a week, 4, 13 or 26 weeks to the week chosen) in the page.
- **Families, in NCs**: an NC counts once in a family when one of its defect lines belongs to it. Branchement: category
  "Erreur Branchement" (inversions, wrong pins, not connected). Déverrouillage: category "Déverrouillage". Câbles: a cable
  defect, the cable itself to remake or resupply (the `cable` column, the dashboard's "Défauts câble"). An NC can be in
  several families.
- **Threshold**: by default a share, 10 %: a family's week is red when the family has more than 10 % of that week's NCs
  (read on working weeks only: a closure week's few NCs make shares that mean nothing). The value can be changed in the page,
  and the switch beside it turns the threshold into a count of NCs per week (then the NC count has one too). Both are kept
  in the browser when it allows it.
- **Comparison**: per week, against as many working weeks before the period as it has (4 at least), without closure weeks
  or low-production weeks (summer), the weeks named; as the MFT page.
- A family pressed in the Pareto shows its causes and sub-codes, and the table lists its NCs.

`preview_local_only.html` opens on a laptop with a frozen copy of the data: never paste it into Slate. The same page with
its own copy of the data: `03_reports/FTO2_Elizabeth.html`.

## Build

```bash
python3 -I 07_scripts/elizabeth/build_elizabeth.py
```

From `07_scripts/elizabeth/elizabeth_template.html` (its styles are the MFT page's, copied at the build) and the two tables
in `05_outputs`. Checked here: the figures above against a count made apart in Python; the page and its Slate version
(in a sandboxed frame, as Slate runs it) give the same figures, with no error.
