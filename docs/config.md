# Settings (config): how they work and how to fill them

Everything about the dashboard that someone may want to change without touching the code is a small table in the folder
`data/config/`, next to the notebook in the Code Workspace. There are 43 tables. This guide explains what is in them, how
they are built, how to fill them in, and how the code reads them.

The three guides: `config.md` (the settings tables; in the Code Workspace also as `data/config/README.md`), `logic.md` (the
notebook's code) and `front_end.md` (the pages' code); these two are also in `notebook_kit/`.

**Contents**

1. [The basics: what a table looks like](#1-the-basics-what-a-table-looks-like)
2. [The three levels: who should edit what](#2-the-three-levels-who-should-edit-what)
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

The file `lisez_moi.csv` (in French) lists every table, its level, what it changes, who should edit it and which part of the
code reads it.

## 2. The three levels: who should edit what

The number at the start of each file name says who should edit it.

| Level | Who | What these tables hold | Risk if wrong |
|---|---|---|---|
| **1** | Anyone in the team | Facts that change over time: the production plan, the MFT actions, the cable requests, the 2025 deliveries, shutdown days. | Low: a wrong date shows a wrong date. |
| **2** | Someone careful | Rules and settings that decide **how things are counted**: what counts as REC, which product an NC belongs to, the hourly rates, the target, the colours. | Medium: the figures change. Check the dashboard before and after. |
| **3** | Someone technical | Expert tables: minutes per type of defect in the cost model, the alarm statistics, the official sub-code list. | High: change only if you understand the model behind it. |

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

Example: `1_plan_msn.csv`, one row per aircraft and product, with its dates. Add a row to add a thing, delete a row to
remove it. Each column holds one piece of information about that thing.

### 4.2 Name and value: one setting per row

Example: `2_cout_parametres.csv`.

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

### 4.5 Tables first filled from a raw file

Some level-1 tables were first filled from a raw file: the production plan (from the Avances / Retards file), the EqMSN
volumes (from the EqMSN Excel file), the cable requests (from the cables team's tracker) and the MFT actions (from the MFT
trackers). Keep them up to date by adding or correcting rows directly. They have a last column **`source`**:

- `auto`: the row came from the raw file;
- `manuel`: the row was typed or corrected by a person.

When you add or correct a row, set its `source` to `manuel`: it marks the rows a person is responsible for.

---

## 5. Every table, one by one

The tables are grouped by subject. For each: what it does, what a row is, and how to fill it.

### Which NCs count, and how each one is labelled (rule tables, level 2)

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

| Table | Level | What a row is | How to fill it |
|---|---|---|---|
| `1_plan_msn.csv` | 1 | One aircraft (MSN) and product: line, product, MSN, rank, then the **planned** (`prevu_`) and **real** (`reel_`) date of the 8 milestones (impression, enclenchement, SE, méca, inté, test, qualité, départ OTA), the export date | Add a row per new aircraft and product; correct the dates as the aircraft moves on. Set `source` = `manuel` on rows you type or correct. |
| `1_eqmsn_mois.csv` | 1 | One product and version (`std` = Standard sheet, `adj` = Adjusted sheet): its EqMSN for each month, the export date, the first forecast month | Copy the new month values from the EqMSN Excel file (both versions), update the export date and the first forecast month. |
| `1_calendrier_production.csv` | 1 | A period of shutdown or slow production: start, end, **weight** (0 = closed, 0.5 = half a normal week), reason | Add a row for each new shutdown or bridge day. It changes the MSN volume of the months and weeks concerned. |
| `1_livraisons_2025.csv` | 1 | One 2025 delivered product: its name, its name in the plan, its line, the count per month of 2025, the total | The basis of the targets. Change only if the 2025 figures were wrong. |
| `1_livraisons_2025_lignes.csv` | 1 | One line: whole MSN delivered in 2025 | Same. |
| `2_produits_plan.csv` | 2 | Product name on the NCs → product name in the plan (`produit_eqmsn`); `a_confirmer` = oui if not yet confirmed | A new product: add its row. |
| `2_produits_noms_plan.csv` | 2 | Name in the plan → name shown (`MIP` → `MIP A350`) | |
| `2_produits_alias.csv` | 2 | NCs whose product is not in the plan, sent to the plan product they belong to: line, product pattern, optional station pattern, target product | Patterns are regular expressions (expert): `^\d{3}VU$` = three digits then VU. |

### The cost of non-quality

How the cost works, simply: each NC goes through up to six **steps** (alert, writing, technical support, preparation, hands-on
work, re-check). Each step takes some **minutes**, paid at the **hourly rate** of whoever does it. Engineering hours (design
queries) and material are added.

| Table | Level | What it holds | How to fill it |
|---|---|---|---|
| `2_cout_parametres.csv` | 2 | Name / value: the **hourly rates** (production 123, quality 107, ME 76, engineering 78.16) and the **minutes of each step** (alert 41, writing 30, at final inspection 60, support 60, preparation 50, minimum work 60, re-check 30...), the factor for internal NCs, the flat amount for a customer return | Change the value only. |
| `2_cout_decisions.csv` | 2 | One decision (RWK rework, REJ reject, SCR scrap, EXC exchange, DQN design query...): `1` or `0` for each step it charges (alerte, redaction, support, travail, recontrole), its engineering hours, `valeur_piece` (1 = the part's value counts), its label, and `base` (where the rule comes from) | A new decision code: add a row. |
| `2_cout_qui_fait_quoi.csv` | 2 | Each step → who does it (`production`, `qualite`, `me`), so which rate it is paid at | |
| `3_cout_temps_defauts.csv` | 3 | One **type of defect**: minutes of work, material in euros, English name, reference sub-code, and `base` (where the time comes from). A type can instead be **computed from another** (`calcule_depuis`) × a factor (`facteur`): "wrong reference" = 2 × "missing" | Expert: these minutes drive most of the cost. |
| `1_prix_pieces.csv` | 1 | **The value of the part** on a rejection, scrap or exchange. Two kinds of row: **a reference and its unit price** (no NC): every NC whose title or text contains that reference gets that price; **an NC number and a reference** (quantity in `quantite`, 1 when empty): that NC used that part, priced by its own `prix_unitaire_eur` or else by the reference's row | Paste your price list as rows `reference;prix` (prices with a dot or a comma). For an NC whose text doesn't name the part, add a row with its NC number. References shorter than 5 characters are not searched. An NC tied by hand is not searched in the text. Only the decisions with `valeur_piece` = 1 in `2_cout_decisions.csv` count it. |
| `3_cout_airbus.csv` | 3 | Airbus standard cost per decision (level 1 of the cost) | Only if the official standard changes. |
| `3_cout_avance.csv` | 3 | Name / value: model version, which NC types are "final inspection" or "internal", the prefixes of a rework order, the connection-error classes, whether the planned time of rework orders and the declared time of aléas replace the model's times (`oui`/`non`), the time window that links an aléa to an NC | Expert. |
| `3_cout_ordres_operations.csv` | 3 | How to read a rework order's operations: a pattern in the operation text → which step it counts as (preparation or work) | Expert. |

### Categories, causes and sub-codes (what the defects are called)

The defects are sorted in three layers: **category** (e.g. Erreur Branchement) → **cause** (e.g. Inversion) → **sub-code**
(the official code, e.g. T04).

| Table | Level | What a row is | How to fill it |
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

| Table | Level | What it holds |
|---|---|---|
| `2_reglages_pages.csv` | 2 | Name / value. The **target** (`objectif_baisse` 0.25 = 2025 minus 25 %), the weight of July and August in the monthly target, what counts as a shutdown week, the minimum MSN volume for a rate, the **filters at opening** (production type, Responsabilité boxes, period), the MFT page's thresholds ("what goes up / down", recurring FIN), the MFT action targets. |
| `2_lignes.csv` | 2 | Each line's colour (1 to 4). |
| `3_alarmes.csv` | 3 | Name / value: the bell's statistics. How many recent weeks are compared (4) with how many weeks before (12), the thresholds for a minor or major alarm, slow rises, odd aircraft, how many alarms are shown (5). |

### MFT actions and cables

| Table | Level | What a row is | How to fill it |
|---|---|---|---|
| `1_actions_mft.csv` | 1 | One MFT action: id, line, title (French and English), **the problem it targets** (`niveau` + `valeurs`), analysis and action owners, dates, status, expected benefit, the tracker it comes from, `source` | To add an action: one row with `source` = `manuel`. `niveau` says what kind of problem: `cat` a category, `rca` a cause, `sub` a sub-category, `code` a sub-code, `where` a place of detection. `valeurs`: the names exactly as on the dashboard, several separated by `\|`. |
| `2_actions_mft_problemes.csv` | 2 | Links a row of the MFT trackers (programme, category, start of the defect text) to the problem it targets (`niveau`, `valeur`); `a_verifier` = to be checked | Only used when the actions are refilled from the trackers; the notebook doesn't read it. |
| `1_demandes_cables.csv` | 1 | One cable request of the cables team: week, date, NC, programme, MSN, reason, imputation, origin, proposed cause, cables, comment, `source` | Add a row per new request; set `source` = `manuel` on rows you type or correct. |
| `2_cables_origines.csv` | 2 | An imputation of the cable tracker → the origin shown (`(autre)` = anything else) | Only used when the requests are refilled from the tracker. |
| `2_regle_cause_cable.csv` | 2 | Rule table (section 4.3): the proposed cause of a cable request, from keywords in its analysis comment | Only used when the requests are refilled from the tracker. |

### General settings and data sources

| Table | Level | What it holds |
|---|---|---|
| `2_parametres.csv` | 2 | Name / value: the plant followed (`FTO2`) and its codes (`FTO2\|FT02`), the **first date counted**, the year of the GPS / Test lists, from when rework orders and aléas are read, whether the old Slate outputs are still written (`oui` while the old app is used), a limit on the number of NCs (empty = all), the comparison year (2025). |
| `2_sources.csv` | 2 | Name / value: the names of the Skywise datasets (as in the notebook's Data panel) and of the files in `data/` (stations, GPS register, Test list), with the lines to skip and the column names in those files. Change it when a dataset or a file is renamed. |

---

## 6. Common tasks

| I want to... | Table | What to do |
|---|---|---|
| Count a new kind of REC | `2_regle_phase.csv` | Add the workflow text to the `valeur` of a REC row (`-CRE\|-PNC\|-RCX`), or add a row before the `99` rule. |
| Price the rejected parts | `1_prix_pieces.csv` | One row per part: `reference;prix_unitaire_eur`. Or tie a part to an NC: add its NC number. |
| Change an hourly rate | `2_cout_parametres.csv` | Change `valeur` of `taux_production`, `taux_qualite` or `taux_me`. |
| Change the target | `2_reglages_pages.csv` | `objectif_baisse`: 0.30 for −30 %. |
| Add a product | `2_regle_produit.csv`, then `2_produits_plan.csv` | A rule that recognises it, then its name in the plan. |
| Update the production plan | `1_plan_msn.csv` | Add the new aircraft, correct the dates that moved; `source` = `manuel` on those rows. |
| Add a shutdown | `1_calendrier_production.csv` | Start, end, weight 0 (closed) or 0.5 (half), reason. |
| Add an MFT action | `1_actions_mft.csv` | One row, `source` = `manuel` (see above). It appears on the MFT page for everyone at the next notebook run. |
| Change what the dashboard shows at opening | `2_reglages_pages.csv` | `defaut_phase`, `defaut_responsabilite`, `defaut_periode`. |
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
| `2_cout_*.csv`, `3_cout_*.csv` (the cost) | `cost/params.py` | Turned into the cost model's settings, used by `cost/model.py` |
| `2_parametres.csv`, `2_sources.csv` | `skywise.py`, `config.py`, `manual_lists.py` | Which plant, from which date, which datasets and files to read |
| `1_*.csv` (production plan, actions, cables...) and the page settings (`2_reglages_pages.csv`, `2_categories.csv`, `2_lignes.csv`, `3_alarmes.csv`) | `reference.py` | Packed into the table `fto2_dash_ref`, which the pages read |
| categories, causes, sub-codes | `reference.py`, `core.py`, `parser/fto2_logic.py` | Names and definitions shown on the pages, official sub-codes of the defect lines |

So the pages never read `data/config/` themselves: they get the settings they need through `fto2_dash_ref`, rewritten at
each run.

**The checks before anything is computed** (`notebook_kit/fto2/config.py`):

- the table exists and is not empty;
- every line has as many `;` columns as the first row ("line N has X columns, the header has Y");
- the columns a table must have are all there ("the column(s) X are missing");
- a name-and-value setting that the code asks for exists ("the line 'X' is missing");
- `oui` / `non` settings hold `oui` or `non`.

**The checks of a rule table** (`notebook_kit/fto2/rules.py`, function `check`): `ordre` is a number, the test is one of the
list and has a value when it needs one, the column exists in the NC data, a regular expression is valid, `resultat` is not
empty, and there is a default rule (`toujours`). Every problem
is reported with the file and the line, in plain words.

**How a rule table is applied** (`rules.py`, function `apply`): for each NC, the rules are tried in `ordre`; the rows of one
rule are combined (all must be true); the first rule that holds gives the result; the `toujours` rule gives the default. The
same function serves every rule table, so all of them behave the same way.

**Settings with several values** (`FTO2|FT02`, `7=0.6|8=0.6`) are split on `|` by `config.parameter_list`; the cost tables
accept a comma or a dot for decimals (`cost/params.py`).

