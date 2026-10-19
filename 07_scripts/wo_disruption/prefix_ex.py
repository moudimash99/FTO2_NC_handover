import sys, re, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
D, R = sys.argv[1], sys.argv[2]
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number").set_index("notification_number")
wo = pd.read_pickle(D+"/wo.pkl")
wo["im"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)
og = wo.groupby("order_number").agg(type=("order_type","first"), ops=("im","size"), im=("im","sum"), hdr=("material_header_description","first"),
     first_ops=("operation_short_text", lambda x: " | ".join(x.astype(str).head(4))), sched=("earliest_scheduled_start_wait_date","min"))
rows = []
for n, s in nc26.linked_document.fillna("").items():
    for p, o in re.findall(r"([A-Z]{2})_0*(\d+)", s):
        if o in og.index: rows.append((n, p, o))
L = pd.DataFrame(rows, columns=["nc","p","o"]).join(og, on="o")
L["nc_wo"] = L.nc.map(nc26.work_order.str.lstrip("0")); L["same"] = L.nc_wo == L.o
L["created"] = L.nc.map(nc26.creation_time).str[:10]; L["wf"] = L.nc.map(nc26.workflow_list); L["typ"] = L.nc.map(nc26.Type_NC_auto)
L["all_links"] = L.nc.map(nc26.linked_document)
for (p, t), g in L.groupby(["p","type"]):
    print(f"\n=== {p} -> {t}: {len(g)} links, same as NC.work_order: {g.same.sum()}")
    print(g[["nc","created","typ","wf","same","sched","ops","im","first_ops","all_links"]].head(6).to_string(index=False))
