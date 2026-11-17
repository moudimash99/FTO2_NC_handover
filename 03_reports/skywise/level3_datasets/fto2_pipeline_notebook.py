# FTO2 NC pipeline and dashboard tables (Skywise Code Workspace).
#
# What it does: reads the NCs, applies the rules of data/config/, and writes the dashboard's three tables
# fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions (the steps are in notebook_kit/fto2/skywise.py).
#
# Before the first run:
#   - upload the folder notebook_kit next to this notebook (the code; upload it again after each update);
#   - upload the folder config into data/, so that it becomes data/config (the settings). Then change the settings there;
#     do not upload the folder again, it would overwrite the changes;
#   - data/ keeps the station mapping, the GPS register and the Test list, and the files saved as they are downloaded:
#     the exports of the Tableau Avances / Retards (production plan) and of the cable team's tracker (their names are in
#     data/config/2_sources.csv);
#   - Data panel: read non_conformity, fto2_ai_labels, work_order_operation, mes_disruptions, and the settings kept in
#     Fusion: fto2_set_targets, fto2_set_cost, fto2_set_blackout, fto2_set_deliveries, fto2_set_eqmsn, fto2_set_plant,
#     fto2_set_part_prices, fto2_set_cables, fto2_set_gps, fto2_set_test (each one missing: its file in data/ is used);
#     write fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions, and while 'garder_anciennes_sorties' is oui
#     (data/config/2_parametres.csv) also fto2_dashboard_data, fto2_dashboard_data_missing_ids, fto2_parsed_defects,
#     fto2_parsed_defects_missing_ids.
#
# Run it as a script (python fto2_pipeline_notebook.py) or as the notebook fto2_pipeline_notebook.ipynb.

# %%
import sys
if "notebook_kit" not in sys.path:
    sys.path.insert(0, "notebook_kit")
for name in [m for m in sys.modules if m == "fto2" or m.startswith("fto2.")]:
    del sys.modules[name]   # the settings of data/config/ are read again at every run: no need to restart the kernel
from foundry.transforms import Dataset, Column
from fto2 import fusion
fusion.load(Dataset)   # the settings kept in Fusion (fto2_set_* in the Data panel); without them, the files of data/config
from fto2 import skywise

# %%
nc_t, def_t, dis_t = skywise.run(Dataset, Column)
