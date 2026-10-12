# REC NC classification — findings (unverified)

Oct 7, 2026 · @Mohammad Machaka

## Read this first

None of this is validated. Mohammad has said that much of what was concluded in the analysis session is untrue, without yet saying which parts. Treat every finding below as a hypothesis to check, not a result.

Each finding separates two layers:

- **Observed**: counts and joins computed directly from the four files. These should be reproducible, but they depend on how the files were parsed and joined, which may itself be wrong.
- **Interpretation**: what those counts are taken to mean, for example what REC is, what a station code means, what a free-text comment implies. These are guesses made without knowledge of the FTO2/REC organisation, and are the most likely source of error.

Corrections already made during the session:

- The in-window count was first given as 93; it is 94 once a typo in the tracker is fixed.
- The station rule was first quoted as 92 of 105 on its own, then as part of an 89% figure that actually combined it with the existing FTO2 filter. The two were not clearly separated at first.
- Mohammad stated that GPS covers SERIE only and is a manual extract that cannot be part of the pipeline. Findings that relied on GPS as a rule are downgraded to an offline check.

## Data used

Four CSV files, joined on the notification number (`notification_no_leading_zeros` on the Skywise side, the number extracted from "numéro du déclaratif" on the tracker side).

| File | Rows | What it appears to be (assumed) |
| --- | --- | --- |
| fto2\_dashboard\_data 12.csv | 1,000 | Mohammad's parsed FTO2 dashboard output; created 20 Jan – 28 Sep 2026 |
| fto2\_dashboard\_data\_missing\_ids 3.csv | 127 | IDs missing from the dashboard, fetched separately; created 15 Dec 2025 – 25 Sep 2026 |
| nc-rec.csv | 115 | Full Skywise records for the NCs listed in the REC tracker |
| Fichier suivi des retouches REC – NC rédigées par le REC.csv | 278 lines, 120 real entries | REC's own log of NCs written by REC quality, with an Imputation column |

Tracker breakdown (observed):

- 116 of the 120 entries have an NC number; the other 4 are early-2025 entries with none.
- All 116 were found in Skywise: 115 in nc-rec.csv, plus 2181014667, which matches nothing as written. It was assumed to be a typo for 218014667, which is in the dashboard. That correction is a guess.
- Imputation: 55 FAL, 50 REC, 10 QSR, 1 blank.
- By creation date: 17 in 2025, 2 on 1–19 Jan 2026, 94 on 20 Jan – 28 Sep 2026 (the dashboard window), 3 after 28 Sep.

Assumption to check: that the tracker is a complete and correct record of NCs written by REC. It is used as ground truth throughout; if it is incomplete or its imputations are disputed, every coverage figure below shifts.

## Finding 1: few tracker NCs reach the dashboard

**Observed.** Of the 94 tracker NCs created inside the dashboard window, 17 appear in the dashboard.

| Tracker imputation | In window | In dashboard |
| --- | --- | --- |
| REC | 38 | 2 |
| FAL | 45 | 5 |
| QSR | 9 | 9 |
| Blank | 1 | 0 |
| **Total** | **94** | **17** (incl. the typo-corrected 218014667) |

All 17 that are in the dashboard are tagged REC in `Programme_auto`. No tracker NC was found tagged SERIE or FTI.

**Interpretation (uncertain).** The dashboard may be missing most NCs written by REC. This only matters if those NCs are supposed to be in an FTO2 dashboard at all. If the dashboard is meant to show only FTO2-liable NCs, their absence may be correct by design.

## Finding 2: the FTO2 scope filter seems to explain who is in

**Observed.** Mohammad's scope filter was described as: plant = FTO2, or liability = \[FTO2\], or the long text contains "FTO2". Applied to the tracker NCs in the window, it splits them exactly: the 17 that pass are the 17 in the dashboard, and the 77 that fail are the 77 missing.

Where the tracker NCs sit in Skywise (all 115 in nc-rec.csv):

- Plant: FFF1 63, FNZ1 22, FTO2 14, DHA1 13, DBR1 2, FTO1 1.
- Liability: \[FFF1\] 78, \[TO\] 30, \[FTO2\] 4, blank 2, \[FNZ1\] 1.
- For the 50 REC-imputed NCs: liability \[FTO2\] on 2, plant FTO2 on 1.

**Interpretation (uncertain).**

- REC NCs might be logged against the FAL plant where the aircraft is, which would be why the filter misses them. This is a guess about how REC works.
- It was suggested that this means FTO2's non-quality cost is understated in Skywise. That depends on what \[TO\] and \[FFF1\] mean for cost allocation, which was not checked. Do not repeat this claim without confirming it.

## Finding 3: REC vs FAL imputation did not show up in the fields checked

**Observed.** Among NCs the tracker attributes to REC authors, the REC-imputed and FAL-imputed ones look alike on every field compared:

| Field | REC-imputed (50) | FAL-imputed (55) |
| --- | --- | --- |
| Liability \[FFF1\] / \[TO\] | 31 / 17 | 37 / 13 |
| Station V42RC1 | 37 | 28 |
| Cause group Human Factors | 32 | 27 |
| Decision Rework to drawing | 38 | 36 |
| Long text contains "REC" | 28 | 25 |
| Long text contains "intervention" | 18 | 20 |

GPS imputation only takes the values Airbus TLS, ERMA and MdB in the dashboard data, and no tracker NC was found in GPS.

**Interpretation (uncertain).** No Skywise field was found that separates REC-caused from FAL-caused. Only a handful of fields and keywords were tested, so a better signal may exist (for example in fields not in these exports, or in text patterns not tried). The tracker's own author was unsure about one entry (217814121), so the tracker imputation is not certain either.

## Finding 4: candidate rules for catching REC-written NCs

