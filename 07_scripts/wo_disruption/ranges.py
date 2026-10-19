import sys, pandas as pd
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); nc = pd.read_pickle(D+"/nc.pkl"); ds = pd.read_pickle(D+"/ds.pkl")
def rng(s): s = pd.to_datetime(s, errors="coerce"); return f"{s.min()} -> {s.max()} (n={s.notna().sum()})"
print("NC2025 creation", rng(nc.creation_time))
print(pd.to_datetime(nc.creation_time).dt.to_period("M").value_counts().sort_index().to_string())
print("DS open", rng(ds.open_date_time))
print(pd.to_datetime(ds.open_date_time).dt.to_period("M").value_counts().sort_index().to_string())
print("WO actual start", rng(wo.actual_start_execution_date))
print(pd.to_datetime(wo.actual_start_execution_date).dt.to_period("M").value_counts().sort_index().to_string())
print("WO earliest sched", rng(wo.earliest_scheduled_start_wait_date))
print("ds empty cols:", [c for c in ds.columns if ds[c].isna().all()])
print("wo empty cols:", len([c for c in wo.columns if wo[c].isna().all()]), "of", wo.shape[1])
