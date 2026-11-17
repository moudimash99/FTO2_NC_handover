# Settings (config): how they work and how to fill them

Everything about the dashboard that someone may want to change without touching the code is a small table in the folder
`data/config/`, next to the notebook in the Code Workspace. There are 45 tables, in four groups. This guide explains what is
in them, how they are built, how to fill them in, and how the code reads them.

The three guides: `config.md` (the settings tables; in the Code Workspace also as `data/config/README.md`), `logic.md` (the
notebook's code) and `front_end.md` (the pages' code); these two are also in `notebook_kit/`.

**Contents**

1. [The basics: what a table looks like](#1-the-basics-what-a-table-looks-like)
2. [The four groups: who should edit what](#2-the-four-groups-who-should-edit-what)
3. [After a change](#3-after-a-change)
4. [The five kinds of tables](#4-the-five-kinds-of-tables)
5. [Every table, one by one](#5-every-table-one-by-one)
6. [Common tasks](#6-common-tasks)
7. [How the code reads the tables](#7-how-the-code-reads-the-tables)

---

## 1. The basics: what a table looks like

Each table is a text file ending in `.csv`. It opens in Excel like a spreadsheet: the first row holds the column names, and
each row below is one entry. Inside the file, the columns are separated by a semicolon (`;`).

**Rules for filling them in**

- **Keep the first row** (the column names) exactly as it is. The code finds the columns by their names.
- **Don't type a `;` inside a cell.** The semicolon separates the columns, so one typed in a text shifts everything after it.
  If the run stops with "line N has X columns, the header has Y", that is the cause.
- **Dates:** year-month-day, e.g. `2026-01-01`. A month alone: `2026-01`.
- **Decimals:** write them with a dot, e.g. `0.25`. (The cost tables also accept a comma.)
- **Several values in one cell:** separate them with `|`, e.g. `FTO2|FT02`. Any one of them is enough.
- **Yes / no settings:** write `oui` or `non`.
- **Saving from Excel:** "CSV UTF-8 (separated by semicolons)", so accents and the `;` stay right. If Excel offers to keep the
  format, say yes.
- A column named `commentaire`, `description`, `note` or `exemple` is for people. The code ignores it: write anything there
  that helps the next person.

The file `lisez_moi.csv` (in French) lists every table, its group, what it changes, who should edit it and which part of the
code reads it.

## 2. The four groups: who should edit what

The number at the start of each file name says which group the table is in.

| Group | Who edits | What these tables hold |
|---|---|---|
| **0** data | Nobody by hand | What comes from the files the team downloads (the production plan, the cable requests) and history (the 2025 deliveries, the 2026 EqMSN sheet). To update them, save a new download in `data/` (see "Files saved as they are downloaded" below). |
| **1** the manager's settings | The person in charge of the dashboard | The few things that are decided, not computed: the year followed, the target, what the pages show at opening, the hourly rates and the minutes of the cost, the shutdown days, the part prices, the MFT actions. Six short tables. |
| **2** rules and names | The developer (or someone careful with this guide) | How things are counted and named: what counts as REC, which product an NC belongs to, the categories, the colours, where the data comes from. The figures change: check the dashboard before and after. |
| **3** expert | The developer | Minutes per type of defect in the cost model, the alarm statistics, the official sub-code list. Change only with the model behind it in mind. |

**Two name / value tables are in two parts.** `1_parametres.csv` and `1_reglages_pages.csv` hold the lines the manager
changes; `2_parametres.csv` and `2_reglages_pages.csv` hold the technical lines of the same kind. The code asks for a line
by its name and finds it in either part; a line written in both stops the run with a message.

### Files saved as they are downloaded

With the Fusion spreadsheet, the production plan, the cable tracker, the GPS register and the Test list are pasted whole
into their sheets (*Production plan*, *Cable tracker*, *GPS register*, *Test list*), as they are: the update finds each
header row itself, says on which row in its first lines, and keeps the previous table, loudly, when it cannot
(`fto2/fusion.py`). The plan's sheet is read as the newest export, dated by a date written above its header, else by the
day of the run. Without those sheets (a notebook whose Data panel does not have them), the files below are read.

Two things are not typed into a table at all. The team downloads a file and saves it in `data/`, beside the station mapping,
the GPS register and the Test list; the next run reads it (`notebook_kit/fto2/downloads.py`).

| What | The file to save in `data/` | How it is read |
|---|---|---|
| The production plan | Each export of the **Tableau Avances / Retards**, as CSV, named `Avances_Retards...csv` | **Every** export in the folder is read, oldest first: keep the earlier ones. An aircraft takes its row from the newest export that lists it; an aircraft delivered before a new export, and no longer listed in it, keeps its last row (this is how the plan remembers the year before, whose deliveries the targets start from); a row that left the export before its delivery has left the plan. |
| The cable requests | The export of the **cable team's tracker**, as CSV, with `cables` in its name | The newest export replaces the list. |

The day of a download is the date at the end of its name when it has one (`Avances_Retards_2026-11-03.csv`), else the day
the file was saved. The names the run looks for are two lines of `2_sources.csv` (`exports_plan`, `suivi_cables`), with
`*` for any text. The tables `0_plan_msn.csv` and `0_demandes_cables.csv` hold the plan and the requests as they stood when
the downloads started to be saved in `data/`: the plan table is read as one more export, at its own date; the cable table
is used only when no tracker export is there. The last lines of each run say which files were read.

## 3. After a change

1. Save the table.
2. Run the notebook.
3. If a table is badly filled, the run stops and says **which file, which line, and what to fix**. For example:
   "2_regle_phase.csv line 4: test 'contien' is not one of contient, mot, commence_par...".
4. Look at the dashboard: the change should show where you expect it, and nowhere else.

For a level 2 or 3 change, note the dashboard's headline figures before the change, and compare after: only what you
expected should move.

## 4. The five kinds of tables

Almost every table is one of these five kinds. Once you know them, every table reads the same way.

### 4.1 Lists: one row per thing

Example: `1_calendrier_production.csv`, one row per shutdown, with its dates and its weight. Add a row to add a thing,
delete a row to remove it. Each column holds one piece of information about that thing.

### 4.2 Name and value: one setting per row

Example: `1_cout_parametres.csv`.

| nom | valeur | unite | description |
|---|---|---|---|
| taux_production | 123 | EUR/h | Production: operator alert, preparation, work... |

The code looks for each setting by its **name** (`nom`): never change a name, never delete a row. Only change the **value**
(`valeur`). The description says what the value means.

### 4.3 Rules: how the code decides something about each NC

Example: `2_regle_phase.csv`, which decides whether an NC is SERIE, REC or FTI.

| ordre | resultat | colonne | test | valeur | commentaire |
|---|---|---|---|---|---|
| 1 | FTI | constituent_assembly | commence_par | WY\|WA | FTI assembly, e.g. WA999 |
| 2 | REC | workflow_list | mot | REC | The word REC in the workflow |
| 3 | REC | workflow_list | contient | -CRE\|-PNC\|A30-REJ-PVU2 | Known REC workflows |
| 99 | SERIE | | toujours | | Everything else |

**How to read it, in plain words:** "If the assembly starts with WY or WA, it's FTI. Otherwise, if the workflow has the word
REC, it's REC. Otherwise, if the workflow contains -CRE, -PNC or A30-REJ-PVU2, it's REC. Otherwise, it's SERIE."

The columns:

- **ordre**: the order in which rules are tried, smallest first. **The first rule that matches gives the result**; the others
  are not looked at.
- **resultat**: what the NC gets when the rule matches.
- **colonne**: which piece of NC data the rule looks at (a column of the Skywise NC data). Two columns joined by ` + ` are
  read as one text, e.g. `description_short + article_version_description`.
- **test**: how it looks (list below).
- **valeur**: what it looks for. Several values separated by `|`: any one is enough.
- **commentaire**: a note for people.

**Several rows with the same `ordre` form one rule: all of them must be true.** In `2_regle_perimetre.csv`, two rows have
ordre 1: the NC is a customer return only if its type is "NC Retour client" **and** FTO2 is in its liability.

**The last rule** has the test `toujours` (always) and no column: it is the default, for every NC no other rule caught. Every
rule table needs one.

**The tests** (upper and lower case are treated the same):

| Test | Means | Example |
|---|---|---|
| `contient` | the text contains one of the values | `-CRE` matches "REW-CRE-01" |
| `ne_contient_pas` | the text contains none of them | |
| `mot` | contains one as a whole word | `REC` matches "REW-REC" but not "RECEPTION" |
| `commence_par` | starts with one of them | `WY\|WA` matches "WA999" |
| `ne_commence_pas_par` | starts with none of them | |
| `egal` | is exactly one of them (spaces at the ends ignored) | |
| `different` | is none of them | |
| `vide` / `non_vide` | the cell is empty / not empty | |
| `toujours` | always true: the default rule, last | |
| `regex` / `pas_regex` | expert: a "regular expression" (a search pattern) is found / not found | `32\d` = "32" then a digit |
| `extraire` | expert: takes a piece of the text, which becomes the result when `resultat` is `{extrait}` | finds "740VU" in the article |

### 4.4 Translations: one value becomes another

Example: `2_produits_plan.csv`, which maps the product name on an NC to its name in the production plan
(`MIP A350` → `MIP`). The left column is what is found, the right column what it becomes. One row per value.

### 4.5 Data tables (group 0)

The tables whose name starts with `0_` are not settings: they hold data. Two are the starting point of what the run now
reads from the downloads saved in `data/` (the production plan, the cable requests: section 2); the others are history (the
2025 deliveries, the 2026 EqMSN sheet). Nobody edits them. A mistake in the plan or in the cable requests is corrected
where it was made, in the Tableau Avances / Retards or in the cable tracker, and a new download is saved.

---

## 5. Every table, one by one

The tables are grouped by subject. For each: what it does, what a row is, and how to fill it.

### Which NCs count, and how each one is labelled (rule tables, group 2)

All of these are **rule tables** (section 4.3). They look at the columns of the Skywise NC data.

| Table | Decides | Results |
|---|---|---|
| `2_regle_exclusion.csv` | Which NCs are left out entirely (ERMA's NCs, NCs deleted at another plant) | `exclure` or `garder` (keep) |
| `2_regle_phase.csv` | The production type | `SERIE`, `REC`, `FTI` |
| `2_regle_ligne.csv` | The aircraft line, from the programme | `A350`, `A330`, `A400M`, `A320`, else the programme's own name, else `Autre` |
| `2_regle_perimetre.csv` | Where the NC was raised | `serie` (at FTO2), `client` (customer return, FTO2 liable), `autre` |
| `2_regle_origine.csv` | Who opened it | `Test` or `Qualite` |
| `2_regle_type_nc.csv` | The NC type (where it was found), in order of priority | `CONTROLE FINAL`, `CABLES`, `TEST`, `NC Interne`, `NC Fournisseur`, `NC Retour client`... |
| `2_regle_produit.csv` | The product, from the article and then the station | `MIP A350`, `PTVU`, `300VU`... or the cabinet number found (`{extrait}`), else `Other` |
| `2_regle_responsabilite.csv` | The three "Responsabilité" boxes of the dashboard | `f` (FTO2), `s` (a supplier), `o` (others) |

Two rules of thumb: put special cases **before** general ones (a smaller `ordre`), and keep the `toujours` rule last.

### Products and the production plan

| Table | Group | What a row is | How to fill it |
|---|---|---|---|
| `0_plan_msn.csv` | 0 | One aircraft (MSN) and product: line, product, MSN, rank, then the **planned** (`prevu_`) and **real** (`reel_`) date of the 8 milestones (impression, enclenchement, SE, méca, inté, test, qualité, départ OTA), the date of the export it comes from | Not edited. The plan as it stood on 3 November 2026; the run adds every export of the Tableau Avances / Retards saved in `data/` (section 2). |
| `0_eqmsn_mois.csv` | 0 | One product and version (`std` = Standard sheet, `adj` = Adjusted sheet): its EqMSN for each month of 2026, the export date, the first forecast month | Not edited. The pages count the volume from the production plan (each aircraft spread over the days the plant works); this table only adds the EqMSN sheet's two versions while its months are those of the year followed. For another year it is ignored. |
| `1_calendrier_production.csv` | 1 | A period of shutdown or slow production: start, end, **weight** (0 = closed, 0.5 = half a normal week), reason | Add a row for each new shutdown or bridge day, each year. It changes the MSN volume of the months and weeks concerned. Dates as `2026-12-24` or `24/12/2026`. |
| `0_livraisons_2025.csv` | 0 | One product delivered in 2025: its name, its name in the plan, its line, the count per month of 2025, the total | Not edited. The basis of the 2026 targets. For a later comparison year no such table is needed: the deliveries are counted in the production plan (see "The year" below). A table `0_livraisons_<year>.csv` of the same shape is used instead when it exists. |
| `2_produits_plan.csv` | 2 | Product name on the NCs → product name in the plan (`produit_eqmsn`); `a_confirmer` = oui if not yet confirmed | A new product: add its row. |
| `2_produits_noms_plan.csv` | 2 | Name in the plan → name shown (`MIP` → `MIP A350`) | |
| `2_produits_alias.csv` | 2 | NCs whose product is not in the plan, sent to the plan product they belong to: line, product pattern, optional station pattern, target product | Patterns are regular expressions (expert): `^\d{3}VU$` = three digits then VU. |

### The cost of non-quality

How the cost works, simply: each NC goes through up to six **steps** (alert, writing, technical support, preparation, hands-on
work, re-check). Each step takes some **minutes**, paid at the **hourly rate** of whoever does it. Engineering hours (design
queries), material, and the price of a rejected, scrapped or exchanged part are added.

| Table | Group | What it holds | How to fill it |
|---|---|---|---|
| `1_cout_parametres.csv` | 1 | Name / value: the **hourly rates** (production 123, quality 107, ME 76, engineering 78.16) and the **minutes of each step** (alert 41, writing 30, at final inspection 60, support 60, preparation 50, minimum work 60, re-check 30...), the **logistics minutes** added when the work comes from the rework order (15), the factor for internal NCs, the flat amount for a customer return | Change the value only, with a dot or a comma. A value below zero stops the run. |
| `2_cout_decisions.csv` | 2 | One decision (RWK rework, REJ reject, SCR scrap, EXC exchange, DQN design query...): `1` or `0` for each step it charges (alerte, redaction, support, travail, recontrole), its engineering hours, `valeur_piece` (1 = the part's value counts), its label, and `base` (where the rule comes from) | A new decision code: add a row. |
| `2_cout_qui_fait_quoi.csv` | 2 | Each step → who does it (`production`, `qualite`, `me`), so which rate it is paid at | |
| `3_cout_temps_defauts.csv` | 3 | One **type of defect**: minutes of work, material in euros, English name, reference sub-code, and `base` (where the time comes from). A type can instead be **computed from another** (`calcule_depuis`) × a factor (`facteur`): "wrong reference" = 2 × "missing" | Expert: these minutes drive most of the cost. |
| `1_prix_pieces.csv` | 1 | **The price of each part**: one row per material (the material number the NC names), its description and its unit price. The value of a rejected, scrapped or exchanged part = price × quantity | Add a row per material, or paste an export (the material and price columns are recognised by their names). Empty price = not priced yet. The materials still without a price are listed at each run in `fto2_parts_to_price.csv`. Guide: `part_prices.md`. |
| `3_cout_airbus.csv` | 3 | Airbus standard cost per decision (level 1 of the cost) | Only if the official standard changes. |
| `3_cout_avance.csv` | 3 | Name / value: model version, which NC types are "final inspection" or "internal", the prefixes of a rework order, the connection-error classes, whether the planned time of rework orders and the declared time of aléas replace the model's times (`oui`/`non`), the time window that links an aléa to an NC | Expert. |
| `3_cout_ordres_operations.csv` | 3 | How to read a rework order's operations: a pattern in the operation text → which step it counts as (preparation or work) | Expert. |

### Categories, causes and sub-codes (what the defects are called)

The defects are sorted in three layers: **category** (e.g. Erreur Branchement) → **cause** (e.g. Inversion) → **sub-code**
(the official code, e.g. T04).

| Table | Group | What a row is | How to fill it |
|---|---|---|---|
| `2_categories.csv` | 2 | One category: its order on the charts, its colour (1 to 9), `a_part` = oui to show it aside, with no colour | Change the order or the colour. |
| `2_causes_noms.csv` | 2 | A cause code (from the text reader) → the name shown | **Don't change the code** (left column); the name can change. |
| `2_causes_definitions.csv` | 2 | One cause: its category, its definition in French and in English (the Définitions tab) | Improve a definition freely. |
| `3_sous_categories.csv` | 3 | One sub-category: its category, its cause, minor or not, its official sub-codes | Expert. |
| `3_souscodes.csv` | 3 | The official sub-codes: sub-category, group, cause, description, severity... | Only when the official list changes. |
| `3_souscodes_fr.csv` | 3 | Each sub-code's French description | |
| `3_a400m_titres.csv` | 3 | A400M NCs have no long text, so their sub-code is read from the title: a pattern in the title → sub-code, cable or not, an example. The first pattern found wins; an empty sub-code means "not a defect" | Expert: patterns are regular expressions. |
| `2_decisions.csv` | 2 | A decision code → its label | |
| `2_libelles_lieu_detection.csv` | 2 | A "where found" value → its English label | |

### The pages

| Table | Group | What it holds |
|---|---|---|
| `1_reglages_pages.csv` | 1 | Name / value, the manager's part. The **target** (`objectif_baisse`: 0.25, 0,25 or 25 % all mean the comparison year's rate minus 25 %; the pages' texts show the percentage written here), the **filters at opening** (`defaut_phase`: SERIE, REC, FTI or empty; `defaut_responsabilite`: letters among f, s, o; `defaut_periode`: ytd, m1, m3, m6, m12 or all), the **MFT action target** (minus 30 %, held 4 weeks). Each value is checked: a mistake stops the run and says what to write. |
| `2_reglages_pages.csv` | 2 | Name / value, the technical part: what counts as a shutdown week, the minimum MSN volume for a rate, the sub-codes that mean "not specified", the MFT page's thresholds ("what goes up / down", recurring FIN, reference windows). |
| `2_lignes.csv` | 2 | Each line's colour (1 to 4). |
| `3_alarmes.csv` | 3 | Name / value: the bell's statistics. How many recent weeks are compared (4) with how many weeks before (12), the thresholds for a minor or major alarm, slow rises, odd aircraft, how many alarms are shown (5). |

### MFT actions and cables

| Table | Group | What a row is | How to fill it |
|---|---|---|---|
| `1_actions_mft.csv` | 1 | One MFT action: `id` (its own, never reused), line, title (French and English), **the problem it targets** (`niveau` + `valeurs`), analysis and action owners, dates, status, expected benefit, where it comes from | To add an action: one row. `niveau` says what kind of problem: `cat` a category, `rca` a cause, `sub` a sub-category, `code` a sub-code, `where` a place of detection (the French words are read too: `catégorie`, `cause`, `sous-catégorie`, `sous-code`, `lieu`). `valeurs`: the names exactly as on the dashboard, several separated by `\|`. Dates as `2026-07-01` or `01/07/2026`. An action without `niveau` shows on the MFT page with no result followed. The run checks the ids, the `niveau` and the dates. |
| `0_demandes_cables.csv` | 0 | One cable request of the cables team: week, date, NC, programme, MSN, reason, imputation, origin, proposed cause, cables, comment | Not edited. The requests as they stood in November 2026; the run reads the newest export of the cable tracker saved in `data/` instead (section 2). |
| `2_cables_origines.csv` | 2 | An imputation of the cable tracker → the origin shown (`(autre)` = anything else) | Read each time the tracker's export is read. A new imputation in the tracker: add its row. |
| `2_regle_cause_cable.csv` | 2 | Rule table (section 4.3): the proposed cause of a cable request, from keywords in its analysis comment | Read each time the tracker's export is read. |

### General settings and data sources

| Table | Group | What it holds |
|---|---|---|
| `1_parametres.csv` | 1 | Name / value, the manager's part: **the year followed** (`annee`) and the comparison year (`annee_comparaison`, empty = the year before). See "The year" below. |
| `2_parametres.csv` | 2 | Name / value, the technical part: the plant followed (`FTO2`) and its codes (`FTO2\|FT02`), whether the old Slate outputs are still written (`oui` while the old app is used), a limit on the number of NCs (empty = all). |
| `2_sources.csv` | 2 | Name / value: the names of the Skywise datasets (as in the notebook's Data panel) and of the files in `data/` (stations, GPS register, Test list, exports of the production plan, cable tracker), with the lines to skip and the column names in those files. Change it when a dataset or a file is renamed. In the name of a list, `{annee}` stands for the year followed; in the name of a download, `*` stands for any text. |

### The year

The pages follow **one calendar year**: the NCs created that year, its production plan, its targets. The year is one line
of `1_parametres.csv`, left **empty**: the year followed is then the current year, and it changes by itself on 1 January.
Write a year there only to look back at a past year:

```
annee;
```

Everything tied to the year follows from that line, with nothing else to change:

| What | How it follows the year |
|---|---|
| The NCs shown | Created from 1 January to 31 December of the year (plus the NCs of the GPS register and the Test list dated that year) |
| The production volume | The aircraft of the production plan (the exports saved in `data/`), counted in the months and the weeks of the year |
| The comparison year | The year before (or the one written in `annee_comparaison`): its NCs are read in Skywise at each run |
| The comparison year's deliveries | `0_livraisons_<year>.csv` when that table exists (2025), else counted in the production plan: a product is delivered in the month of its Départ OTA |
| The targets | The comparison year's rate, minus the percentage of `objectif_baisse`, times the year's production |
| The bell | Its weeks are the weeks of the year; it needs 16 weeks of the year before it can compare |
| Every text of the pages | The two years and the target's percentage are written in from the settings |

**At the start of a new year** (each January) the year changes by itself. What still needs a hand:

1. Nothing to write on the line `annee` (leave it empty).
2. Save a fresh export of the Tableau Avances / Retards in `data/`, **beside the earlier ones** (they give last year's
   deliveries: never delete them).
3. Add the new year's shutdowns to `1_calendrier_production.csv`.
4. Save the new year's GPS register in `data/`. Its name is written in `2_sources.csv` with `{annee}` in place of the year
   (`GPS NC INT_SERIE ELEC {annee} - NC REGISTRE.csv`), so the 2027 file is found by itself if it is named as the 2026 one.
   The Test list keeps its name.
5. Run the notebook. If a list is missing, its last lines say which file it looked for.

When a year is written on the line, the pages keep showing that year, complete, and the notebook says so at the end of
each run once that year is over.

---

## 6. Common tasks

| I want to... | Table | What to do |
|---|---|---|
| Count a new kind of REC | `2_regle_phase.csv` | Add the workflow text to the `valeur` of a REC row (`-CRE\|-PNC\|-RCX`), or add a row before the `99` rule. |
| Price the rejected parts | `1_prix_pieces.csv` | One row per material: `materiel;designation;prix_unitaire_eur`. What is left to price: `fto2_parts_to_price.csv`, written at each run. |
| Change an hourly rate | `1_cout_parametres.csv` | Change `valeur` of `taux_production`, `taux_qualite` or `taux_me`. |
| Change the target | `1_reglages_pages.csv` | `objectif_baisse`: 0.30 for −30 %. |
| Start a new year | — | The year changes by itself; then the production plan, the shutdowns and the GPS register (see "The year"). |
| Add a product | `2_regle_produit.csv`, then `2_produits_plan.csv` | A rule that recognises it, then its name in the plan. |
| Update the production plan | a file in `data/` | Download the Tableau Avances / Retards as CSV and save it in `data/` beside the earlier exports. |
| Update the cable requests | a file in `data/` | Download the cable team's tracker as CSV and save it in `data/`. |
| Add a shutdown | `1_calendrier_production.csv` | Start, end, weight 0 (closed) or 0.5 (half), reason. |
| Add an MFT action | `1_actions_mft.csv` | One row with its own `id` (see above). It appears on the MFT page for everyone at the next notebook run. |
| Change what the dashboard shows at opening | `1_reglages_pages.csv` | `defaut_phase`, `defaut_responsabilite`, `defaut_periode`. |
| Change a category's colour or order | `2_categories.csv` | `couleur` (1 to 9), `ordre`. |
| Rename a dataset Skywise gives us | `2_sources.csv` | The new name in `valeur`. |

---

## 7. How the code reads the tables

Nothing is copied from a table into the code: the notebook reads every table **each time it runs**. That is why a change
needs only a new run.

**Who reads what.** `lisez_moi.csv`, column `lu_par`, names the code file that reads each table. In short:

| Tables | Read by (in `notebook_kit/fto2/`) | What happens to them |
|---|---|---|
| `2_regle_*.csv` (the rules) | `selection.py`, `core.py`, `parser/fto2_logic.py`, through `rules.py` | Applied to every NC to give it a label (phase, line, product, type, scope...) |
| `1_cout_parametres.csv`, `2_cout_*.csv`, `3_cout_*.csv` (the cost) | `cost/params.py` | Turned into the cost model's settings, used by `cost/model.py` |
| `1_parametres.csv`, `2_parametres.csv`, `2_sources.csv` | `skywise.py`, `config.py`, `manual_lists.py`, `downloads.py` | Which plant, which year (`config.year`, `config.comparison_year`), which datasets and files to read |
| `1_prix_pieces.csv` (part prices) | `cost/parts.py` | Each NC's material (read from the NC data) gets its unit price; the cost model adds price × quantity for the decisions that count the part |
| the downloads saved in `data/` (exports of the production plan, cable tracker) with `0_plan_msn.csv`, `0_demandes_cables.csv`, `2_cables_origines.csv`, `2_regle_cause_cable.csv` | `downloads.py` | Turned into the production plan and the cable requests |
| the other `0_` and `1_` tables (deliveries, shutdowns, MFT actions) and the page settings (`1_reglages_pages.csv`, `2_reglages_pages.csv`, `2_categories.csv`, `2_lignes.csv`, `3_alarmes.csv`) | `reference.py` | Packed with the plan and the requests into the table `fto2_dash_ref`, which the pages read |
| categories, causes, sub-codes | `reference.py`, `core.py`, `parser/fto2_logic.py` | Names and definitions shown on the pages, official sub-codes of the defect lines |

So the pages never read `data/config/` themselves: they get the settings they need through `fto2_dash_ref`, rewritten at
each run.

**The checks before anything is computed** (`notebook_kit/fto2/config.py`):

- the table exists and is not empty;
- every line has as many `;` columns as the first row ("line N has X columns, the header has Y");
- the columns a table must have are all there ("the column(s) X are missing");
- a name-and-value setting that the code asks for exists ("the line 'X' is missing"), and is in one part only;
- `oui` / `non` settings hold `oui` or `non`;
- the manager's values are of the right kind: a year has four digits, a share is between 0 and 1 (or a percentage), a
  filter at opening is one of its choices, a rate is not negative, an MFT action has its own id, a known `niveau` and
  readable dates. Each message names the table, the line and what to write.

**A settings folder made before November 2026** holds some tables under their former names (`1_plan_msn.csv`,
`2_cout_parametres.csv`...) and the manager's lines inside `2_parametres.csv` and `2_reglages_pages.csv`. It still works:
a table that is not found under its name is taken under its former one (`config.path`).

**The checks of a rule table** (`notebook_kit/fto2/rules.py`, function `check`): `ordre` is a number, the test is one of the
list and has a value when it needs one, the column exists in the NC data, a regular expression is valid, `resultat` is not
empty, and there is a default rule (`toujours`). Every problem
is reported with the file and the line, in plain words.

**How a rule table is applied** (`rules.py`, function `apply`): for each NC, the rules are tried in `ordre`; the rows of one
rule are combined (all must be true); the first rule that holds gives the result; the `toujours` rule gives the default. The
same function serves every rule table, so all of them behave the same way.

**Settings with several values** (`FTO2|FT02`, `7=0.6|8=0.6`) are split on `|` by `config.parameter_list`; the cost tables
and `1_prix_pieces.csv` accept a comma or a dot for decimals (`cost/params.py`, `cost/parts.py`).

**The part prices** (`cost/parts.py`) are checked too: a price that isn't a number stops the run with "1_prix_pieces.csv:
'…' is not a price (line N)", and a list without a recognisable material or price column says which columns it found.
Without the table, no part is priced. The full guide to that table: `part_prices.md`.

