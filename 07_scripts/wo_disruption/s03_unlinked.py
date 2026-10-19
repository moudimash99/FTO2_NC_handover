import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90); pd.set_option("display.max_rows", 200)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); L = pd.read_pickle(D+"/nc_s03_links.pkl"); po = pd.read_pickle(D+"/s03_orders.pkl")
s3 = wo[wo.order_type=="S03"].copy(); s3["im"] = pd.to_numeric(s3.labor_standard_value, errors="coerce").fillna(0)
s3["linked"] = s3.order_number.isin(L.order)
txt = (s3.operation_short_text.fillna("")+" "+s3.operation_long_text.fillna("")).str.lower()
s3["t"] = txt
o = s3.groupby("order_number").agg(linked=("linked","first"), im=("im","sum"), ops=("im","size"), t=("t"," || ".join),
     hdr=("material_header_description","first"), prog=("order_program","first"), wcd=("work_center_description", lambda x: " / ".join(sorted(set(x.dropna()))[:4])),
     wcc=("work_center_category", lambda x: ",".join(sorted(set(x)))))
def why(r):
    t = r.t
    if re.search(r"\bnc\b|non.?conform|suite [àa] (la )?nc", t): return "mentions NC"
    if "rec-s/t" in r.wcd.lower() or "rec" in r.wcd.lower(): return "REC S/T work centre"
    if re.search(r"rattrapage", t): return "rattrapage (catch-up)"
    if re.search(r"retrofit|modif|evolution|mod\b", t): return "retrofit/modif"
    return "other"
o["why"] = o.apply(why, axis=1)
print(pd.crosstab(o.why, o.linked, values=o.im, aggfunc="sum").fillna(0).div(100).round(0))
print(pd.crosstab(o.why, o.linked))
print("total S03 planned hours Sept:", round(o.im.sum()/100), "| linked:", round(o[o.linked].im.sum()/100))
for w in ["rattrapage (catch-up)","other","REC S/T work centre"]:
    print("\n==", w)
    print(o[(o.why==w)&(~o.linked)].sort_values("im", ascending=False)[["im","ops","prog","hdr","wcd"]].head(8).to_string())
    for t in o[(o.why==w)&(~o.linked)].sort_values("im", ascending=False).t.head(3): print("   >", t[:400].replace("\r\n"," "))
o.to_pickle(D+"/s03_orders_why.pkl")
