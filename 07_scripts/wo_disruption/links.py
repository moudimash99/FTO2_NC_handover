import sys, re, pandas as pd
from collections import Counter
D, R = sys.argv[1], sys.argv[2]
wo = pd.read_pickle(D+"/wo.pkl"); nc25 = pd.read_pickle(D+"/nc.pkl")
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number")
print("nc26", len(nc26), pd.to_datetime(nc26.creation_time).min(), pd.to_datetime(nc26.creation_time).max())
def docs(s):
    return re.findall(r"([A-Z]{2})_0*(\d+)", s or "")
for name, nc in [("nc25", nc25), ("nc26", nc26)]:
    c = Counter(p for s in nc.linked_document.fillna("") for p, _ in docs(s))
    print(name, "linked_document prefixes:", c.most_common())
wo_orders = set(wo.order_number.str.lstrip("0"))
ot = wo.drop_duplicates("order_number").set_index(wo.drop_duplicates("order_number").order_number.str.lstrip("0")).order_type
print("WO orders", len(wo_orders), ot.value_counts().to_dict())
for name, nc in [("nc25", nc25), ("nc26", nc26)]:
    w = nc.work_order.dropna().astype(str).str.replace(r"\.0$","",regex=True).str.lstrip("0")
    hit = w[w.isin(wo_orders)]
    print(name, "NC.work_order in WO file:", hit.nunique(), "orders /", len(hit), "NCs of", len(w), "| types", ot.reindex(hit).value_counts().to_dict())
    rows = [(nc_, p, n) for nc_, s in zip(nc.notification_number, nc.linked_document.fillna("")) for p, n in docs(s)]
    L = pd.DataFrame(rows, columns=["nc","p","n"])
    L["hit"] = L.n.isin(wo_orders)
    print(name, "linked docs in WO file by prefix:", L.groupby("p").hit.agg(["sum","count"]).to_dict("index"))
    print(name, " order types of hits:", L[L.hit].groupby("p").n.apply(lambda x: ot.reindex(x).value_counts().to_dict()).to_dict())
