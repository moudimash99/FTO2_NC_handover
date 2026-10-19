import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 160); pd.set_option("display.max_rows", 200)
D, R = sys.argv[1], sys.argv[2]
wo = pd.read_pickle(D+"/wo.pkl"); wo["h"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)/100
ds = pd.read_pickle(D+"/ds2.pkl"); nr = pd.read_pickle(D+"/nc_rw.pkl"); n26 = nr["2026"]
t = (wo.operation_short_text.fillna("")+" "+wo.operation_long_text.fillna("")).str.replace(r"\s+"," ",regex=True)
cut = wo[t.str.contains(r"fagot|débiter du|debiter du|Débiter câbles BF|Débiter câble BF", case=False) & (wo.order_type=="S03")].copy()
cut["txt"] = t[cut.index]
oc = cut.groupby("order_number").agg(h=("h","sum"), prog=("order_program","first"), msn=("order_msn","first"), wc=("work_center", lambda x: ",".join(sorted(set(x)))),
       start=("actual_start_execution_date","min"), sched=("earliest_scheduled_start_wait_date","min"), txt=("txt", " | ".join))
print("cable-cutting S03 orders:", len(oc), "hours", round(oc.h.sum(),1))
print("by programme/MSN:", oc.groupby(["prog","msn"]).h.agg(["size","sum"]).round(1).to_string())
print("work centres:", oc.wc.value_counts().to_dict())
print("planned per order:", oc.h.round(1).value_counts().to_dict())
print("confirmed on:", pd.to_datetime(oc.start).dt.date.value_counts().sort_index().to_dict())
# cable types, quantities, lengths
spec = oc.txt.str.findall(r"(B[FD]\d{2}|AD\d{2}|DR\d{2}|KL\d{2})[^0-9]{0,30}?(\d+) câbles de (\d+) ?cm")
rows = [(o, ty, int(n), int(l)) for o, l_ in spec.items() for ty, n, l in l_]
sp = pd.DataFrame(rows, columns=["order","type","n","cm"])
print("cables requested:", sp.groupby(["type","cm"]).n.sum().to_dict(), "| total cables:", sp.n.sum())
print("sample texts:"); [print("  ", x[:300]) for x in oc.txt.drop_duplicates().head(4)]
# Is cutting BF24 also done in normal production orders (S01)?
s01 = wo[(wo.order_type=="S01") & t.str.contains(r"BF24|BF20|Débiter", case=False)]
print("\nS01 ops mentioning BF24/BF20/Débiter:", len(s01), round(s01.h.sum(),1), s01.operation_short_text.str[:40].value_counts().head(5).to_dict())
# A330 NCs and disruptions about short / missing cables on the same MSNs
msns = set(oc.msn.astype(str).str.lstrip("0"))
nn = n26[n26.msn.astype(str).str.lstrip("0").isin(msns)]
print("\n2026 NCs on those MSNs:", len(nn), "| cable type NCs:", (nn.Type_NC_auto=="CABLES").sum(), "| mentioning BF24/BF20:", nn.description_long_text.fillna("").str.contains("BF2[04]").sum())
dd = ds[ds.msn.fillna("").str.lstrip("0").isin(msns)]
print("disruptions on those MSNs:", len(dd), dd.kind.value_counts().to_dict(), "| mentioning BF:", dd.comment.fillna("").str.contains(r"\bBF ?2[04]", case=False).sum())
print("all 2026 NCs mentioning BF24/BF20:", n26.description_long_text.fillna("").str.contains(r"BF ?2[04]").sum(), "| all disruptions mentioning BF24/20:", ds.comment.fillna("").str.contains(r"BF ?2[04]", case=False).sum())
print(ds[ds.comment.fillna("").str.contains(r"BF ?2[04]", case=False)][["open_date_time","line","kind","comment"]].assign(comment=lambda x: x.comment.str.replace(r"\s+"," ",regex=True).str[:120]).head(8).to_string())
