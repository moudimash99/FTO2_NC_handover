import sys, re, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 130)
D = sys.argv[1]
ds = pd.read_pickle(D+"/ds2.pkl"); nr = pd.read_pickle(D+"/nc_rw.pkl"); n26 = nr["2026"]
print("nc26 msn samples:", n26.msn.dropna().astype(str).head(8).tolist(), "| A330 msns:", sorted(n26[n26.programme=="A330"].msn.dropna().astype(str).unique())[-12:])
msns = {"2166","2169","2170","2171","2173"}
norm = lambda s: s.fillna("").astype(str).str.replace(r"\.0$","",regex=True).str.lstrip("0")
nn = n26[norm(n26.msn).isin(msns)]
print("2026 NCs on those MSNs:", len(nn), nn.Type_NC_auto.value_counts().to_dict())
print("  short texts:", nn.description_short.head(15).tolist())
dd = ds[norm(ds.msn).isin(msns)]
print("disruptions on those MSNs:", len(dd), dd.type_desc.value_counts().to_dict())
bf = ds[ds.comment.fillna("").str.contains(r"BF ?2[04]", case=False)]
print("disruptions mentioning BF20/BF24:", len(bf)); print(bf[["open_date_time","line","type_desc","comment"]].assign(comment=lambda x: x.comment.str.replace(r"\s+"," ",regex=True).str[:110]).to_string())
print("2026 NCs mentioning BF20/BF24:", n26.description_long_text.fillna("").str.contains(r"BF ?2[04]").sum())
