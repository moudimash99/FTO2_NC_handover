# NC Deep Dive — Beyond the Surface Counts
*Scope: 807 NCs, Jan–Jul 2026, plant Electricity France. Analysis restricted to SERIE (741 NCs) unless stated. Source: Skywise extract + long-description text mining.*

---

## 1. The headline: your NC count hides a 3× fault volume

The dashboard KPI counts notifications. But the long descriptions show that many notifications are **bundles**: one "RETOUCHES TEST MSN xxx" or "Inspection finale MIP MSN xxx" NC contains a numbered list of individual faults (`DEF 1-T04 : ...`, `1 - FIN xxx : ...`).

Parsing every long description and counting the individual fault items gives:

| Metric | Value |
|---|---|
| SERIE NCs (Jan–Jul) | 741 |
| **Estimated individual faults** | **≈ 2,300** |
| Multiplier | ×3.1 |
| Bundle NCs (≥5 faults) | 111 NCs (15%) carrying ≈1,600 faults (**70% of fault volume**) |
| Where bundles occur | Contrôle final (≈1,010 faults) and Interne/test (≈560 faults) |

Monthly, NC counts look flat (~110–150/month) while the true fault load runs 310–430/month. Any trend, target, or CONQ discussion based on NC counts is dampened by a factor of three, and the dampening is worst exactly where it hurts most: escapes caught at final control and test.

The parsed fault count was calibrated against the manual `Ext_Nb_Defauts` column: **89% exact match, 94% within ±1, 96% within ±2** (n=314). In other words, the manual counting activity behind the external lists is automatable today with regex alone — no AI needed.

## 2. The fault-level Pareto looks nothing like the NC-level one

The structured columns are too coarse to steer action: `defect_code` is "[Electrical Assembly Installation]" for 43% of NCs, and `cause_code` is "[People]" for 49% — both analytically dead ends. At the individual-fault level, mined from the text (1,580 classified fault lines, SERIE):

| Defect family | Faults | Note |
|---|---|---|
| Inversion de branchement / câble en mauvaise borne | ≥485 (likely ~550 incl. partial matches) | dominated by MIP A350, caught at test |
| Câble / pièce manquant(e) | ~120 | includes "cables manquants non reçus" lists |
| Câble coupé / abîmé / cassé | ~106 | |
| Longueur câble (trop court / surlongueur) | ~70 | recurring "reçu trop court" from upstream |
| Borne déverrouillée (Q01) | ~60 | |
| Erreur référence / plaquette, FOD, continuité/HS, étiquettes, métallisation, sertissage, frètes, torquage | ~10–25 each | |

By product, **MIP A350 concentrates ≈1,530 faults — 67% of all SERIE faults — while it is only 35% of NC lines.** The NC-count Pareto on the current dashboard structurally understates the MIP problem. 740VU is a distant second (~250), then PTVU (~140).

## 3. A systemic, actionable signal: repeat-offender connectors

Within inversion/mauvaise-borne faults, the same FINs come back across **different NCs and MSNs** — this is chronic, not one bad build:

| FIN | Faults | Distinct NCs |
|---|---|---|
| 3RN1B / 3RN1A / 3RN2A / 3RN3A / 3RN3B | 73 total | 7–13 NCs each |
| 3SEA | 13 | 13 |
| 1WK11A / 1WK21A / 1WK22A / 1WK53A | 39 total | 4–10 NCs each |
| 1608VC070A | 9 | 4 |

Roughly **120+ test-caught wiring inversions concentrate on ~10 connector references** on the MIP A350. That is a textbook target for a focused action: pinning aid, détrompage, instruction clarification, or a dedicated self-check step at those FINs — and a before/after KPI to prove the effect. If you bring one thing to Emmanuelle from this analysis, this is it: bounded scope, measurable, and it attacks the top of the true Pareto.

## 4. The hidden taxonomy: Q/T codes already exist in the text

Operators already classify faults with an internal code in the DEF lists, even though no structured column captures it. Observed semantics (mined from the text itself):

| Code | Meaning (as used) | Occurrences |
|---|---|---|
| T04 | Inversion de branchement entre bornes | 353 |
| T02 | Câble en mauvaise borne (X au lieu de Y) | 262 |
| Q01 | Borne / contact déverrouillé | 76 |
| Q04 | Erreur référence / inversion de plaquette | 69 |
| Q11 | Prise cassée / erreur référence prise | 54 |
| T01, T03 | Câble / élément manquant | 18 |
| Q07, Q08 | Sertissage / blindage / tresse | 21 |
| T05, Q03, Q05, Q06, Q10, Q12 | minor volumes | <10 each |

This taxonomy should be promoted to a first-class structured field in the pipeline (see §6). It is already spoken by the shop floor — you don't need to invent a classification, just extract and govern this one.

## 5. Data-quality battery (auto vs GPS vs Ext)

**Decision status — healthy.** `Statut_decision_auto` vs `GPS_Statut_decision`: 94% agreement (n=449). Two fixable artifacts: auto "Request for Design Change" should map to GPS "DQN" (5 cases), and DQN↔Echange confusion (6 cases).

**Type NC — needs work.** Agreement only **74%** (n=408). Hotspots: auto says INTERNE where GPS says CONTROLE FINAL (46) or FOURNISSEUR (17); auto CONTROLE FINAL vs GPS INTERNE (26). Also, GPS uses categories the auto rules never emit (CLIENT, DAMAGES, CASSE) — the two taxonomies aren't even the same list. Align the value sets first, then fix rules.

