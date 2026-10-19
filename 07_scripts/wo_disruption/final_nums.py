import sys, pandas as pd, numpy as np
pd.set_option("display.width", 250)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); pn = pd.read_pickle(D+"/s03_vs_model.pkl"); o26 = pd.read_pickle(D+"/cnq_nc26.pkl")
v = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)
print("Sept 2026 planned hours by order type (IM/100):", (v.groupby(wo.order_type).sum()/100).round(0).to_dict(), "| orders:", wo.groupby("order_type").order_number.nunique().to_dict())
print("ops with no standard value by type:", (v==0).groupby(wo.order_type).mean().round(2).to_dict())
nc26 = pd.concat([pd.read_csv(sys.argv[2]+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number").set_index("notification_number")
r = pn[pn.cnq_rule=="RWK"].join(nc26.Type_NC_auto)
g = r.groupby("Type_NC_auto").agg(n=("s03_min","size"), s03_median=("s03_min","median"), s03_sum=("s03_min","sum"), model_work_median=("model_work_min","median"), model_work_sum=("model_work_min","sum"), model_hands_sum=("cnq_min_hands_on","sum"))
print(g.round(0).to_string())
# within 2x agreement
ratio = r.s03_min.replace(0,np.nan)/r.model_work_min
print("NCs with S03 within 0.5x-2x of model work:", ((ratio>=0.5)&(ratio<=2)).sum(), "of", len(r), "| S03 = 0:", (r.s03_min==0).sum())
print("if IM were minutes: S03 sum", round(r.s03_min.sum()/0.6), "vs model", round(r.model_work_min.sum()))
