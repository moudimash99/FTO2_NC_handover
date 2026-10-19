import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 50); pd.set_option("display.max_rows", 300)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); wo["min"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)*0.6
t = wo.operation_short_text.fillna("").str.lower()
is_test = t.str.contains(r"\btest|tester|essai|continuit|isolement|atténuation|attenuation|quadrax|sonnage|banc") & ~t.str.contains(r"finition|conditionn|administrativ|après test|apres test")
is_conn = t.str.contains(r"branch|enfich|connect") & ~is_test
is_crimp = t.str.contains(r"sertir|sertissage|d[ée]nuder") & ~is_conn & ~is_test
wo["kind"] = np.select([is_test, is_conn, is_crimp], ["test", "connection", "crimping"], "other")
s1 = wo[wo.order_type=="S01"].copy()
hdr = s1.material_header_description.fillna("").str.upper()
def fam(h):
    if re.search(r"\bMIP\b|1101VB|SOUS-ENSEMBLES ROUTE", h): return "MIP A350 (1101VB…)"
    if re.search(r"740VU|743VU", h): return "740VU / 743VU doors"
    if re.search(r"ERUDDER|4714VB|4715VB|4716VB|4717VB|E-RUDDER", h): return "eRudder harness (A320)"
    if re.search(r"045[12]VB|451VB|452VB|MFRL", h): return "MFRL harness 451/452VB"
    if re.search(r"ELEC ASSY|\d+VU", h): return "VU electrical assembly"
    if re.search(r"HARNESS|WIRE BUNDLE|\d+VB", h): return "Other harness"
    return "Other / no header"
s1["family"] = hdr.map(fam)
po = s1.pivot_table(index="order_number", columns="kind", values="min", aggfunc="sum", fill_value=0)
po["total"] = po.sum(axis=1); po["family"] = s1.groupby("order_number").family.first(); po["hdr"] = s1.groupby("order_number").material_header_description.first()
po["n_test_ops"] = s1[s1.kind=="test"].groupby("order_number").size(); po["n_test_ops"] = po.n_test_ops.fillna(0)
po["test_ops_no_time"] = s1[(s1.kind=="test") & (s1["min"]==0)].groupby("order_number").size(); po["test_ops_no_time"] = po.test_ops_no_time.fillna(0)
print("S01 test ops:", (s1.kind=="test").sum(), "| with no planned time:", ((s1.kind=="test") & (s1["min"]==0)).sum())
print("  texts of test ops with no time:", s1[(s1.kind=="test") & (s1["min"]==0)].operation_short_text.str[:35].value_counts().head(8).to_dict())
withtest = po[po.test > 0]
print("\nOrders with planned test time, by product family (minutes per order = per product unit):")
print(withtest.groupby("family").agg(orders=("test","size"), test_median=("test","median"), test_min=("test","min"), test_max=("test","max"),
      connection_median=("connection","median"), total_median=("total","median")).round(0).to_string())
print("\nExamples (one order each):")
ex = withtest.sort_values("test").groupby("hdr").head(1).groupby("family").head(3)
print(ex[["family","hdr","test","connection","crimping","total"]].round(0).to_string())
# connection time per product
conn = po[po.connection > 0]
print("\nOrders with planned connection (branchement) time, by family:")
print(conn.groupby("family").agg(orders=("connection","size"), connection_median=("connection","median"), connection_max=("connection","max"), share_of_order=("connection", lambda x: (x/po.loc[x.index,"total"]).median())).round(2).to_string())
print("connection op texts:", s1[s1.kind=="connection"].operation_short_text.str[:45].value_counts().head(10).to_dict())
po.to_pickle(D+"/s01_orders.pkl")
