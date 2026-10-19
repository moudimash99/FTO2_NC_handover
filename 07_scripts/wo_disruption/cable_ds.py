import sys, re, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 110)
D = sys.argv[1]
d = pd.read_pickle(D+"/defs_nc26.pkl"); lk = pd.read_pickle(D+"/ds_nc_links.pkl")
cab = d[d.defaut_cable.astype(str).str.lower().isin(["true","1"]) & (d.perimetre=="FTO2")]
print("FTO2 cable defects:", len(cab), "NCs", cab.notification_number.nunique(), cab.provenance.value_counts().to_dict())
lk = lk.groupby("notification_number").agg(comment=("comment", lambda x: " | ".join(x.fillna(""))), solution=("solution", lambda x: " | ".join(x.fillna(""))))
cab = cab.join(lk, on="notification_number")
cab["has_ds"] = cab.comment.notna()
print("cable defects whose NC has a linked disruption:", cab.has_ds.sum())
def prov(t):
    t = t.lower() if isinstance(t, str) else ""
    rec = re.search(r"livr|re[çc]u|arriv|servi|fourni|impression|imprim", t)
    line = re.search(r"trop court|coup[ée]|erreur de cheminement|par erreur|arrach|op[ée]rateur|pinc", t)
    return "line" if line and not rec else "received" if rec and not line else "both" if rec and line else "silent"
cab["ds_prov"] = cab.comment.map(prov)
print(pd.crosstab(cab[cab.has_ds].provenance, cab[cab.has_ds].ds_prov, margins=True))
print(cab[cab.has_ds & (cab.provenance=="NON_PRECISE") & (cab.ds_prov!="silent")][["notification_number","sous_groupe","ds_prov","comment"]].assign(comment=lambda x: x.comment.str.replace(r"\s+"," ",regex=True).str[:100]).head(12).to_string())
