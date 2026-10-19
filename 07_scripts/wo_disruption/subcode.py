import sys, pandas as pd
d = pd.read_pickle(sys.argv[1]+"/defs_nc25.pkl")
for c in ["sub_code","code","resolved_by","confidence"]:
    v = d[c].astype(str).str.strip()
    print(c, "non-empty:", round((~v.isin(["", "None", "nan", "-"])).mean(), 2), v.value_counts().head(6).to_dict())
print("sous_groupe classes used:", d.sous_groupe.nunique())
