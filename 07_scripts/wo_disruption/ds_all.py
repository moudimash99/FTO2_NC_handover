import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 150); pd.set_option("display.max_rows", 200)
D, R = sys.argv[1], sys.argv[2]
ds = pd.read_pickle(D+"/ds2.pkl"); wo = pd.read_pickle(D+"/wo.pkl"); lk = pd.read_pickle(D+"/ds_nc_links.pkl")
nr = pd.read_pickle(D+"/nc_rw.pkl"); n26 = nr["2026"]; fam = pd.read_pickle(D+"/s03_family.pkl"); c26 = pd.read_pickle(D+"/cnq_nc26.pkl").set_index("notification_number")
ot = wo.drop_duplicates("order_number").set_index("order_number").order_type
ds["tl"] = pd.to_numeric(ds.time_lost); ds["m"] = ds.ot.dt.strftime("%m")
short = {"LOG - Probleme servitude":"Missing part (logistics)","SUPTECH - Probleme OF-OT et Definition":"Work order / definition problem","QLS - Probleme qualite":"Quality problem"}
ds["kind"] = ds.type_desc.map(short).fillna("Line problem (TL/PPE)")
print("where:", ds.line.value_counts().to_dict())
print("stations with REC/FAL in name:", ds.physical_station.str.contains("REC|FAL", case=False, na=False).sum())
g = ds.groupby("kind").agg(n=("tl","size"), hours_lost=("tl", lambda x: x.sum()/60), median_min=("tl","median"), followed_by_nc=("has_nc","sum"))
g["eur_at_50"] = g.hours_lost*50; g["pct_nc"] = (100*g.followed_by_nc/g.n).round(0)
print(g.round(0).to_string()); print("total hours", round(ds.tl.sum()/60), "EUR", round(ds.tl.sum()/60*50), "per month EUR", round(ds.tl.sum()/60*50/9))
print("per month hours:", (ds.groupby("m").tl.sum()/60).round(0).to_dict())
# disruption on which order type (Sept only, where the WO file applies)
sep = ds[ds.m=="09"].copy(); sep["wo_type"] = sep.work_order.fillna("").str.lstrip("0").map(ot)
print("\nSept disruptions:", len(sep), "| work order found in WO file:", sep.wo_type.notna().sum(), sep.wo_type.value_counts().to_dict())
print(sep[sep.wo_type=="S03"][["kind","comment","tl"]].assign(comment=lambda x: x.comment.str.replace(r"\s+"," ",regex=True).str[:110]).to_string())
# solution/comment naming an order: which families
txt = ds.comment.fillna("")+" "+ds.solution.fillna("")
named = [(i, x) for i, t in zip(ds.disruption_id, txt) for x in re.findall(r"(?<!\d)(10\d{8})(?!\d)", t)]
nd = pd.DataFrame(named, columns=["d","o"]); nd["type"] = nd.o.map(ot); nd["family"] = nd.o.map(fam.family)
print("\norder numbers named in disruptions found in WO file:", nd.type.notna().sum(), nd.type.value_counts().to_dict(), "| S03 family:", nd.family.value_counts().to_dict())
# full chain: disruption -> NC -> rework order (Sept file), with times
rw = n26.set_index("notification_number").rw
chain = lk.copy(); chain["rw"] = chain.notification_number.map(rw)
chain["in_file"] = chain.rw.apply(lambda l: [o for o in (l if isinstance(l, list) else []) if o in fam.index])
chain["planned_h"] = chain.in_file.apply(lambda l: fam.loc[l].h.sum() if l else np.nan)
full = chain[chain.in_file.str.len() > 0]
print("\nfull chains disruption -> NC -> rework order in Sept file:", len(full))
print(full[["disruption_id","notification_number","dh","tl","planned_h","comment"]].assign(comment=lambda x: x.comment.str.replace(r"\s+"," ",regex=True).str[:70]).head(8).round(1).to_string())
# example chain with model cost
ex = full.sort_values("dh").iloc[0]
print("\nexample NC model steps:", c26.loc[ex.notification_number, ["cnq_rule","cnq_min_alert","cnq_min_writing","cnq_min_support","cnq_min_setup","cnq_min_hands_on","cnq_min_recheck","cnq_cost_total"]].to_dict())
# samples of the non-NC disruption kinds
for k in ["Work order / definition problem", "Missing part (logistics)", "Line problem (TL/PPE)"]:
    x = ds[(ds.kind==k)].comment.fillna("").str.replace(r"\s+"," ",regex=True).str[:110]
    print(f"\n{k} top comments:", x.value_counts().head(5).to_dict())
    print("  samples:", x.sample(6, random_state=1).tolist())
