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

## Main numbers

- NC `linked_document` `AW_…` points to S03 "Parasitic flow" orders (89 of 89 found are S03). S03 = rework orders created from NCs, plus other orders (régul, REC subcontractor catch-up, A400M).
- Work-order confirmations equal the standard value for 98% of operations; start = finish timestamp for 93%. No measured durations.
- Unit `IM` read as 1/100 hour (to confirm).
- 98 reworked 2026 NCs with an S03 order: planned 11,249 min on S03 vs 11,932 min of work in CNQ level 3. Per NC: 53 of 98 within ×0.5–2.
- 214 of 322 quality disruptions (QLS) are followed by an NC on the same work order within 72 h, median 2.6 h. QLS time lost: median 30 min.
- Jul–Sep 2026 FTO2 NCs with a work order: 61 of 219 preceded by a disruption (cable NCs 42 of 49, test NCs 0 of 52).
- 2025 (plant FTO2, Jan–Dec): 1,002 AEC NCs, CNQ level 3 = 211,842 EUR (211 EUR per NC). 2026 Feb–Sep, same scope: 217 EUR per NC.
