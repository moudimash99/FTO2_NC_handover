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
| Skywise dashboard pack v4.8 | Delivered, **install not confirmed**; 2 known fixes pending | `02_dashboard_pack/`, handover doc (section 10) |
| Real pipeline notebook | Running in Skywise today, uses an older parser; read-only context | `06_input_data/pipeline_notebook.py`, section 5 |
| Professional FR/EN Pareto dashboard (offline HTML) | Done | `03_reports/FTO2_Pareto_defauts.html` |
| Cable defects analysis | Findings done, **decision pending** (options A–D) | section 6, Docs "FTO2 Cable Defects – Findings" |
| REC tagging | Rule + regex proposed, **definition decision and precision check pending** | section 7, Docs "REC NC Tagging – Findings" |
| Full defect table for the presentation | Done | `05_outputs/FTO2_defects_detail_v48.xlsx` |
| H1 2026 deep dive, writing standard, entry-tool spec | Done (Aug–Sep), not deployed | section 8, `03_reports/` |
| CNQ reconciliation (predecessor files vs official method M1888 / UG2600252) | Mentioned by Mohammad, **not started here** | — |
| CNQ model | Version cnq-2026.10.19: 7 rule changes from SAP rework orders and MES aléas, approved 19 Oct | `cnq_handoever/`, `CNQ_CHANGES.md` |
| Work orders, MES aléas, 2025 NCs (uploaded 19 Oct) | Analysed; investigation checklist for Mohammad, **checks pending** | `05_outputs/CNQ_investigation_checklist.html`, `07_scripts/wo_disruption/` |
| New Pôle Élec Quality Hub (Slate home page) | Template 5 chosen 20 Oct. Page `hub/pole_elec_hub.html`, links in `hub/hub_config.js` (placeholders he fills). Content = current hub only; **names of the 2 hidden third-row tiles and the QA Management tab content still needed** | `09_pole_elec_hub/` |

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
- **Bug to mention to Mohammad when relevant:** in STANDARD mode it writes `fto2_dashboard_data` twice; the second write (`final_df`) overwrites the enriched NC table from `explode_dataframe`.

### 5b. The v4.8 install pack (`02_dashboard_pack/`)

- `1_pipeline/fto2_logic.py`: plain pandas; EDIT block at top holds dataset paths, `SAP_COLUMNS`, `OUR_PLANT`, `PERIOD_START/END`, `LINES`, `RCA_NAMES`. `fto2_transforms.py` wires it into a Code Repository; `code_workbook_fallback.py` for a Code Workbook.
- Outputs `fto2_defects` (one row per defect) and `fto2_nc` (one row per NC, counts per category).
- `2_slate_queries/q01…q08`: Slate SQL on the Postgres syncs `foundry_sync.fto2_defects` / `foundry_sync.fto2_nc`, widgets `w_mineurs`, `w_groupe`.
- `3_check/valeurs_attendues.csv`: expected values on the SAP extract 5 Jan – 6 Jul 2026 (install check).
- Step-by-step install: Docs "Skywise NC Dashboard Handover" (section 10).

**Pending fixes in the pack (decided, not applied):**
1. `LINES` must map programme **"MT" → A400M** (A400M is "MT" in Skywise).
2. **Drop the A400M chart** (all MT long texts are redacted): remove `q02_top5_A400M.sql`, its preview card, and mentions in the doc and README.

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

Deliverables: Docs "FTO2 Cable Defects – Findings"; `05_outputs/FTO2_defects_detail_v48.xlsx` (one row per defect with NC info merged, 45 columns, Summary sheet with live COUNTIFS, Read me); `07_scripts/cable_check.py`, `build_defect_table.py`.

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
0b. **Hub:** template 5 chosen; get the names of the 2 hidden third-row tiles and the QA Management tab content, then prepare the page for Slate (he installs it and pastes the links). Content must stay exactly what the current hub has.
1. **Cable defence:** get Mohammad's choice among options A–D and the "cable problem" definition; then produce the slide numbers (by defect and by NC). Nothing in the parser has been changed for this yet.
2. **REC:** get the definition decision; ask for the precision query result and REC's roster; then write the final rule spec for the pipeline team (columns `rec_written`, `rec_fixed`, `imputation`).
3. **Pack v4.8:** apply the two pending fixes (MT → A400M in `LINES`; drop A400M chart) when he asks; confirm whether the pack was installed.
4. **Mohammad to check** the English RCA / category translations in the FR/EN dashboard.
5. Human review of 185 low-confidence defects (`05_outputs/revue_humaine_souscodes.csv`, column `sous_code_correct` empty).
6. Not started: CNQ reconciliation of predecessor files with the official method (M1888 CNQ, UG2600252 NC cost model / concession MC.QU.02).

---

## 10. Links (Claude artifacts, private to Mohammad's account)

- Skywise NC Dashboard Handover (install guide for pack v4.8): https://claude.ai/code/artifact/691b9b8e-8254-4684-a8db-75a332082083
- FTO2 Defect Pareto (online dashboard): https://claude.ai/artifact/M6Ge6BcdZwxPRo3A8LD3dM
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
| `03_reports/` | Dossier, deep dive, classification spec, code-sheet analysis, taxonomy notes, writing standard, entry-tool spec, findings PDF/HTML, FR/EN Pareto dashboard, Slate preview, presentation |
| `04_reference/` | Official codes, sub-category reference, mappings, codes to verify |
| `05_outputs/` | Defect table xlsx; parsed defects v4.8 (CSV) and v4.1–v4.7; NC table v4.7; LLM sub-codes; human-review list; v4.7 group changes; cable review files; count disagreements; NC review list |
| `06_input_data/` | Inputs Mohammad uploaded: dashboard export, missing IDs, nc-rec, REC tracker, cable team tracker, MFT action trackers (A330/A350), pipeline notebook, earlier REC note, sample NC text, code sheet text |
| `07_scripts/` | `rec_checks.py`, `cable_check.py`, `build_defect_table.py` (+ older working scripts in `archive/`) |
| `08_tools/` | NC entry tool prototypes (JSX), logic flow (Mermaid), old Slate SQL and preview |
| `cnq_handoever/` | CNQ model (pipeline step, Slate queries, offline dashboard, tests); README_handover.md section 4 lists the 19 Oct changes |
| `CNQ_CHANGES.md` | Every CNQ change: applied, decided, kept for later, needed from the pipeline team |
| `05_outputs/CNQ_investigation_checklist.html` | Offline checklist of open CNQ checks; click a check to open its list; answers kept in the browser, CSV export |
| `06_input_data/work_orders_disruptions_nc2025.rar` | Upload of 19 Oct: SAP work-order operations (Sept 2026), MES aléas (Jan-Sep 2026), Skywise NCs 2025 |
| `07_scripts/wo_disruption/` | Scripts behind every number of the 19 Oct analysis, README with run order |
| `09_pole_elec_hub/` | Five templates for the new hub page, one link list (`hub_links.json`), build and screenshot scripts, README |
