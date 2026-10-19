import sys, pandas as pd, warnings
warnings.filterwarnings("ignore")
D, REPO = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO + "/cnq_handoever")
from cnq.cnq_core import compute_cnq
nr = pd.read_pickle(D+"/nc_rw.pkl")
erma = set(nr["2025"][nr["2025"].user_department.str.contains("ERMA", na=False)].notification_number.astype(str))
for tag in ["nc26", "nc25"]:
    nc = pd.read_pickle(f"{D}/cnq_{tag}.pkl"); d = pd.read_pickle(f"{D}/defs_{tag}.pkl")
    nc = nc[[c for c in nc.columns if not c.startswith("cnq_")]]; d = d[[c for c in d.columns if not c.startswith("cnq_")]]
    links = nr["2025" if tag == "nc25" else "2026"][["notification_number", "linked_document", "work_order"]].astype({"notification_number": str})
    nc = nc.drop(columns=[c for c in ("linked_document", "work_order") if c in nc.columns]).merge(links, on="notification_number", how="left")
    old = pd.read_pickle(f"{D}/cnq_{tag}.pkl")
    out, _ = compute_cnq(nc, d)
    for lab, o in [("before", old), ("after", out)]:
        o = o.copy(); o["dt"] = pd.to_datetime(o.date_creation, utc=True, errors="coerce")
        if tag == "nc25": a = o[(o.cnq_on_aec==1)&(o.plant=="FTO2")&(o.dt.dt.year==2025)&(~o.notification_number.isin(erma))]; name = "2025 Jan-Dec, plant FTO2, without ERMA"
        else: a = o[(o.cnq_on_aec==1)&(o.plant=="FTO2")&(o.dt>=pd.Timestamp("2026-02-01",tz="UTC"))&(o.dt<pd.Timestamp("2026-10-01",tz="UTC"))]; name = "2026 Feb-Sep, plant FTO2"
        print(f"{name:42s} {lab:6s} NCs {len(a)}  L3 {a.cnq_cost_total.sum():>10,.0f}  per NC {a.cnq_cost_total.mean():6.0f}  L2 {a.cnq_cost_global.sum():>10,.0f}  L1 {a.cnq_cost_airbus.sum():>10,.0f}")
        if lab == "after": print("   by type:", a.groupby("type_nc").cnq_cost_total.sum().round(0).to_dict())
    if tag == "nc26":
        r = out[(out.cnq_on_aec==1) & (out.cnq_customer_return==1)]; r0 = old[(old.cnq_on_aec==1) & (old.cnq_customer_return==1)]
        print(f"   customer returns 2026 (all months): {len(r)} NCs, {r0.cnq_cost_total.sum():,.0f} -> {r.cnq_cost_total.sum():,.0f}")
