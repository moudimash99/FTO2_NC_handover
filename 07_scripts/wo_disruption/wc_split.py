import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 200)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); o = pd.read_pickle(D+"/s03_status.pkl"); m = pd.read_pickle(D+"/calib.pkl")
s3 = wo[wo.order_type=="S03"].copy(); s3["im"] = pd.to_numeric(s3.labor_standard_value, errors="coerce").fillna(0)
# 0. redo model vs planned without the quality re-check
r = m[(m.cnq_rule=="RWK") & m.complete].copy()
r["model_work"] = r.cnq_min_setup + r.cnq_min_hands_on
print("84 NCs: planned", round(r.total.sum()), "| model setup+defects", round(r.model_work.sum()), "| ratio", round(r.model_work.sum()/r.total.sum(),2))
print("  of which planned on 'Inspection' ops:", round(r.inspect.sum()), "| close ops:", round(r.close.sum()))
print(r.groupby("Type_NC_auto").agg(n=("total","size"), planned=("total","sum"), model=("model_work","sum")).assign(ratio=lambda x: (x.model/x.planned).round(2)).round(0).to_string())
r["nd"] = pd.cut(r.cnq_defect_lines, [-1,1,10,999], labels=["1","2-10",">10"])
print(r.groupby("nd", observed=True).agg(n=("total","size"), planned_median=("total","median"), model_median=("model_work","median"), planned_sum=("total","sum"), model_sum=("model_work","sum")).round(0).to_string())
# 1. work centres in S03: prefix + description
s3["wc_pref"] = s3.work_center.str[:4]
w = s3.groupby("work_center").agg(desc=("work_center_description", lambda x: x.value_counts().index[0]), cat=("work_center_category","first"), ops=("im","size"), h=("im", lambda x: x.sum()/100), orders=("order_number","nunique")).sort_values("h", ascending=False)
print(w.head(45).round(1).to_string())
