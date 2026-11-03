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


## Second round (4 Nov 2026): the new lines only

391 defect lines of 146 NCs (Sep - 26 Oct, from the raw extract `06_input_data/nc_2026_skywise_fto2_2026-10-26.csv`) had no label. `prep_new.py` writes the lines the build has no usable label for (status not ok) as batches in the same format; five Claude sub-agents in the session (no external API) labelled them with the same `guide.md`, each checked with `validate.py` (OK); `merge_new.py` appends them to `04_reference/llm_labels_longtext.csv` (snippet = the parser's text of the line, so a label is used only while the text is unchanged). Confidence: 282 high, 105 medium, 4 low. The scripts' folder paths point to the session scratchpad: change `S` to rerun. Same next time: run `prep_new.py`, label, `merge_new.py`, rebuild.
