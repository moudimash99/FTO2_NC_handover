import sys, pandas as pd
n26 = pd.read_pickle(sys.argv[1]+"/nc_rw.pkl")["2026"].reset_index(drop=True)
n26["m"] = pd.to_datetime(n26.creation_time, utc=True).dt.strftime("%m")
cr = n26[n26.Type_NC_auto=="NC Retour client"]
print("customer-return NCs per month (2026):", cr.groupby("m").size().to_dict())
s = cr[cr.m=="09"]
print("Sept by programme:", s.programme.value_counts().to_dict(), "| plants:", s.plant.value_counts().to_dict())
