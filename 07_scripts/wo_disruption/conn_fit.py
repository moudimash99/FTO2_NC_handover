import sys, pandas as pd, numpy as np
pd.set_option("display.width", 250)
D = sys.argv[1]
m = pd.read_pickle(D+"/calib.pkl"); d26 = pd.read_pickle(D+"/defs_nc26.pkl")
conn = {"Inversion", "Erreur de branchement", "Non connecté"}
comp = d26.groupby("notification_number").agg(n=("sous_groupe","size"), n_conn=("sous_groupe", lambda x: x.isin(conn).sum()))
x = m[(m.cnq_rule=="RWK") & m.complete].join(comp, how="left")
x[["n","n_conn"]] = x[["n","n_conn"]].fillna(0)
print("complete reworked NCs:", len(x), "| with >=1 connection error:", (x.n_conn>0).sum(), "| only connection errors:", ((x.n_conn==x.n)&(x.n>0)).sum())
c = x[x.n_conn > 0].copy(); c["share_conn"] = c.n_conn/c.n
print(c[["Type_NC_auto","n","n_conn","share_conn","total","work","test","cnq_min_hands_on"]].sort_values("n_conn").round(2).to_string())
mostly = c[c.share_conn >= 0.6]
if len(mostly) >= 3:
    b, a = np.polyfit(mostly.n_conn, mostly.total, 1)
    print(f"\nNCs where >=60% of defects are connection errors: {len(mostly)} | fit planned = {a:.0f} + {b:.1f} x connection errors")
    print(f"total planned / total connection errors: {mostly.total.sum()/mostly.n_conn.sum():.1f} min | model hands-on for same: {mostly.cnq_min_hands_on.sum()/mostly.n_conn.sum():.1f} min per error")
