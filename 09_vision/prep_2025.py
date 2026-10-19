"""2025 NCs for the vision page: the same scope and parser as the 2026 dashboard, no NC text kept.

Input: the folder unpacked from 06_input_data/work_orders_disruptions_nc2025.rar (branch main),
       which holds split_part_nc_1..4.csv (Skywise NCs, plant FTO2, created 3 Jan 2025 - 30 Jan 2026).
Output: 09_vision/data/nc_2025.csv and 09_vision/data/defects_2025.csv.

Scope, as the 2026 pipeline: FTO2 in liability, not deleted, user_department without ERMA.
Phase (production type), as Programme_auto: FTI if constituent_assembly starts with WY or WA,
REC if workflow_list matches the REC pattern, else SERIE. Defects come from parser v4.8 (02_dashboard_pack).

    unar -o <W> 06_input_data/work_orders_disruptions_nc2025.rar
    python3 -I 09_vision/prep_2025.py <W>/wo <repo>
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

SRC, REPO = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, "02_dashboard_pack", "skywise_nc_dashboard_v48", "1_pipeline"))
sys.path.insert(0, os.path.join(REPO, "09_vision"))
import fto2_logic as L  # noqa: E402
from pins import pin_pair  # noqa: E402

L.PERIOD_START, L.PERIOD_END = "2025-01-01", "2026-01-01"

files = sorted(glob.glob(os.path.join(SRC, "split_part_nc_*.csv")))
sap = pd.concat([pd.read_csv(f, dtype=str, encoding="utf-8-sig", keep_default_na=False, na_values=[""]) for f in files], ignore_index=True)
sap["notification_number"] = sap.notification_number.astype(str)
ts = pd.to_datetime(sap.creation_time, utc=True)
wf = sap.workflow_list.fillna("")
nc = pd.DataFrame({
    "notification_number": sap.notification_number,
    "date": ts.dt.strftime("%Y-%m-%d"),                      # UTC day, as fto2_logic.nc_fields
    "ligne": sap.programme.map(L._ligne),
    "msn": sap.msn,
    "phase": np.where(sap.constituent_assembly.fillna("").str.match(r"^(WY|WA)"), "FTI",
                      np.where(wf.str.contains(r"\bREC\b|-CRE|-PNC|A30-REJ-PVU2"), "REC", "SERIE")),
    "in_scope": (sap.liability.fillna("").str.contains("FTO2") & ~sap.status_open_closed.eq("deleted")
                 & ~sap.user_department.str.contains("ERMA", na=False)).astype(int),
})
nc = nc[nc.date < "2026-01-01"]

defects = L.build_defects(sap)
defects = defects[defects.notification_number.isin(nc.notification_number)]
pins = defects.text.map(pin_pair)
out = pd.DataFrame({
    "notification_number": defects.notification_number, "seq": defects.seq,
    "categorie": defects.groupe, "rca": defects.rca_nom,
    "cable": defects.defaut_cable.astype(bool).astype(int), "mineur": defects.mineur.astype(bool).astype(int),
    "fin": defects.fin, "pin_a": pins.str[0], "pin_b": pins.str[1],
})

os.makedirs(os.path.join(REPO, "09_vision", "data"), exist_ok=True)
nc.to_csv(os.path.join(REPO, "09_vision", "data", "nc_2025.csv"), index=False)
out.to_csv(os.path.join(REPO, "09_vision", "data", "defects_2025.csv"), index=False)
s = nc[nc.in_scope == 1]
print("2025 NCs:", len(nc), "| in FTO2 scope:", len(s), s.phase.value_counts().to_dict(), "| defects on them:", out.notification_number.isin(s.notification_number).sum())
