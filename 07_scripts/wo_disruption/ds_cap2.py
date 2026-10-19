import sys, pandas as pd, numpy as np
D = sys.argv[1]
raw = pd.read_csv(sys.argv[2], dtype=str, encoding="utf-8-sig", keep_default_na=False, na_values=[""])
nc = pd.read_pickle(D+"/nc.pkl")
ct = pd.to_datetime(nc.creation_time)
print("FTO2 NCs created 29 Dec 2025 - 9 Jan 2026 by day:", ct[(ct>="2025-12-29")&(ct<"2026-01-10")].dt.date.value_counts().sort_index().astype(int).to_dict())
o = pd.to_datetime(raw.open_date_time)
first = o.groupby(o.dt.date).min()
mins = first.dt.hour*60 + first.dt.minute
print("time of first disruption of the day: median", f"{int(mins.median())//60:02d}:{int(mins.median())%60:02d}", "| 25%", f"{int(mins.quantile(.25))//60:02d}:{int(mins.quantile(.25))%60:02d}", "| days starting after 08:57:", (mins > 8*60+57).mean().round(2))
mon = first[[pd.Timestamp(d).dayofweek==0 for d in first.index]]
mm = mon.dt.hour*60+mon.dt.minute
print("Mondays: median first time", f"{int(mm.median())//60:02d}:{int(mm.median())%60:02d}", "| Mondays starting after 08:57:", (mm > 8*60+57).sum(), "of", len(mm))
# timezone check for answer time
a = pd.to_datetime(raw.date_answer_time); ack = pd.to_numeric(raw.time_to_get_ack)
diff = (a - pd.to_timedelta(ack, unit="m") - o).dt.total_seconds()/60
day = o.dt.hour.between(7, 15) & a.notna() & (ack > 0)
print("daytime: (answer - ack) - open, minutes:", diff[day].round(0).value_counts().head(6).to_dict())
