# Offline run of `rec_rule_test.ipynb`

`foundry/transforms.py` stands in for Skywise: it serves the exported NCs as the `non_conformity`
dataset, with `liability` as arrays and `creation_time` as timestamps, as Skywise returns them.
Executes the notebook cell by cell on a Jupyter kernel (needs `nbformat nbclient ipykernel`). `full` sets `FULL_SCAN = True`.

```
python3 -I build_data.py <repo>/06_input_data <nc2025_dir> <W>/skywise_mock.pkl
cd <W> && python3 -I <repo>/07_scripts/rec_test_local/runner.py <repo>/07_scripts/rec_test_local <W>/skywise_mock.pkl <repo>/07_scripts/rec_rule_test.ipynb <W>/executed.ipynb [full]
```
`<nc2025_dir>` holds `split_part_nc_*.csv` from `06_input_data/work_orders_disruptions_nc2025.rar`.
