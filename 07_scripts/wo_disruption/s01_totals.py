import sys, re, pandas as pd, numpy as np
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); wo["min"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)*0.6
s1 = wo[wo.order_type=="S01"]; t = s1.operation_short_text.fillna("").str.lower()
is_test = t.str.contains(r"\btest|tester|essai|continuit|isolement|atténuation|attenuation|quadrax|sonnage|banc") & ~t.str.contains(r"finition|conditionn|administrativ|après test|apres test")
is_conn = t.str.contains(r"branch|enfich|connect") & ~is_test
is_crimp = t.str.contains(r"sertir|sertissage|d[ée]nuder") & ~is_conn & ~is_test
is_route = t.str.contains(r"chemin|fretter|gainer|cabler|câbler") & ~is_conn & ~is_test & ~is_crimp
is_insp = (s1.work_center_category=="QUAL") & ~is_test
k = pd.Series(np.select([is_test, is_conn, is_crimp, is_route, is_insp], ["Test","Connection","Crimping","Routing / sleeving","Inspection"], "Other"), index=s1.index)
g = s1.groupby(k)["min"].agg(ops="size", hours=lambda x: x.sum()/60, median_min="median")
g["share"] = (100*g.hours/g.hours.sum()).round(0)
print(g.round(0).sort_values("hours", ascending=False).to_string()); print("total S01 planned h:", round(s1["min"].sum()/60))
