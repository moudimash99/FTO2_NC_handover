import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 200)
D, REPO = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO + "/cnq_handoever")
from cnq.cnq_core import compute_cnq
wo = pd.read_pickle(D+"/wo.pkl"); ds = pd.read_pickle(D+"/ds.pkl")
R = REPO + "/06_input_data"
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number")
defs = pd.read_csv(REPO+"/05_outputs/fto2_parsed_defects_v4_8.csv", dtype=str, encoding="utf-8-sig")
# ---- CNQ model on 2026 NCs
nc = nc26.rename(columns={"status_open_closed":"statut","creation_time":"date_creation"}).copy()
nc["type_nc"] = nc.GPS_Type_NC.where(nc.GPS_Type_NC.notna(), nc.Type_NC_auto)
per = defs.drop_duplicates("notification_number").set_index("notification_number").perimetre
nc["perimetre"] = nc.notification_number.map(per)
nc_out, d_out = compute_cnq(nc[["notification_number","statut","decision_status","liability","liability_description","date_creation","type_nc","perimetre"]], defs[defs.perimetre.notna()])
print("defect lines with unknown class:", (d_out.cnq_time_known==0).sum(), "of", len(d_out), d_out[d_out.cnq_time_known==0].sous_groupe.value_counts().head(5).to_dict())
nc_out.to_pickle(D+"/nc26_cnq.pkl")
# ---- NC -> S03 orders
s3 = wo[wo.order_type=="S03"].copy()
s3["im"] = pd.to_numeric(s3.labor_standard_value, errors="coerce").fillna(0)
s3set = set(s3.order_number)
links = []
for n, s in zip(nc26.notification_number, nc26.linked_document.fillna("")):
    for p, o in re.findall(r"([A-Z]{2})_0*(\d+)", s):
        if o in s3set: links.append((n, o, "linked_document "+p))
txt = s3.operation_short_text.fillna("")+" "+s3.operation_long_text.fillna("")
for o, t in zip(s3.order_number, txt):
    for n in re.findall(r"(?<!\d)(2\d{8})(?!\d)", t):
        links.append((n, o, "S03 text"))
L = pd.DataFrame(links, columns=["nc","order","how"]).drop_duplicates(["nc","order"])
print("links:", len(L), L.how.value_counts().to_dict(), "| NCs", L.nc.nunique(), "orders", L.order.nunique(), "| in nc26:", L.nc.isin(nc26.notification_number).sum())
print("orders serving >1 NC:", (L.groupby("order").nc.nunique()>1).sum(), "| NCs with >1 order:", (L.groupby("nc").order.nunique()>1).sum())
print("S03 orders with no NC link found:", len(s3set - set(L.order)), "of", len(s3set))
L.to_pickle(D+"/nc_s03_links.pkl")
# ---- classify S03 ops
def kind(t):
    t = t.lower()
    if re.search(r"attestation|cl[ôo]ture|removed due", t): return "close/attest"
    if re.search(r"inspection|contr[ôo]l|v[ée]rif", t): return "inspection"
    if re.search(r"pr[ée]paration|analys", t): return "prep/analysis"
    if re.search(r"test", t): return "test"
    return "work"
s3["kind"] = s3.operation_short_text.fillna("").map(kind)
print(s3.groupby("kind").im.agg(["count","sum","median"]).assign(h=lambda x: x["sum"]/100).round(1).to_string())
per_order = s3.pivot_table(index="order_number", columns="kind", values="im", aggfunc="sum", fill_value=0)
per_order["total_im"] = per_order.sum(axis=1); per_order["n_ops"] = s3.groupby("order_number").size()
per_order["wc"] = s3.groupby("order_number").work_center_description.agg(lambda x: x.value_counts().index[0])
print("S03 per order (IM):", per_order.total_im.describe().round(0).to_dict())
per_order.to_pickle(D+"/s03_orders.pkl")
# ---- compare for linked NCs in the 2026 set (1 order per NC to keep it clean -> sum orders per NC)
m = L[L.nc.isin(nc_out.notification_number)].merge(per_order, left_on="order", right_index=True)
pn = m.groupby("nc")[["total_im","work","prep/analysis","inspection","test","close/attest"]].sum()
pn = pn.join(nc_out.set_index("notification_number")[["cnq_rule","cnq_on_aec","cnq_defect_lines","cnq_min_hands_on","cnq_min_setup","cnq_min_support","cnq_min_recheck","cnq_cost_total"]])
pn["s03_min"] = pn.total_im*0.6; pn["s03_work_min"] = (pn.work+pn.test)*0.6
pn["model_work_min"] = pn.cnq_min_hands_on + pn.cnq_min_setup
print("NCs compared:", len(pn), pn.cnq_rule.value_counts().to_dict(), "on AEC:", pn.cnq_on_aec.sum())
r = pn[pn.cnq_rule.isin(["RWK","EXC"])]
print("RWK/EXC NCs:", len(r))
print(r[["s03_min","s03_work_min","model_work_min","cnq_min_hands_on","cnq_defect_lines"]].describe().round(0).to_string())
print("sum s03_min", round(r.s03_min.sum()), "sum s03_work_min", round(r.s03_work_min.sum()), "sum model work", round(r.model_work_min.sum()), "model hands-on", round(r.cnq_min_hands_on.sum()))
print("corr work vs model hands-on:", np.corrcoef(r.s03_work_min, r.cnq_min_hands_on)[0,1].round(2), "spearman", r[["s03_work_min","cnq_min_hands_on"]].corr("spearman").iloc[0,1].round(2))
pn.to_pickle(D+"/s03_vs_model.pkl")
print(r.sort_values("s03_min", ascending=False)[["s03_min","s03_work_min","model_work_min","cnq_defect_lines"]].head(10).round(0).to_string())
