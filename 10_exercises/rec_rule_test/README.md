# REC rule test

**Exercise, not official.** Kept on main as an exercise (Mohammad, 2 Nov): the pipeline's REC tag does not use it. It lived
on the branch `ccr-3c772102-f53cls` (20–22 Oct) in `07_scripts/`.

The question: which NCs are written by the REC team. The rule tried here reads the writer's department; the notes, the
Skywise run of 21 Oct (where the first version failed on precision) and what is left to decide are in `HANDOVER.md`,
section "REC", "Update 20 Oct".

| File | What it is |
| --- | --- |
| `rec_dept_rule.py` | The rule checked on our exports (`python3 -I rec_dept_rule.py <repo>/06_input_data <nc2025_dir>`) |
| `rec_rule_test.ipynb` | The test for the Skywise notebook, one cell per test (read only, writes nothing to Skywise) |
| `rec_test_local/` | An offline stand-in for Skywise to run the notebook on a laptop (its README says how) |
