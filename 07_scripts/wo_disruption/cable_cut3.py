import sys, pandas as pd
D = sys.argv[1]
ds = pd.read_pickle(D+"/ds2.pkl"); n26 = pd.read_pickle(D+"/nc_rw.pkl")["2026"]
bf = ds[ds.comment.fillna("").str.contains(r"BF ?2[04]", case=False)]
for _, r in bf.iterrows():
    print(f"--- {r.disruption_id} {r.open_date_time} {r.line} {r.type_desc} lost {r.time_lost} min\n  comment: {' '.join(str(r.comment).split())[:600]}\n  solution: {' '.join(str(r.solution).split())[:300]}")
x = n26[n26.description_long_text.fillna("").str.contains(r"BF ?2[04]")]
for _, r in x.iterrows():
    t = ' '.join(str(r.description_long_text).split())
    i = max(0, t.find("BF") - 150)
    print(f"=== NC {r.notification_number} {str(r.creation_time)[:10]} {r.programme} {r.Type_NC_auto} | {r.description_short} | ...{t[i:i+260]}")
