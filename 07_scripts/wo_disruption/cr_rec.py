import sys, pandas as pd
D = sys.argv[1]
x = pd.read_pickle(D+"/sheet_data.pkl"); cr = x["R"]["cr"]; fam = pd.read_pickle(D+"/s03_family.pkl")
n26 = pd.read_pickle(D+"/nc_rw.pkl")["2026"].set_index("notification_number")
for n, r in cr[cr.fam.str.contains("REC|shop", na=False)].iterrows():
    for o in r.in_file:
        f = fam.loc[o]
        print(f"NC {n} {str(n26.loc[n,'creation_time'])[:10]} plant {n26.loc[n,'plant']} | {n26.loc[n,'description_short']} | order {o} {f.family} {f.h:.1f} h | {' '.join(f.t.split())[:150]}")
