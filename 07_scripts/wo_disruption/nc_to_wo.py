import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 100)
D, R = sys.argv[1], sys.argv[2]
wo = pd.read_pickle(D+"/wo.pkl"); ot = wo.drop_duplicates("order_number").set_index("order_number").order_type
nc25 = pd.read_pickle(D+"/nc.pkl")
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number")
c25 = pd.read_pickle(D+"/cnq_nc25.pkl").set_index("notification_number"); c26 = pd.read_pickle(D+"/cnq_nc26.pkl").set_index("notification_number")
def rework_orders(row):
    own = str(row.work_order or "").replace(".0","").lstrip("0")
    return sorted({o for p, o in re.findall(r"([A-Z]{2})_0*(\d+)", row.linked_document or "") if p in ("AW","WO","RS") and o != own})
out = {}
for name, nc, c in [("2025", nc25, c25), ("2026", nc26, c26)]:
    nc = nc.copy(); nc["notification_number"] = nc.notification_number.astype(str)
    nc["linked_document"] = nc.linked_document.where(nc.linked_document.notna(), "")
    nc["work_order"] = nc.work_order.where(nc.work_order.notna(), "")
    nc["rw"] = nc.apply(rework_orders, axis=1); nc["has_rw"] = nc.rw.str.len() > 0
    nc = nc.join(c[["cnq_rule","cnq_on_aec","type_nc","cnq_defect_lines"]] if "type_nc" in c.columns else c[["cnq_rule","cnq_on_aec","cnq_defect_lines"]], on="notification_number")
    if "Type_NC_auto" not in nc.columns: nc["Type_NC_auto"] = nc.type_nc
    nc["year_ok"] = pd.to_datetime(nc.creation_time, utc=True, errors="coerce").dt.year == int(name)
    a = nc[(nc.cnq_on_aec == 1) & nc.year_ok & (nc.plant == "FTO2")]
    print(f"\n===== {name}: FTO2-liable NCs at plant FTO2: {len(a)} | with a rework order: {a.has_rw.sum()} ({100*a.has_rw.mean():.0f}%)")
    print("by decision:", a.groupby("cnq_rule").has_rw.agg(["size","sum"]).T.to_dict())
    r = a[a.cnq_rule == "RWK"]
    print(f"RWK NCs: {len(r)}, with rework order {r.has_rw.sum()} ({100*r.has_rw.mean():.0f}%)")
    print(r.groupby("Type_NC_auto").has_rw.agg(n="size", with_order="sum").assign(pct=lambda x: (100*x.with_order/x.n).round(0)).to_string())
    print(r.groupby(r.workflow_list.fillna("(none)")).has_rw.agg(n="size", with_order="sum").assign(pct=lambda x: (100*x.with_order/x.n).round(0)).sort_values("n", ascending=False).head(12).to_string())
    print("by defect count:", r.groupby(pd.cut(r.cnq_defect_lines, [-1,0,1,3,10,999], labels=["0","1","2-3","4-10",">10"])).has_rw.agg(["size","mean"]).round(2).T.to_dict())
    print("by month:", r.groupby(pd.to_datetime(r.creation_time, utc=True).dt.strftime("%m")).has_rw.mean().round(2).to_dict())
    print("linked_document empty:", (r.linked_document == "").sum())
    out[name] = nc
# 2026 Aug-Sep: rework order exists -> in Sept WO file?
n = out["2026"]; n["ct"] = pd.to_datetime(n.creation_time, utc=True)
w = n[(n.ct >= pd.Timestamp("2026-08-15", tz="UTC")) & n.has_rw]
w = w.assign(in_file=w.rw.apply(lambda l: any(o in ot.index for o in l)))
print("\n2026 NCs created 15 Aug-28 Sep with a rework order:", len(w), "| order in the Sept file:", w.in_file.sum())
pd.to_pickle(out, D+"/nc_rw.pkl")
# ERMA check
e = out["2025"]; print("\n2025 ERMA user_department NCs:", e.user_department.str.contains("ERMA", na=False).sum(), "| FTO2-liable:", (e.user_department.str.contains("ERMA", na=False) & (e.cnq_on_aec == 1)).sum())
