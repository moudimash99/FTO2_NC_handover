import sys, glob, pandas as pd
D = sys.argv[1]
def load(pattern):
    fs = sorted(glob.glob(D + "/" + pattern))
    return pd.concat([pd.read_csv(f, dtype=str, encoding="utf-8-sig", keep_default_na=False, na_values=[""]) for f in fs], ignore_index=True)
wo = load("split_part_[0-9].csv")
nc = load("split_part_nc_*.csv")
ds = load("disrup.csv")
for n, df in [("wo", wo), ("nc", nc), ("ds", ds)]:
    df.to_pickle(f"{D}/../{n}.pkl")
    print(n, df.shape)
