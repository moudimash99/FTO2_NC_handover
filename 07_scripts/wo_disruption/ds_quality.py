import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 130)
D = sys.argv[1]
ds = pd.read_pickle(D+"/ds2.pkl"); ds["tl"] = pd.to_numeric(ds.time_lost)
short = {"LOG - Probleme servitude":"Missing part","SUPTECH - Probleme OF-OT et Definition":"Work order / definition","QLS - Probleme qualite":"Quality problem"}
ds["kind"] = ds.type_desc.map(short).fillna("Line problem")
txt = (ds.comment.fillna("")+" "+ds.solution.fillna("")).str.lower()
qual_words = r"ab[iî]m|endommag|d[ée]t[ée]rior|trop court|coup[ée]|cass[ée]|d[ée]chir|ray[ée]|non.?conform|d[ée]fectu|\bhs\b|\bnc\b|invers|mal (serti|mont|branch|pos)|mauvais(e)? (serti|branch|montage|mise en)|oubli|doublon|erreur de (c[aâ]blage|branchement|montage)"
ds["q_words"] = txt.str.contains(qual_words)
ds["q_group"] = np.select([ds.kind=="Quality problem", ds.has_nc, ds.q_words], ["1. Quality problem (as declared)", "2. Other kind, but an NC follows", "3. Other kind, quality wording, no NC"], "4. Not quality-related")
g = ds.groupby("q_group").agg(n=("tl","size"), hours=("tl", lambda x: x.sum()/60)); g["eur"] = g.hours*50
print(g.round(0).to_string())
print(pd.crosstab(ds.q_group, ds.kind).to_string())
for grp in ["2. Other kind, but an NC follows", "3. Other kind, quality wording, no NC"]:
    print(f"\n{grp} samples:")
    for _, r in ds[ds.q_group==grp].sample(8, random_state=3).iterrows():
        print(f"   [{r.kind}] {r.tl} min | {' '.join(str(r.comment).split())[:120]}")
q = ds[ds.q_group!="4. Not quality-related"]
print("\nquality-related total:", len(q), "disruptions,", round(q.tl.sum()/60), "h,", round(q.tl.sum()/60*50), "EUR | per month:", (q.groupby(q.ot.dt.strftime('%m')).tl.sum()/60).round(0).to_dict())
print("lines:", q.line.value_counts().head(6).to_dict())
