import sys, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
ds = pd.read_pickle(sys.argv[1]+"/ds2.pkl"); ds["tl"] = pd.to_numeric(ds.time_lost)
print(ds[ds.physical_station.str.contains("REC|FAL", case=False, na=False)].physical_station.value_counts().head(5).to_dict())
q = ds[ds.type_desc.str.startswith("QLS", na=False) & ~ds.has_nc]
print("quality disruptions without an NC:", len(q), "hours lost", round(q.tl.sum()/60), "| no work order:", q.work_order.isna().sum(), "| solutions:", q.solution.fillna("").str[:40].value_counts().head(6).to_dict())
print(q.comment.fillna("").str.replace(r"\s+"," ",regex=True).str[:110].sample(10, random_state=2).tolist())
