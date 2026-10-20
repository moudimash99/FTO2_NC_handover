# FTO2 NC dashboard, level 3: the two datasets the Slate dashboard reads.
# Run after the pipeline notebook (same Code Workspace): it reads that notebook's two output datasets, so the NC selection
# stays the pipeline's. Upload the folder notebook_kit next to the notebook (as nc_defect_parser.py already is).
#
# Datasets to add in the workspace's Data panel (alias = name used below):
#   read : fto2_dashboard_data, fto2_dashboard_data_missing_ids  (written by the pipeline notebook)
#          fto2_ai_labels  (upload notebook_kit/fto2_ai_labels.csv once as a dataset; append rows after each AI pass)
#   write: fto2_dash_nc, fto2_dash_defects  (new; sync both to Postgres for Slate as foundry_sync.fto2_dash_nc / fto2_dash_defects)
import sys
sys.path.insert(0, "notebook_kit")           # our copies first (parser v4.8, CNQ model, the build's data steps)

from foundry.transforms import Dataset
import fto2_core as core

frames = [Dataset.get("fto2_dashboard_data").read_table(format="pandas"),
          Dataset.get("fto2_dashboard_data_missing_ids").read_table(format="pandas")]
labels = Dataset.get("fto2_ai_labels").read_table(format="pandas")
nc_t, def_t, info, to_label = core.build(frames, labels, ref_dir="notebook_kit/ref")

Dataset.get("fto2_dash_nc").write_table(nc_t)
Dataset.get("fto2_dash_defects").write_table(def_t)
print("FTO2 dashboard tables:", info["nc_table"], "NCs,", info["defect_table"], "defect lines; level-3 CNQ on AEC:", info["level3_aec"], "EUR")
print("NCs created", info["created_from"], "to", info["created_to"], "| defect lines without an AI label (parser label used):", info["to_label"])

# lines for the next AI pass (once IT has approved the tool): a CSV to download from the workspace. Each line comes with its
# full text (snippet) and the NC's long text; the labels go back into fto2_ai_labels with the same notification_number, seq, snippet.
to_label.to_csv("fto2_lines_to_label.csv", index=False)
