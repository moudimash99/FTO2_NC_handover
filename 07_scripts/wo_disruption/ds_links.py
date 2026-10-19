import sys, re, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
D, R = sys.argv[1], sys.argv[2]
wo = pd.read_pickle(D+"/wo.pkl"); ds = pd.read_pickle(D+"/ds.pkl")
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number")
ncs = set(nc26.notification_number.str.lstrip("0"))
txt = ds.comment.fillna("") + " || " + ds.solution.fillna("")
ds["nc_in_text"] = txt.str.findall(r"(?<!\d)(2\d{8})(?!\d)")
ds["ord_in_text"] = txt.str.findall(r"(?<!\d)(10\d{8})(?!\d)")
print("disruptions mentioning a 9-digit 2xxxxxxxx number:", (ds.nc_in_text.str.len()>0).sum())
print("  ...of which in our 2026 NC set:", ds.nc_in_text.apply(lambda l: any(x in ncs for x in l)).sum())
print("disruptions mentioning a 10xxxxxxxx order:", (ds.ord_in_text.str.len()>0).sum())
woset = set(wo.order_number); ot = wo.drop_duplicates("order_number").set_index("order_number").order_type
hits = [o for l in ds.ord_in_text for o in l if o in woset]
print("  ...orders in WO file:", len(hits), pd.Series(hits).map(ot).value_counts().to_dict())
print("mention 'NC' word:", txt.str.contains(r"\bNC\b", case=False).sum())
print(pd.crosstab(ds.type_desc, ds.nc_in_text.str.len()>0))
print(pd.crosstab(ds.type_desc, txt.str.contains(r"\bNC\b|non.?conf", case=False)))
print(ds[ds.nc_in_text.str.len()>0][["type_desc","comment","solution","time_lost"]].head(12).to_string())
# key join: work_order + operation
nc26["wo"] = nc26.work_order.str.lstrip("0"); nc26["op"] = nc26.operation.fillna("").str.replace(r"\.0$","",regex=True).str.zfill(4)
ds["wo"] = ds.work_order.fillna("").str.lstrip("0")
m = ds[ds.wo!=""].merge(nc26[["notification_number","wo","op","creation_time","description_short"]], on="wo")
m["dt_h"] = (pd.to_datetime(m.creation_time, utc=True) - pd.to_datetime(m.open_date_time+m.open_date_time_tz, utc=True)).dt.total_seconds()/3600
print("disruption-NC pairs sharing work_order:", len(m), "disruptions", m.disruption_id.nunique(), "NCs", m.notification_number.nunique())
close = m[(m.dt_h>-2)&(m.dt_h<72)]
print("  NC raised within -2h..+72h of disruption:", close.disruption_id.nunique(), "disruptions /", close.notification_number.nunique(), "NCs")
print(close.type_desc.value_counts().to_string())
same_op = close[close.op==close.operation]
print("  + same operation:", same_op.disruption_id.nunique())