**Unknown backlog.** 163 NCs (20%) are `Type_NC_auto = Unknown`; GPS covers only 43 of them, including 11 CLIENT — a category your rules can't produce today. The 43 GPS-labeled Unknowns are free training/validation examples for improving the auto rules.

**Manual count errors exist but are rare.** 13 NCs diverge by >2 between `Ext_Nb_Defauts` and the parsed count — each is either a manual miscount or a parser edge case; both are worth a look (list attached).

**Other flags.** `Ext_Nb_Defauts = 0` on 38 closed NCs — an undocumented convention (NC without retouche? created in error?) that should be made explicit. 99 NCs (12%) are status *deleted* but still flow into the extract — decide whether the dashboard excludes them (today they inflate counts). 76 long texts (9%) are "Removed for classification reason" — a permanent blind spot for text mining; for these, the manual GPS/Ext lists are the only fault-level source, so the future pipeline must keep a manual-entry lane rather than assume 100% text coverage.

## 6. Blueprint: the proactive dashboard (Skywise-native, no AI required)

The principle: **change the unit of analysis from notification to fault.** Everything else follows.

**Layer 1 — Parse (deterministic, works today).** A scheduled transform (Pipeline Builder or a Code Repository / PySpark job on the same dataset feeding Slate) that, per NC: strips quoted `> X*` blocks; splits `NonConformity NNNN :` blocks; extracts DEF-lists (`DEF n-CODE :`) and numbered lists (`n - FIN xxx :`); counts cable-list items (`N° ...`); extracts Q/T codes, FIN references, `Decision Taken`, `Type of nonconformity`, department codes and companies from the log; classifies each fault line into the keyword families of §2. Output: a **fault-level dataset** (one row per fault, keyed to the NC) sitting next to the NC dataset. This entire layer is regex + keywords — the 89% calibration above is the proof it works without any LLM.

**Layer 2 — Reconcile.** Join the parsed output with GPS/Ext lists. Where both exist: agree → confidence high; disagree → row lands on an *exceptions queue* for a human. Where text is redacted: manual list wins. This converts today's parallel manual bookkeeping into a review-only workflow — people stop counting and start checking, and the counting error class disappears.

**Layer 3 — Detect (this is what makes it proactive).** Alerts computed on each data refresh, not dashboards someone must remember to open:
1. *Recurrence watch*: same FIN (or same Q/T code × product) appearing in ≥N distinct NCs in a rolling window → "3RN3B inversions: 3rd MSN this month."
2. *Rate shift*: faults-per-MSN or faults-per-week per product against its own baseline (a simple c-chart / EWMA on count data is enough; you don't need ML for control limits).
3. *New-symptom detector*: fault lines whose keyword signature matches no known family (today's "Autre") above a threshold → surfaces novel failure modes early.
4. *Data-health*: auto vs GPS disagreements, Ext mismatches, Unknown rate, deleted-NC leakage — the battery of §5 as a permanent tile.
Delivery: Foundry notifications / email digest to the team, plus a "what changed this week" panel at the top of the Slate app. The existing charts (aircraft, product, station, trends…) stay, but re-pointed at the fault-level dataset with an NC/fault toggle.

**Layer 4 — LLM upgrade (the +2 months option).** Once AI access lands, slot it *inside* the same pipeline, not as a replacement: classify the residual "Autre" lines (~40% today), normalize free-text into the Q/T taxonomy, summarize each week's exceptions queue, and enable semantic clustering to find recurrences that keyword rules miss (same failure, different words). Because Layers 1–3 already produce structured fault rows, the LLM only handles the hard residue — cheaper, auditable, and you can measure its lift against the deterministic baseline you already have.

A note on sequencing: resist the temptation to wait two months for the LLM. The deterministic parser already reproduces the manual count at 89% and exposes the full Pareto; shipping Layers 1–3 now means the LLM arrives into a working system with a measured baseline.

## 7. Improvements to the current processing

On naming and provenance: the `_auto` / `GPS_` / `Ext_` convention works but is tribal knowledge — add a single `source` column per derived field (auto | manual | reconciled) so any consumer of the dataset can filter by provenance without knowing the suffix lore. On the auto rules: align the `Type_NC_auto` value set with GPS's (add CLIENT, DAMAGES, CASSE or map them), then use the 43 GPS-labeled Unknowns plus the 89 auto-vs-GPS disagreements as the test set for each rule revision — you have a labeled benchmark for free. On conventions: document what `Ext_Nb_Defauts = 0` means, and decide the fate of deleted NCs in every query (exclude by default, show as a separate tile). On robustness: the parser must keep stripping quoted `> X*` replies (15 NCs would otherwise double-count) and keep the manual lane for the 9% redacted texts. Finally, one human-factors point: the DEF-list discipline at test/contrôle final is what makes all of this parseable — it's worth telling those teams their format is being machine-read now, both so they keep doing it and so the two list formats (DEF n-CODE vs `n - FIN`) can converge on one.

---

*Attached: `fault_level_extract.csv` (1,580 parsed fault lines — a working prototype of the Layer-1 output) and `nc_review_list.csv` (161 rows: count mismatches, type disagreements, GPS-labeled Unknowns).*
