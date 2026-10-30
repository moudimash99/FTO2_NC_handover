# Tableau Elizabeth in Slate

The NC count and seven families (Câbles, Branchement, Déverrouillage, Élément Endommagé, Élément Manquant, MEO Facteur
humain, Autres), each NC in one family only: figures, a Pareto, and week by week against a threshold (by default a family
over 10 % of the week's NCs). Its own Slate app, set up as the MFT: two queries, one code sandbox, its state.

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

Expected (data of 28 September 2026): all lines, Série, 4 weeks S36 to S39: **118 NC: Câbles 31, Élément Endommagé 28,
Branchement 12, MEO Facteur humain 12, Élément Manquant 3, Déverrouillage 2, Autres 30**. All of 2026 (Série, 910 NC): Câbles
282, Élément Endommagé 223, MEO 123, Branchement 103, Autres 90, Élément Manquant 50, Déverrouillage 39.

## What the page counts

- **Scope**: NCs raised at FTO2 (plant FTO2 or FT02) created in 2026, as the MFT page; line, production type (Série by
  default) and period (a week, 4, 13 or 26 weeks to the week chosen) in the page.
- **Families, in NCs, each NC in one only** (the first that fits, in this order), so the shares add up to 100 %:
  1. **Câbles**: any cable problem, whatever its category: a cable to remake or resupply (the `cable` column), a damaged or
     cut cable (cause Câble Endommagé, sub-codes Q11-014, Q11-001), a missing cable (T01), a cable of the wrong length
     (Q12-003), the sub-categories "Câble à refaire (ligne)", "Dommage – câble" and "Amont · Câble" (cable delivered wrong:
     printing, length, gauge), a missing item or a printing defect when its text speaks of a cable; every NC of the cable
     shop (NC type CABLES); and an NC with no text whose title speaks of a cable (câble, fil, faisceau, harnais, toron).
  2. **Branchement** (category Erreur Branchement), 3. **Déverrouillage**, 4. **Élément Endommagé**, 5. **Élément
     Manquant**, 6. **MEO Facteur humain**: an NC with a defect line of that category.
  7. **Autres**: the rest (Grounding/Bonding, Kitting Factory, FOD, Autre; the NCs no rule places).
  Because each NC counts once, an NC with a cable defect and an unlocked contact is in Câbles only: Déverrouillage keeps
  39 NCs in 2026 (94 counted on their own).
- **The A400M**: Skywise gives no long text for its NCs, so they have no defect line; each is placed by its title (Skywise's
  short description, the dataset's `title`) with keywords per family (in the template, `FAM`). 2026 Série: Câbles 38, MEO 11,
  Élément Manquant 3, Élément Endommagé 2, Autres 35 (titles such as "RETOUCHES TEST MSN 162" say nothing of the defect).
- **New NCs**: until the periodic AI pass labels them, a new NC's defect lines carry the parser's labels (`label_src`
  "parser"): category, cause and cable flag as usual, but no precise sub-code (a parent code such as "Q11 (non précisé)").
  The rules do not need one: the cable flag, the cable sub-categories, the cause, the text, the NC type and the title are
  there either way. Checked by running the page on the whole year relabelled as the parser alone labels it: Câbles 291
  instead of 282, the other families within a few NCs (the parser and the stored labels agree on the cable flag for 98.8 %
  of lines, on the category for 93.4 %).
- A family pressed in the Pareto shows what it is made of (for Câbles, why each NC is there) and the table lists its NCs.
- **Threshold**: by default a share, 10 %: a family's week is red when the family has more than 10 % of that week's NCs
  (read on working weeks only: a closure week's few NCs make shares that mean nothing). The value can be changed in the page,
  and the switch beside it turns the threshold into a count of NCs per week (then the NC count has one too). Both are kept
  in the browser when it allows it.
- **Comparison**: per week, against as many working weeks before the period as it has (4 at least), without closure weeks
  or low-production weeks (summer), the weeks named; as the MFT page.

`preview_local_only.html` opens on a laptop with a frozen copy of the data: never paste it into Slate. The same page with
its own copy of the data: `03_reports/FTO2_Elizabeth.html`.

## Build

```bash
python3 -I 07_scripts/elizabeth/build_elizabeth.py
```

From `07_scripts/elizabeth/elizabeth_template.html` (its styles are the MFT page's, copied at the build) and the two tables
in `05_outputs`. Checked here: every NC's family and reason against a count made apart in Python (988 NCs, all the same);
the page and its Slate version (in a sandboxed frame, as Slate runs it) give the same result, with no error; the same tables
typed as Slate gives them (numbers, true / false, nulls) give the same families; the parser-only labels as above.
`window.ELZ_CHECK()` in the browser console lists each NC's family and reason.