**Observed.** Coverage of the 94 in-window tracker NCs by each candidate rule:

| Rule | Caught | Missed |
| --- | --- | --- |
| Station contains 42RC, or work\_ctr starts RECX/SUBR | 71 | 23 |
| Current FTO2 filter alone | 17 | 77 |
| Both combined | 84 | 10 |
| Both + author is a REC inspector ID | 90 | 4 |
| Both + pulling tracker IDs directly | 94 | 0 |

The 10 missed by "both combined": 8 are PNCs, mostly with no station; 217022710, which the tracker itself says was not written by REC; and 217990195, with a blank imputation. Of the 4 still missed with inspector IDs, 33 of all 116 tracker NCs have a masked author (`#UID~`), so author ID can never cover everything.

Inside the dashboard, 37 rows sit at a 42RC station; 36 are tagged REC.

**Interpretation (uncertain).**

- "42RC" was read as the REC station code. That is inferred from the pattern, not confirmed.
- The inspector IDs (ST32873, GALIZ81C, RGAGTM5M, PMAR3D30, CLOP5B4I) were picked from the authors of tracker NCs. They are not a confirmed REC roster; some may write non-REC NCs too.
- Recall was measured only against the tracker. Precision was not measured: nothing here shows how many non-REC NCs these rules would also pull in when run on all of Airbus.

## Finding 5: possible tagging inconsistencies

**Observed.** Rows in the dashboard and missing-IDs files where the current `Programme_auto` tag and other signals disagree:

| NC(s) | Current tag | Conflicting signal |
| --- | --- | --- |
| 216383860 | SERIE | Station F42RC1; text "Fait par le rec"; not in GPS; written by OLMEM/Daher, not in tracker |
| 217614732, 217300150, 217131752, 216165997, 216064934 | REC | All in GPS (type DAMAGES); none in tracker; none at a 42RC station |
| 218048019, 218048287, 218048799, 218048980, 218048984 | SERIE | Same QSR campaign (TO/F/EQ/26-00012) as 10 NCs tagged REC; tracker calls the campaign QSR |
| 216085084 | SERIE | Station V42RC1, but in GPS, so SERIE per the GPS = SERIE rule |

In the text-matched REC rows, "REC" was seen used in several senses: REC did the rework ("travail effectué par l'équipe REC"), REC was asked to act ("involve the REC"), REC was blamed ("Responsabilité REC"), REC was explicitly cleared ("n'est pas de responsabilité REC"), or as part of a harness or design-solution label. Two of the five GPS rows (217300150, 217131752) do not mention REC at all; what tagged them REC was not identified.

On the current extract, a rule of tracker OR 42RC station OR RECX/SUBR work\_ctr tags 53 rows REC, of which 1 is in GPS. The current rule tags 85, of which 5 are in GPS. 34 rows tagged REC today would not be REC under the station rule.

**Interpretation (uncertain).** This relies on Mohammad's statement that GPS is SERIE-only. Whether the 34 rows that drop out are errors depends on what the REC tag is meant to mean (see Open questions).

## Finding 6: the dashboard export may be capped at 1,000 rows

**Observed.** fto2\_dashboard\_data 12.csv has exactly 1,000 rows, sorted newest first, and its oldest row is 20 Jan 2026. January has 62 rows against 96–161 in other months. 54 of the 58 January rows in the missing-IDs file fall on 1–19 January.

**Interpretation (uncertain).** This pattern fits an export row limit cutting off the oldest rows. It could also be a deliberate date filter or how the file was produced. If it is a cap, the cut-off date moves forward with every new export. It barely affects the REC tracker figures (2 tracker NCs fall on 1–19 Jan).

## Tentative approach (to validate)

These steps follow from the findings above. If a finding turns out to be wrong, the step built on it falls too.

1. Confirm whether the 1,000-row limit is real (Finding 6). If so, export the dataset itself rather than a table view.
2. Run the extraction on the all-plants NC dataset, with the current FTO2 filter OR station contains 42RC OR work\_ctr starts RECX/SUBR (Finding 4).
3. Join the tracker on notification number, to bring in REC NCs the rules miss and to supply the imputation (Findings 3 and 4).
4. Replace the single REC label with separate columns:
   - `rec_author`: in the tracker or matches the station rule.
   - `imputation`: from the tracker; "to confirm" otherwise.
   - `rec_rework`, optional: text says REC did the work.
5. Use the free-text "REC" keyword only as a review flag, not a classifier (Finding 5).
6. Tag the QSR push-button campaign one way.
7. Outside the pipeline, compare each new GPS extract with the output: any NC in GPS but tagged REC is a conflict to review.

A draft PySpark transform for steps 2–4 (fto2\_rec\_scope.py) was written during the session. It assumes column names from the CSV exports and has not been run.

## Open questions and what to verify

- [ ] Which of the findings above are wrong, and why? The rest of this list should be re-ordered once that is known.
- [ ] What does "REC NC" mean for the dashboard: written by REC, caused by REC, reworked by REC, or something else?
- [ ] Is the tracker complete, and are its imputations accepted by FAL and FTO2?
- [ ] Is 42RC really the REC station code? Ask REC or check station master data.
- [ ] Get the actual REC inspector roster instead of IDs inferred from 116 NCs.
- [ ] Run the station rule on all of Airbus and sample about 20 hits not in the tracker to measure precision.
- [ ] Is the tracker entry 2181014667 really 218014667?
- [ ] What tagged 217300150 and 217131752 as REC in the current rule?
- [ ] Check with REC whether 216059511 and 217542391 (text says REC responsible; both in GPS) are theirs.
- [ ] What do \[TO\] and \[FFF1\] liability mean for cost allocation, before saying anything about CNQ being understated?
- [ ] Is the 1,000-row cut-off an export limit or a filter?
