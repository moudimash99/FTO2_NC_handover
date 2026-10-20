# FTO2 NC dashboard, level 3: the three datasets the Slate dashboard reads.
# Run after the pipeline notebook (same Code Workspace): it reads that notebook's two NC outputs, so the NC selection stays the
# pipeline's. Upload the folder notebook_kit next to the notebook (as nc_defect_parser.py already is).
#
# Datasets to add in the workspace's Data panel (the alias is the name used below; change the names here if yours differ):
#   read : fto2_dashboard_data, fto2_dashboard_data_missing_ids  (written by the pipeline notebook; kept apart, each NC is tagged
#          with its origin: normal / missing_ids)
#          fto2_ai_labels  (upload notebook_kit/fto2_ai_labels.csv once as a dataset; append rows after each AI pass)
#          Work_Order_Operation  -> alias in WO_OPERATIONS: the rework orders' planned times (cost of the rework)
#          MES Disruptions       -> alias in MES_DISRUPTIONS: the aléas (alert time of each NC, and the disruption block)
#   write: fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions  (new; sync the three to Postgres for Slate, schema foundry_sync)
# Leave WO_OPERATIONS or MES_DISRUPTIONS empty to run without them (the model's times; no disruption block).
WO_OPERATIONS = "work_order_operation"
MES_DISRUPTIONS = "mes_disruptions"
SINCE = "2025-12-01 00:00:00"                # operations and aléas read from this date (the NCs start mid-December 2025)
import sys
sys.path.insert(0, "notebook_kit")           # our copies first (parser v4.8, CNQ model, the build's data steps)

from foundry.transforms import Dataset, Column
import fto2_core as core

frames = []
for name in ("fto2_dashboard_data", "fto2_dashboard_data_missing_ids"):
    f = Dataset.get(name).read_table(format="pandas")
    f["_source"] = name                      # the origin of each NC: normal, or missing_ids when the name holds "missing"
    frames.append(f)
labels = Dataset.get("fto2_ai_labels").read_table(format="pandas")
ops = dis = None
if WO_OPERATIONS:
    ops = (Dataset.get(WO_OPERATIONS)
           .where((Column.get("plant") == "FTO2") & (Column.get("order_type") == "S03"))
           .select("order_number", "order_type", "operation_number", "operation_short_text", "plant", "labor_standard_value",
                   "unit_of_measure_for_the_standard_value_labor", "setup_standard_value", "unit_of_measure_for_the_standard_value_setup")
           .read_table(format="pandas"))
if MES_DISRUPTIONS:
    dis = (Dataset.get(MES_DISRUPTIONS)
           .where((Column.get("plant") == "FTO2") & (Column.get("open_date_time") >= SINCE))
           .select("disruption_id", "plant", "physical_station", "work_order", "wo_designation", "ds_material", "type_desc", "open_date_time",
                   "open_date_time_tz", "status", "time_lost", "program", "comment")
           .read_table(format="pandas"))
nc_t, def_t, dis_t, info, to_label = core.build(frames, labels, ref_dir="notebook_kit/ref", ops=ops, dis=dis)

Dataset.get("fto2_dash_nc").write_table(nc_t)
Dataset.get("fto2_dash_defects").write_table(def_t)
Dataset.get("fto2_dash_disruptions").write_table(dis_t)
print("FTO2 dashboard tables:", info["nc_table"], "NCs,", info["defect_table"], "defect lines,", info["disruption_table"], "aléas; level-3 CNQ on AEC:", info["level3_aec"], "EUR")
print("NCs created", info["created_from"], "to", info["created_to"], "| origin:", info["origin"], "| defect lines without an AI label (parser label used):", info["to_label"])
print("rework orders:", info["rework_orders"], "| aléas:", info.get("aleas", "not read"))

# lines for the next AI pass (once IT has approved the tool): a CSV to download from the workspace. Each line comes with its
# full text (snippet) and the NC's long text; the labels go back into fto2_ai_labels with the same notification_number, seq, snippet.
to_label.to_csv("fto2_lines_to_label.csv", index=False)
