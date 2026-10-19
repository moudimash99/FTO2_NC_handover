import sys, re, pandas as pd
pd.set_option("display.width", 250)
D, R = sys.argv[1], sys.argv[2]
nc25 = pd.read_pickle(D+"/nc.pkl")
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number")
wo = pd.read_pickle(D+"/wo.pkl"); ot = wo.drop_duplicates("order_number").set_index("order_number").order_type
for name, nc in [("2025", nc25), ("2026", nc26)]:
    rows = []
    for n, s, w in zip(nc.notification_number, nc.linked_document.fillna(""), nc.work_order.fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.lstrip("0")):
        for p, o in re.findall(r"([A-Z]{2})_0*(\d+)", s):
            rows.append((n, p, o, o == w))
    L = pd.DataFrame(rows, columns=["nc","p","o","same_as_nc_work_order"])
    print(name, "share of link = NC.work_order, by prefix:", L.groupby("p").same_as_nc_work_order.agg(["mean","size"]).round(2).to_dict("index"))
    print(name, "  number pattern:", L.groupby("p").o.agg(lambda x: x.str[:3].value_counts().head(3).to_dict()).to_dict())
    hit = L[L.o.isin(ot.index)]
    print(name, "  in WO file -> order type:", hit.groupby("p").o.apply(lambda x: x.map(ot).value_counts().to_dict()).to_dict())
    # NC raised on an S03 order?
    w = nc.work_order.fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.lstrip("0")
    print(name, "  NCs whose own work_order is S03 in WO file:", w.map(ot).eq("S03").sum())
