import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 100); pd.set_option("display.max_rows", 100)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); nr = pd.read_pickle(D+"/nc_rw.pkl"); n26, n25 = nr["2026"], nr["2025"]
m = pd.read_pickle(D+"/calib.pkl"); ot = wo.drop_duplicates("order_number").set_index("order_number").order_type
# 1. REJ / EXC NCs with orders in file
for rule in ["REJ","EXC","DELETED"]:
    x = m[m.cnq_rule==rule]
    print(rule, "NCs with order in file:", len(x), "complete:", x.complete.sum(), "planned min median/sum:", x.total.median(), x.total.sum())
x = n26[(n26.cnq_rule=="REJ") & (n26.cnq_on_aec==1)]
print("REJ 2026 workflows:", x.workflow_list.value_counts().head(6).to_dict(), "| with rework order by wf:", x.groupby("workflow_list").has_rw.mean().round(2).head(6).to_dict())
# 2. quality-admin / NC handling ops booked on S03
s3 = wo[wo.order_type=="S03"].copy(); s3["im"] = pd.to_numeric(s3.labor_standard_value, errors="coerce").fillna(0)
tt = (s3.operation_short_text.fillna("")+" "+s3.operation_long_text.fillna("")).str.lower()
adm = s3[tt.str.contains(r"gestion nc|alerte qualit|retours? client|accompagnement prod|ad-hoc|recherche ibm|admin")]
print("\nNC-handling / quality admin ops on S03:", len(adm), "orders", adm.order_number.nunique(), "hours", round(adm.im.sum()/100,1))
print(adm[["order_number","order_program","order_msn","operation_short_text","work_center_description","im"]].assign(h=lambda d: d.im/100).drop(columns="im").to_string())
# 3. orders that exist but are not in the Sept file
n26["ct"] = pd.to_datetime(n26.creation_time, utc=True); n26["cl"] = pd.to_datetime(n26.closure_time, utc=True, errors="coerce")
w = n26[(n26.ct >= pd.Timestamp("2026-08-15", tz="UTC")) & n26.has_rw].copy()
w["in_file"] = w.rw.apply(lambda l: any(o in ot.index for o in l))
nf = w[~w.in_file]
print("\nrework order exists, not in Sept file:", len(nf), "| NC closed before 1 Sep:", (nf.cl < pd.Timestamp("2026-09-01", tz="UTC")).sum(), "| NC still open:", nf.cl.isna().sum(), "| status:", nf.status_open_closed.value_counts().to_dict())
# RWK without any rework order: what are they
for name, n in [("2025", n25), ("2026", n26)]:
    z = n[(n.cnq_rule=="RWK") & (n.cnq_on_aec==1) & (n.plant=="FTO2") & ~n.has_rw]
    print(f"\n{name} RWK FTO2-liable without rework order: {len(z)} | linked_document empty: {(z.linked_document=='').sum()} | TS only: {z.linked_document.str.contains('TS_').sum()}")
    print("  types:", z.Type_NC_auto.value_counts().to_dict(), "| user_dept:", z.user_department.value_counts().head(4).to_dict())
    print("  short texts:", z.description_short.head(8).tolist())
