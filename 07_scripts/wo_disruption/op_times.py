import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 300)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); wo["min"] = pd.to_numeric(wo.labor_standard_value, errors="coerce")*0.6
t = wo.operation_short_text.fillna("").str.lower()
wcd = wo.work_center_description.fillna("").str.lower()
wo["kind"] = np.select([
    wcd.str.contains("test|essai") | t.str.contains(r"\btest|essai|continuit|isolement|sonn"),
    t.str.contains(r"branch|enfich|connect"),
    t.str.contains(r"sertir|sertissage|d[ée]nuder"),
    t.str.contains(r"chemin|fretter|gainer|cabler|câbler"),
    t.str.contains(r"contr[ôo]l|inspect|attestation"),
], ["Test", "Connection (branchement)", "Crimping (sertissage)", "Routing / wiring", "Inspection / control"], "Other")
s1 = wo[(wo.order_type=="S01")]
print("S01 ops:", len(s1), "| with a planned time:", s1["min"].gt(0).sum())
g = s1[s1["min"]>0].groupby("kind")["min"].agg(ops="size", total_h=lambda x: x.sum()/60, median="median", p25=lambda x: x.quantile(.25), p75=lambda x: x.quantile(.75))
print(g.round(1).to_string())
print("ops with no planned time by kind:", s1[~(s1["min"]>0)].kind.value_counts().to_dict())
# test ops: what are they and per product
te = s1[(s1.kind=="Test") & (s1["min"]>0)].copy()
print("\nTest ops texts:", te.operation_short_text.str[:40].value_counts().head(15).to_dict())
print("Test work centres:", te.work_center_description.value_counts().head(6).to_dict())
te["product"] = te.material_header_description.fillna("(no header)").str.strip()
pt = te.groupby("product")["min"].agg(ops="size", median="median", min="min", max="max").sort_values("ops", ascending=False)
print("\nTest time per product (planned minutes per test operation):"); print(pt.head(30).round(0).to_string())
