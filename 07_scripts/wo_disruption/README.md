# Work orders, disruptions and 2025 NCs (19 Oct 2026)

Input: `06_input_data/work_orders_disruptions_nc2025.rar`, uploaded by Mohammad on 19 Oct 2026.

| File in the archive | Content |
| --- | --- |
| `split_part_1..8.csv` | SAP work-order operations, plant FTO2, operations confirmed 1 Sep – 1 Oct 2026 (2,757 orders, 16,285 operations) |
| `split_part_nc_1..4.csv` | Skywise NCs, plant FTO2 only, created 3 Jan 2025 – 30 Jan 2026 (1,458 NCs) |
| `disrup.csv` | MES disruptions, plant FTO2, opened 5 Jan – 30 Sep 2026 (2,500 rows; `nc_number` is empty) |

## Run order

Unpack the archive into its own folder, then pass paths as arguments (session rule: `python3 -I`).

```
unar -o <W>/wo_extract 06_input_data/work_orders_disruptions_nc2025.rar
X=<W>/wo_extract/<folder created by unar>      # holds the csv files
P=<W>/wo_extract                                # pickles are written here
python3 -I load.py $X                           # -> wo.pkl, nc.pkl, ds.pkl in $P
python3 -I s03_vs_model.py $P <repo>            # NC -> S03 links, S03 vs CNQ model
python3 -I s03_unlinked.py $P                   # what the unlinked S03 orders are
python3 -I ds_nc.py $P <repo>/06_input_data     # disruption -> NC (same work order, -2 h .. +72 h)
python3 -I run2025.py $P <repo>                 # parser v4.8 + CNQ on 2025 and 2026 NCs
python3 -I cable_ds.py $P                       # cable defects vs disruption comments
python3 -I final_nums.py $P <repo>/06_input_data
```

`profile.py`, `ranges.py`, `links.py`, `units.py`, `s03.py`, `ds_links.py` are the exploration steps (column profiles, date ranges, link tests, time units).

Second round (after `run2025.py`):

```
python3 -I prefix.py $P <repo>/06_input_data       # what AW_ / WO_ / RS_ / TS_ links mean
python3 -I prefix_ex.py $P <repo>/06_input_data
python3 -I plan_vs_actual.py $P                     # the 2% of operations where confirmed != planned
python3 -I nc_to_wo.py $P <repo>/06_input_data      # NC -> rework order, all NCs, both years
python3 -I wo_to_nc.py $P <repo>/06_input_data      # every Sept S03 order -> trace back to an NC
python3 -I erma.py $P                               # ERMA NCs (excluded by the 2026 pipeline)
python3 -I calib.py $P                              # planned rework time vs CNQ model, complete orders
python3 -I extra.py $P                              # REJ / EXC, NC-handling orders, timing gaps
python3 -I y2025.py $P                              # 2025 vs 2026 with and without ERMA
python3 -I subcode.py $P                            # sub-code fill in parser output
```

Link rule: an `AW_`, `WO_` or `RS_` link whose number is not the NC's own `work_order` is the NC's rework order (all such hits in the file are S03). Same number = the order the NC was raised on (S01).

## Main numbers

- NC `linked_document` `AW_…` points to S03 "Parasitic flow" orders (89 of 89 found are S03). S03 = rework orders created from NCs, plus other orders (régul, REC subcontractor catch-up, A400M).
- Work-order confirmations equal the standard value for 98% of operations; start = finish timestamp for 93%. No measured durations.
- Unit `IM` = 1/100 hour: on the 193 operations where confirmed != planned, 176 confirmed values equal the start-to-finish clock time converted at 1 IM = 0.6 min (7 if read as minutes). Those 193 are artefacts (open operations, ×10 typos): 565 h planned, 8,535 h confirmed.
- 96–97% of reworked FTO2 NCs have a rework order (2025: 760 of 790, 2026: 578 of 595). Exchanges: 0 of 20. Rejections: about half.
- Sept 2026 S03: 614 orders, 1,615 planned h. Traced to an NC: ~160 orders, ~245 h. No NC number: 453 orders, 1,371 h (FAL catch-up on RECX work centres, REC subcontractors, OT régul, aircraft-side requests, cable/test work).
- 84 reworked NCs with a complete rework order: planned 9,685 min vs 13,332 min for the model's setup + hands-on + recheck (model ~38% high). 1-defect NCs: planned median 59 min, model 110.
- 214 of 322 quality disruptions (QLS) are followed by an NC on the same work order within 72 h, median 2.6 h. QLS time lost: median 30 min.
- Jul–Sep 2026 FTO2 NCs with a work order: 61 of 219 preceded by a disruption (cable NCs 42 of 49, test NCs 0 of 52).
- 2025 (plant FTO2, Jan–Dec): 1,002 AEC NCs, CNQ level 3 = 211,842 EUR (211 EUR per NC). The 2025 file includes 184 FTO2-liable NCs written by ERMA (33,672 EUR), which the 2026 pipeline excludes. Without ERMA: 818 NCs (68 per month), 178,170 EUR, 218 EUR per NC. 2026 Feb–Sep (pipeline, no ERMA): 87 NCs per month, 217 EUR per NC.
- Parser output used for the cost: `sous_groupe` (42 classes), from keywords (53% of defects) and written head codes (30%). `sub_code` is empty in the pack v4.8 output.

Third round (after the second):

