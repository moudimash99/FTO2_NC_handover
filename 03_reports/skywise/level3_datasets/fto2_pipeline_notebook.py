# FTO2 NC pipeline and dashboard tables (Skywise Code Workspace).
#
# What it does: reads the NCs, applies the rules of data/config/, and writes the dashboard's three tables
# fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions (the steps are in notebook_kit/fto2/skywise.py).
#
# Before the first run:
#   - upload the folder notebook_kit next to this notebook (the code; upload it again after each update);
#   - upload the folder config into data/, so that it becomes data/config (the settings). Then change the settings there;
#     do not upload the folder again, it would overwrite the changes;
#   - data/ keeps the station mapping, the GPS register and the Test list (their names are in data/config/2_sources.csv);
#   - Data panel: read non_conformity, fto2_ai_labels, work_order_operation, mes_disruptions;
#     write fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions, and while 'garder_anciennes_sorties' is oui
#     (data/config/2_parametres.csv) also fto2_dashboard_data, fto2_dashboard_data_missing_ids, fto2_parsed_defects,
#     fto2_parsed_defects_missing_ids.
#
# Run it as a script (python fto2_pipeline_notebook.py) or as the notebook fto2_pipeline_notebook.ipynb.

# %%
import sys
sys.path.insert(0, "notebook_kit")
from foundry.transforms import Dataset, Column
from fto2 import skywise

# %%
nc_t, def_t, dis_t = skywise.run(Dataset, Column)
