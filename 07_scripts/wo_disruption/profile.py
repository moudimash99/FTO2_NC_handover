import sys, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
df = pd.read_pickle(sys.argv[1])
print(df.shape)
for c in df.columns:
    s = df[c]
    nn = s.notna().sum()
    if nn == 0: continue
    vc = s.value_counts()
    top = "; ".join(f"{k[:40]!s}={v}" for k, v in vc.head(6).items())
    print(f"{c[:45]:45s} nn={nn:5d} uniq={s.nunique():5d} | {top}")
