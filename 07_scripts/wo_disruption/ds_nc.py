import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 100); pd.set_option("display.max_rows", 200)
D, R = sys.argv[1], sys.argv[2]
ds = pd.read_pickle(D+"/ds.pkl"); cnq = pd.read_pickle(D+"/nc26_cnq.pkl")
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number")
nc26["ct"] = pd.to_datetime(nc26.creation_time, utc=True)
print("nc26 per month:", nc26.ct.dt.strftime("%Y-%m").value_counts().sort_index().to_dict())
ds["ot"] = pd.to_datetime(ds.open_date_time + ds.open_date_time_tz, utc=True)
ds["wo"] = ds.work_order.fillna("").str.lstrip("0"); nc26["wo"] = nc26.work_order.fillna("").str.lstrip("0")
ds["tl"] = pd.to_numeric(ds.time_lost)
# restrict to the window where nc26 is complete: from first full month
start = pd.Timestamp("2026-07-01", tz="UTC")
m = ds[ds.wo!=""].merge(nc26[nc26.wo!=""][["notification_number","wo","ct","Type_NC_auto","trigger","plant","station"]], on="wo")
m["dh"] = (m.ct - m.ot).dt.total_seconds()/3600
w = m[(m.dh>=-2)&(m.dh<=72)].sort_values("dh")
first = w.drop_duplicates("disruption_id")
ds["has_nc"] = ds.disruption_id.isin(first.disruption_id)
print("\nShare of disruptions followed by an NC on same WO within 72h, by type (all months):")
print(ds.groupby("type_desc").agg(n=("has_nc","size"), with_nc=("has_nc","sum"), time_lost_sum_h=("tl", lambda x: round(x.sum()/60)), tl_median=("tl","median")).assign(pct=lambda x: (100*x.with_nc/x.n).round(0)).to_string())
q = ds[ds.type_desc.str.startswith("QLS", na=False)]
print("\nQLS disruptions with work_order:", q.wo.ne("").sum(), "of", len(q))
print("delay NC - disruption (h), QLS:", first[first.type_desc.str.startswith("QLS")].dh.describe(percentiles=[.25,.5,.75,.9]).round(1).to_dict())
print("QLS time_lost (min):", q.tl.describe(percentiles=[.25,.5,.75,.9]).round(0).to_dict())
print("QLS time_lost when NC follows:", q[q.has_nc].tl.describe(percentiles=[.25,.5,.75]).round(0).to_dict())
print("QLS by month:", q.ot.dt.strftime("%m").value_counts().sort_index().to_dict())
# Coverage from the NC side, Jul-Sep 2026 where nc26 is complete and both datasets overlap
shop = nc26[(nc26.ct>=start)&(nc26.ct<pd.Timestamp("2026-10-01",tz="UTC"))&(nc26.plant=="FTO2")]
shop = shop[shop.wo!=""]
linked_ncs = set(first.notification_number)
shop["had_disruption"] = shop.notification_number.isin(linked_ncs)
print("\nFTO2 NCs Jul-Sep 2026 with a WO:", len(shop), "| preceded by a disruption:", shop.had_disruption.sum())
print(shop.groupby("Type_NC_auto").had_disruption.agg(["size","sum"]).to_string())
print(shop.groupby(shop.station.str[:2]).had_disruption.agg(["size","sum"]).to_string())
# examples
print(first[first.type_desc.str.startswith("QLS")][["disruption_id","notification_number","dh","tl","comment"]].head(8).assign(comment=lambda x: x.comment.str.replace(r"\s+"," ",regex=True).str[:90]).to_string())
# time_to_get_ack/fix units: compare with clock
print("\nresponsible groups for QLS:", q.responsible_group_desc.value_counts().head(8).to_dict())
first.to_pickle(D+"/ds_nc_links.pkl"); ds.to_pickle(D+"/ds2.pkl")
