# FTO2 dashboard vision (night of 19 to 20 Oct 2026)

Mohammad asked for vision, not routine work: what could be the wow factor, visually and in what the dashboard
connects. Two pages came out of it, both private artifacts on his account:

- Prototype on the real data: https://claude.ai/artifact/KmELL2B43ksMwXPcEGdFov (`FTO2_Vision.html`)
- Notes, with the roadmap and his choices: https://claude.ai/artifact/W4Y6wLvN772mzHnxwYNvKu (`FTO2_Vision_Notes.html`)

**His choices** (Now / Later / No per roadmap line, with a note) are saved in the notes page's store, collection
`choices`, one document per line (`r01` to `r13`, fields `choice`, `note`, `at`). Read them first:
`ArtifactData list` on the notes URL, collection `choices`.

## The idea

The dashboard shows each piece on its own tab. The prototype reads as one story, from the plant to one aircraft, and
draws the links: 2026 against the real 2025, cause → station that finds it → customer, what an NC costs step by step,
the locations and pins that come back, and every NC of one aircraft. Every finding sentence is computed from the
filtered rows (a switch turns titles back into plain names, the dashboard's current rule).

## Five findings (default view: all lines, Série, all defects, data of 28 Sep 2026)

| # | Number | Finding |
| --- | --- | --- |
| 1 | +11 % | 722 NCs against 518 at the same date in 2025 (+39 %). By quarter +50 %, +55 %, then +11 % in Q3; defects +72 %, +57 %, +6 %. MFT actions started in July (coincidence in time, not proof). A350: 4.5 → 5.0 NCs per aircraft with an NC; A330: 7.0 → 8.8. |
| 2 | 805 / 813 | Connection errors found at test; none reached a customer in Série. At the customer: damaged items 9 of 263 (3.4 %), missing items 5 of 305, workmanship 16 of 1,007. |
| 3 | 4 h 22 | Work per NC in the CNQ model, 1 h 04 of it repair (24 %); 3,149 h this year, 765 hands-on. 181 € per defect in a one-defect NC, 25 € in a list. Airbus standard method ×2.2. |
| 4 | 20 / 68 | 113 locations hit on ≥ 5 aircraft carry 1,128 of 2,221 located defects (51 %). 300VT101: 4/50 A350 in 2025 → 20/68 (new); 9KS 15/50 → 18/68, 115VM 16/50 → 18/68 (chronic). 44 % of readable swaps between consecutive pins; 34 pin pairs on several aircraft (411VC001A pins 6↔15 on 4). |
| 5 | +9 % | Cable defects 223 → 243 while all defects 1,855 → 2,704 (+46 %); share 12.0 % → 9.0 %. Parser v4.8 both years. |

2025 comes from `06_input_data/work_orders_disruptions_nc2025.rar` on main (see `prep_2025.py`): FTO2 liable, not
deleted, no ERMA, same phase rule, cut at the same calendar date. Check: 83 of the 86 January 2026 NCs of that file
are in the 2026 extract.

## What to change in the current dashboard (from the 19 Oct screenshots)

1. Placeholders that read as results: the target card shows +33 % on every line (target = 2026 − 25 % by
   construction), "2025 fictif (= 2026)", budget = forecast − 25 %. Use the real 2025.
2. Two colour systems: the cost tab and the Où product chart use saturated blue / green / yellow / pink. One rule:
   green FTO2, orange cable only, red customer and alerts, grey context.
3. Charts that do not earn their space: "Mois de création" (no axis), the two-row cable card, the NC bubble timeline.
4. Headline figures with no comparison.
5. Tabs that do not connect: customer returns apart (old layout), RCA tab ~11,000 px of reference text.
6. Titles that name charts instead of stating the point.

## Roadmap (the lines of the choice sheet)

Now: r01 real 2025 on the overview · r02 cause → station → customer on the customer-returns tab · r03 NC anatomy on
the cost tab · r04 one colour rule.
Next: r05 locations new or chronic (Où) · r06 pin swaps (Où) · r07 alerts on the overview · r08 aircraft passport ·
r09 computed titles · r10 presentation mode and copy summary.
Later: r11 disruption → NC → rework order (pipeline links, rules on main) · r12 late aircraft vs NCs (Avances /
Retards per MSN) · r13 real customer-return cost (check H3).

## Data to ask for

2025 NCs in the Skywise dataset (same query); disruption → NC and NC → rework order links as columns; Avances /
Retards per MSN; insert drawings for the ten connectors with the most swaps; a real target and budget, or none.
