# LLM re-labelling with the full long text (12 Oct 2026)

Every parsed defect (parser v4.8, 3,098 defects / 1,025 NCs) was re-labelled by Claude Sonnet sub-agents
inside the Claude session (no external API). Each agent got ~100 defects with, per NC: the parser snippet
for each defect **and** the full cleaned `description_long_text`, `description_short`, SAP defect/cause codes,
station and author department.

Steps (paths in the scripts point to the session scratchpad; change `S`/`R` to rerun):

1. `prep.py` – joins `05_outputs/fto2_parsed_defects_v4_8.csv` with the long texts of
   `06_input_data/fto2_dashboard_data_12.csv` + `fto2_dashboard_data_missing_ids_3.csv`, writes 34 JSON batches.
2. `guide.md` – the instructions each agent followed (taxonomy, approved rules, **ROOT CAUSE FIRST**, output format).
3. `validate.py` – checks one output line per defect, valid labels, `symptome` key.
4. `merge.py` – merges the JSONL outputs with the parser table.
5. `fix.py`, `fix2.py` – the two manual review passes (5 collar cases aligned to Frettage; 32 loose E4 moves
   "câble manquant, à fournir" sent back from Amont to Manquant – câble).
6. The labels were saved as `04_reference/llm_labels_longtext.csv`; `build/build_all.py` joins them and writes every output (the earlier `out_build.py` is gone).
