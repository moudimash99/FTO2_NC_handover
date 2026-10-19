import sys, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 45)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl")
v = pd.to_numeric(wo.labor_standard_value, errors="coerce"); p = pd.to_numeric(wo.processing_time, errors="coerce")
a = pd.to_numeric(wo.total_activity_to_be_confirmed, errors="coerce")
st = pd.to_datetime(wo.actual_start_execution_date); fi = pd.to_datetime(wo.actual_finish_execution_time)
el_min = (fi - st).dt.total_seconds()/60
both = v.notna() & p.notna() & (v > 0)
diff = both & (abs(p - v) > 0.01*v + 1e-6)
print("ops with planned & confirmed:", both.sum(), "| differ:", diff.sum())
print("by order type:", pd.crosstab(wo.order_type[both], diff[both]).to_dict("index"))
d = wo[diff].assign(v=v, p=p, a=a, el=el_min, ratio=p/v)
print("ratio confirmed/planned:", d.ratio.describe(percentiles=[.1,.25,.5,.75,.9]).round(2).to_dict())
print("planned h on differing ops:", round(d.v.sum()/100), " confirmed:", round(d.p.sum()/100))
# is confirmed = elapsed calendar time?
for unit, f in [("IM (x100/60)", 100/60), ("minutes", 1)]:
    e = d.el * f
    print(f"confirmed within 5% of elapsed time in {unit}:", (abs(d.p - e) <= 0.05*d.p + 1).sum(), "of", len(d))
print("start==finish among differing:", (d.el == 0).sum())
print(d.groupby("order_type").agg(n=("v","size"), planned_h=("v", lambda x: round(x.sum()/100)), confirmed_h=("p", lambda x: round(x.sum()/100))).to_string())
s3 = d[d.order_type=="S03"]
print("\nS03 differing ops:\n", s3[["order_number","operation_short_text","work_center_description","v","p","a","el"]].round(1).to_string())
# S03 planned vs confirmed at order level
s3all = wo[wo.order_type=="S03"].assign(v=v.fillna(0), p=p.fillna(0))
print("\nS03 total planned h:", round(s3all.v.sum()/100), "confirmed h:", round(s3all.p.sum()/100))
# S01 big differing: show
print(d[d.order_type=="S01"].sort_values("p", ascending=False)[["operation_short_text","v","p","a","el","number_of_employees"]].head(8).round(1).to_string())
