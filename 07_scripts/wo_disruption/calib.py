import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 100)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); nr = pd.read_pickle(D+"/nc_rw.pkl"); n26 = nr["2026"]
c26 = pd.read_pickle(D+"/cnq_nc26.pkl").set_index("notification_number"); d26 = pd.read_pickle(D+"/defs_nc26.pkl")
s3 = wo[wo.order_type=="S03"].copy(); s3["im"] = pd.to_numeric(s3.labor_standard_value, errors="coerce").fillna(0)
t = s3.operation_short_text.fillna("").str.lower()
s3["kind"] = np.select([t.str.contains(r"attestation|cl[ôo]ture|autoclos"), t.str.contains(r"inspection|contr[ôo]l"), t.str.contains(r"pr[ée]paration|analys"), t.str.contains(r"test")],
                       ["close","inspect","prep","test"], "work")
po = s3.pivot_table(index="order_number", columns="kind", values="im", aggfunc="sum", fill_value=0)/100*60   # minutes
po["total"] = po.sum(axis=1)
po["complete"] = s3.groupby("order_number").kind.apply(lambda k: (k=="close").any())
# NCs with their rework orders in the file
rows = [(n, o) for n, l in zip(n26.notification_number, n26.rw) for o in l if o in po.index]
L = pd.DataFrame(rows, columns=["nc","order"])
m = L.join(po, on="order").groupby("nc").agg({**{k:"sum" for k in ["close","inspect","prep","test","work","total"]}, "complete":"all"})
m = m.join(c26[["cnq_rule","cnq_on_aec","cnq_defect_lines","cnq_min_setup","cnq_min_hands_on","cnq_min_recheck","cnq_cost_total","cnq_final_inspection"]])
m = m.join(n26.set_index("notification_number")[["Type_NC_auto","creation_time"]])
m["model_comp"] = m.cnq_min_setup + m.cnq_min_hands_on + m.cnq_min_recheck
r = m[(m.cnq_rule=="RWK") & m.complete]
print("RWK NCs with complete rework order(s) in file:", len(r), "| all RWK with order in file:", (m.cnq_rule=="RWK").sum())
print("planned minutes per NC (median / mean):")
print(r[["prep","work","test","inspect","close","total","cnq_min_setup","cnq_min_hands_on","cnq_min_recheck","model_comp"]].agg(["median","mean","sum"]).round(0).to_string())
print("share of S03 orders with 0 planned min:", (r.total==0).mean().round(2))
print("\nby NC type (sum of minutes, planned vs model's setup+hands-on+recheck):")
g = r.groupby("Type_NC_auto").agg(n=("total","size"), planned_sum=("total","sum"), planned_median=("total","median"), model_sum=("model_comp","sum"), model_median=("model_comp","median"))
g["model/planned"] = (g.model_sum/g.planned_sum).round(2); print(g.round(0).to_string())
print("\nby number of defects:")
r = r.assign(nd=pd.cut(r.cnq_defect_lines, [-1,0,1,3,10,999], labels=["0","1","2-3","4-10",">10"]))
print(r.groupby("nd", observed=True).agg(n=("total","size"), planned_median=("total","median"), planned_mean=("total","mean"), model_median=("model_comp","median"), model_mean=("model_comp","mean")).round(0).to_string())
# single-defect NCs: planned minutes by class
one = r[r.cnq_defect_lines==1].index
cls = d26[d26.notification_number.isin(one)].drop_duplicates("notification_number").set_index("notification_number")[["sous_groupe","cnq_min_per_defect"]]
x = r.loc[one].join(cls)
print("\nsingle-defect NCs, planned total by class (n>=2):")
k = x.groupby("sous_groupe").agg(n=("total","size"), planned_median=("total","median"), planned_work_median=("work","median"), model_hands_on=("cnq_min_per_defect","first"), model_comp_median=("model_comp","median"))
print(k[k.n>=2].sort_values("n", ascending=False).round(0).to_string())
# what fixed part does S03 carry on 1-defect orders
print("\n1-defect NCs: prep median", x.prep.median(), "inspect", x.inspect.median(), "close", x.close.median(), "work", x.work.median(), "test", x.test.median())
m.to_pickle(D+"/calib.pkl")
