import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 200)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); wo["min"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)*0.6
fam = pd.read_pickle(D+"/s03_family.pkl"); m = pd.read_pickle(D+"/calib.pkl"); d26 = pd.read_pickle(D+"/defs_nc26.pkl")
nr = pd.read_pickle(D+"/nc_rw.pkl"); n26 = nr["2026"]
s3 = wo[(wo.order_type=="S03") & wo.order_number.isin(fam[fam.family=="FTO2 shop floor"].index)].copy()
t = s3.operation_short_text.fillna("").str.lower()
rt = s3[t.str.contains(r"\btest|tester|essai|continuit|emi\b|sonn")]
print("Re-test ops on shop-floor rework orders:", len(rt), "| with planned time:", (rt["min"]>0).sum())
print(rt.groupby(rt.operation_short_text.str[:45])["min"].agg(ops="size", median="median", max="max").sort_values("ops", ascending=False).head(12).round(0).to_string())
# rework orders of TEST NCs: structure
rows = [(n, o) for n, l in zip(n26.notification_number, n26.rw) for o in l if o in fam.index]
L = pd.DataFrame(rows, columns=["nc","order"]).merge(n26[["notification_number","Type_NC_auto"]], left_on="nc", right_on="notification_number")
tn = L[L.Type_NC_auto=="TEST"]
ops = wo[wo.order_number.isin(tn.order)]
print("\nRework orders of TEST NCs:", tn.order.nunique(), "| op texts (planned min median):")
print(ops.groupby(ops.operation_short_text.str[:45])["min"].agg(ops="size", median="median", total="sum").sort_values("ops", ascending=False).head(10).round(0).to_string())
# connection errors: planned rework vs number of errors, NCs whose defects are only connection errors
conn_cls = {"Inversion", "Erreur de branchement", "Non connecté"}
dd = d26[d26.notification_number.isin(m.index)]
comp = dd.groupby("notification_number").agg(n=("sous_groupe","size"), n_conn=("sous_groupe", lambda x: x.isin(conn_cls).sum()))
x = m[(m.cnq_rule=="RWK") & m.complete].join(comp, how="inner")
only = x[(x.n_conn == x.n) & (x.n > 0)]
print("\nReworked NCs with only connection errors and a complete rework order:", len(only))
print(only[["n","total","work","test","Type_NC_auto"]].sort_values("n").to_string())
if len(only) >= 3:
    b, a = np.polyfit(only.n, only.total, 1)
    print(f"fit: planned minutes = {a:.0f} + {b:.1f} x errors | median per error: {(only.total/only.n).median():.1f} | total planned / total errors: {only.total.sum()/only.n.sum():.1f}")
    print("model today: 35 min per error + 50 setup (floor 60)")
