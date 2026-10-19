# -*- coding: utf-8 -*-
"""
Run the CNQ calculation on two CSV exports, outside Foundry.

    python tests/run_local.py <nc.csv> <defects.csv> [<extra_nc_columns.csv>]

The third file is a STOPGAP: the v4.7 NC export has no decision, liability, NC type or product
(nor linked_document / work_order, used to find the NC's rework order).
Until the pipeline adds them, they are joined here from the earlier Skywise export by NC number.
Writes sample_output/*.csv, params/*.csv and tests/expected_totals.json.
"""
import json, os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from cnq.cnq_core import compute_cnq, parameters_as_tables  # noqa: E402


def load(nc_path, defects_path, extra_path=None):
    nc = pd.read_csv(nc_path, low_memory=False)
    defects = pd.read_csv(defects_path, low_memory=False)
    if extra_path:
        x = pd.read_csv(extra_path, low_memory=False)
        x["type_nc"] = x["GPS_Type_NC"].where(x["GPS_Type_NC"].notna(), x["Type_NC_auto"])
        keep = ["notification_number", "decision_status", "liability", "type_nc", "produit"] + [c for c in ("linked_document", "work_order") if c in x.columns]
        x = x.rename(columns={"Produit_auto": "produit"})[keep]
        nc = nc.merge(x, on="notification_number", how="left")
    return nc, defects


def totals(nc, d):
    a = nc[nc.cnq_on_aec == 1]
    return {
        "nc_rows": int(len(nc)), "nc_on_aec": int(len(a)), "nc_no_master_data": int((nc.cnq_liability_group == "No master data").sum()),
        "cost_aec": round(float(nc.cnq_cost_aec.sum()), 2), "cost_all": round(float(nc.cnq_cost_total.sum()), 2),
        "level1_airbus_aec": round(float(a.cnq_cost_airbus.sum()), 2), "level2_global_aec": round(float(a.cnq_cost_global.sum()), 2),
        "level3_detailed_aec": round(float(a.cnq_cost_total.sum()), 2),
        "cost_admin_aec": round(float(a.cnq_cost_admin.sum()), 2), "cost_work_aec": round(float(a.cnq_cost_work.sum()), 2),
        "cost_engineering_aec": round(float(a.cnq_cost_engineering.sum()), 2), "cost_material_aec": round(float(a.cnq_cost_material.sum()), 2),
        "defect_lines": int(len(d)), "defect_lines_costed": int(d.cnq_line_costed.sum()),
        "cost_direct_lines": round(float(d.cnq_cost_direct.sum()), 2),
        "by_rule_aec": {k: round(float(v), 2) for k, v in a.groupby("cnq_rule").cnq_cost_total.sum().items()},
    }


if __name__ == "__main__":
    nc, defects = load(*sys.argv[1:4])
    nc_out, d_out = compute_cnq(nc, defects)
    nc_out.to_csv(os.path.join(ROOT, "sample_output", "fto2_nc_cnq.csv"), index=False)
    d_out.to_csv(os.path.join(ROOT, "sample_output", "fto2_defects_cnq.csv"), index=False)
    for name, t in zip(("cnq_steps", "cnq_rules", "cnq_defect_times"), parameters_as_tables()):
        t.to_csv(os.path.join(ROOT, "params", name + ".csv"), index=False)
    t = totals(nc_out, d_out)
    json.dump(t, open(os.path.join(HERE, "expected_totals.json"), "w"), indent=2, ensure_ascii=False)
    print(json.dumps(t, indent=2, ensure_ascii=False))
