import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); wo["min"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)*0.6
fam = pd.read_pickle(D+"/s03_family.pkl"); n26 = pd.read_pickle(D+"/nc_rw.pkl")["2026"]
s3 = wo[wo.order_type=="S03"].copy(); s3["family"] = s3.order_number.map(fam.family)
t = s3.operation_short_text.fillna("").str.lower()
s3["retest"] = np.select([t.str.contains(r"par (le|la) test"), t.str.contains(r"\btest|tester|continuit|\bemi\b|sonn")], ["fixed by the test team", "re-test"], "")
# NC type of each order
rows = [(o, ty) for l, ty in zip(n26.rw, n26.Type_NC_auto) for o in l]
otype = pd.DataFrame(rows, columns=["order","nc_type"]).drop_duplicates("order").set_index("order").nc_type
for f in ["FTO2 shop floor", "REC (FAL)", "IEVB (MSN 700/701)"]:
    g = s3[s3.family==f]; o = g.groupby("order_number")
    has = o.retest.apply(lambda x: (x!="").any())
    print(f"\n== {f}: {g.order_number.nunique()} rework orders | with a re-test operation: {has.sum()}")
    r = g[g.retest!=""]
    print(r.groupby(["retest", r.operation_short_text.str[:42]])["min"].agg(ops="size", with_time=lambda x: (x>0).sum(), median="median", max="max").round(0).to_string())
sf = s3[s3.family=="FTO2 shop floor"].copy(); sf["nc_type"] = sf.order_number.map(otype).fillna("(no NC linked)")
by = sf.groupby("order_number").agg(nc_type=("nc_type","first"), retest=("retest", lambda x: "fixed by the test team" if (x=="fixed by the test team").any() else ("re-test" if (x=="re-test").any() else "none")),
                                   retest_min=("min", lambda x: x[sf.loc[x.index,"retest"]!=""].sum()))
print("\nShop-floor rework orders by NC type and re-test:")
print(pd.crosstab(by.nc_type, by.retest).to_string())
print("\nplanned re-test minutes per order (when present), by NC type:")
print(by[by.retest!="none"].groupby(["nc_type","retest"]).retest_min.agg(["size","median","min","max"]).round(0).to_string())