```
python3 -I wc_split.py $P                           # planned vs model without the quality re-check; S03 work centres
python3 -I nonrec.py $P <repo>/06_input_data        # S03 split REC / IEVB (MSN 700/701) / régul / A400M / shop floor
python3 -I ds_all.py $P <repo>/06_input_data        # disruptions: time lost by kind, links to NCs and rework orders
python3 -I ds_rest.py $P                            # quality disruptions with no NC
```

- With the 30-min quality re-check left out (it is done by the quality line service, not planned on the order): planned 9,685 min vs model setup + defects 10,812 min (+12%; +4% without customer returns).
- Sept S03 by family: REC 274 orders / 746 h, IEVB (MSN 700/701) 74 / 217 h, régul 8 / 200 h, A400M 9 / 58 h, FTO2 shop floor 249 / 394 h (144 orders / 213 h traced to an NC).
- Disruptions Jan–Sep 2026 (all FTO2 shop floor): 1,346 h lost. Work order / definition 516 h, missing parts 330 h, line 261 h, quality 238 h.

Fourth round:

```
python3 -I quality_wo.py $P                         # quality work centres; the two NC-management orders in full
python3 -I cable_cut.py $P <repo>/06_input_data     # 37 S03 cable-cutting orders (A330 print room 4FEM0E14)
python3 -I cable_cut2.py $P; python3 -I cable_cut3.py $P   # related NCs and BF24 disruptions
python3 -I ds_cap.py $P $X/disrup.csv; python3 -I ds_cap2.py $P $X/disrup.csv   # export window and 2,500-row question
python3 -I ds_quality.py $P                         # quality-related disruptions across all kinds
python3 -I cr_sept.py $P                            # customer-return NCs per month
```

- Quality-related disruptions Jan–Sep 2026: 322 declared quality (238 h) + 93 other kinds followed by an NC (68 h) + 107 other kinds with quality wording (91 h) = 522, 398 h. Groups 2 and 3 are keyword / time-window matches and need a read.
- Disruption export: 5 Jan 2026 08:57 (plant restart; no NCs 29 Dec–2 Jan) to 30 Sep 2026 23:31, sorted newest first, exactly 2,500 rows.

Fifth round (test and connection times):

```
python3 -I op_times.py $P; python3 -I op_times2.py $P   # planned test / connection time per product order (S01)
python3 -I s01_totals.py $P                              # S01 planned hours by operation type
python3 -I retest_conn.py $P; python3 -I conn_fit.py $P  # re-test on rework orders; planned time vs number of connection errors
```

- Test NCs where >= 60% of defects are connection errors (11 NCs): planned rework ≈ 77 min + 15 min per connection error (22 min per error on average), against 35 min per error in the CNQ model.

`python3 -I retest.py $P` — re-test operations on rework orders, by family and NC type.

Simulation of proposed CNQ changes (nothing in `cnq_handoever/` is modified; parameters are copied in memory):

```
python3 -I simulate.py $P <repo>     # level 3 before/after each change, 2026 Feb–Sep and 2025 without ERMA
python3 -I outlier.py $P             # the two largest planned rework orders (NC 218233692, 218248460)
```

- All six changes together: 2026 Feb–Sep 151,093 -> 136,417 EUR (217 -> 196 EUR per NC); 2025 without ERMA 178,170 -> 161,761 EUR. Customer returns 2026: 11,975 -> 13,670 EUR.

CNQ model changes applied on 19 Oct 2026 (approved: alert only when an operator raises one; connection errors 35 then 15 min; internal NCs x 2):

```
python3 -I internal_size.py $P            # planned vs model on internal NCs -> factor 2.0
python3 -I rerun_real.py $P <repo>        # 2026 Feb-Sep and 2025 (no ERMA) before / after, with the updated cnq_core
python3 check_dash.py <repo>/cnq_handoever/dashboard/cnq_dashboard.html   # headless check of the dashboard (needs playwright)
```

- Pack data (v4.7, 5 Jan-6 Jul 2026): level 3 134,206 -> 121,503 EUR. 2026 Feb-Sep: 151,093 -> 142,151 EUR. 2025 without ERMA: 178,170 -> 168,633 EUR.

Investigation checklist (19 Oct 2026): `05_outputs/CNQ_investigation_checklist.html` (offline page; click a check to open its list)
and `CNQ_CHANGES.md` at the repository root (every CNQ change: done, decided, to do). Both are written by the same script.

```
python3 -I sheet_data.py $P <repo>       # lists and checks (new model, option B block, M1 groups, returns, no-time orders)
python3 -I cr_rec.py $P                  # customer returns linked to rework orders in the Sept file
python3 -I build_checklist_html.py $P <repo> $X/disrup.csv    # uses checklist_template.html
python3 check_checklist.py <repo>/05_outputs/CNQ_investigation_checklist.html   # headless test (needs playwright)
```

- Disruption block, option B (decided): quality aléas with no NC, Jan-Sep 2026: 108 aléas, 91.2 h, 4,560 EUR. Aléas that led to an NC stay inside the NC cost (alert step).
- Decided after that: the 19 aléas on the MIP / 1101VB (possible ERMA NCs) are left out until checked: 89 aléas, 66.9 h, 3,347 EUR.
- Final state of the CNQ model on 19 Oct 2026 (cnq-2026.10.19, all approved changes): pack 128,741 EUR; 2026 Feb-Sep 149,824 EUR; 2025 without ERMA 178,870 EUR; customer returns 2026 12,577 EUR. The figures quoted earlier in this file are intermediate steps.
