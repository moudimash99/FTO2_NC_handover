# FTO2 NC dashboard for Skywise: install pack (parser v4.8)

Follow the handover doc "Skywise NC Dashboard Handover" step by step. This pack holds the files it refers to.

| Folder | Files | Used in |
| --- | --- | --- |
| 1_pipeline | nc_defect_parser.py, fto2_logic.py, fto2_transforms.py, code_workbook_fallback.py | Step 1 |
| 2_slate_queries | q01 to q08, one Slate query each (11 files) | Step 4 |
| 3_check | valeurs_attendues.csv (from the SAP extract of 5 Jan to 6 Jul 2026) | Step 6 |
| 4_reference | sous_categories.csv: each sub-category with its Pareto category, RCA name and minor flag | Reading the charts |

Everything specific to your Skywise is in the EDIT block at the top of `1_pipeline/fto2_logic.py`:
dataset paths, SAP column names, the plant code, the period, the line names and the RCA names shown on the charts.
The Slate queries only need the name of the Postgres sync on their FROM lines, if yours differs from
`foundry_sync.fto2_defects` / `foundry_sync.fto2_nc`.

The pipeline builds two datasets:
- `fto2_defects`: one row per defect, with Pareto category (`groupe`), sub-category, RCA, minor flag, line, scope (`perimetre`) and the NC fields.
- `fto2_nc`: one row per NC, with its number of defects and defects per Pareto category.

Pareto categories: MEO Câblage · Erreur Branchement · Élément Manquant · Élément Endommagé · Déverrouillage ·
Grounding/Bonding · Kitting Factory · FOD · Autre (the last three shown aside, in grey).
Scope (`perimetre`): FTO2 · Retour client (raised outside FTO2, FTO2 in `liability`) · Fournisseur · Supprimée · Hors périmètre (raised outside FTO2, FTO2 not liable) · Autre.
Minor (`mineur`): a missing tyrap, frette or ficelle, or a missing cap, cerise or plug.
Top 5 per line: the 5 biggest RCA, plus Déverrouillage every time.
