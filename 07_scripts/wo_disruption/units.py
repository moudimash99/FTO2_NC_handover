import sys, pandas as pd, numpy as np
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); ds = pd.read_pickle(D+"/ds.pkl")
v = pd.to_numeric(wo.labor_standard_value, errors="coerce")
print("labor std value counts of round values:", {k:int((v==k).sum()) for k in [5,6,10,12,15,20,25,30,40,45,50,60,75,90,100,120,150,180,200,240,300]})
p = pd.to_numeric(wo.processing_time, errors="coerce"); a = pd.to_numeric(wo.total_activity_to_be_confirmed, errors="coerce")
both = v.notna() & p.notna()
print("ops with std & confirmed:", both.sum(), "equal(±1%):", (abs(p[both]-v[both]) <= 0.01*v[both].abs()+1e-6).sum())
d = wo[both & (abs(p-v) > 0.01*v.abs()+1e-6)]
print("differing examples:\n", d[["order_type","operation_short_text","labor_standard_value","processing_time","total_activity_to_be_confirmed","number_of_employees"]].head(15).to_string())
st = pd.to_datetime(wo.actual_start_execution_date); fi = pd.to_datetime(wo.actual_finish_execution_time)
print("start==finish:", (st==fi).sum(), "of", len(wo))
for c in ["actual_start_processing_date","actual_finish_processing_date","actual_finish_setup_date"]:
    print(c, wo[c].notna().sum())
# disruption time units
o = pd.to_datetime(ds.open_date_time); c = pd.to_datetime(ds.closure_date_time); a2 = pd.to_datetime(ds.date_answer_time)
ack = (a2-o).dt.total_seconds()/60; fix = (c-o).dt.total_seconds()/60
t_ack = pd.to_numeric(ds.time_to_get_ack); t_fix = pd.to_numeric(ds.time_to_get_fix); tl = pd.to_numeric(ds.time_lost)
print("ack corr (minutes):", np.corrcoef(ack[ack.notna()], t_ack[ack.notna()])[0,1], (abs(ack - t_ack)<2).mean())
print(pd.DataFrame({"ack_min":ack,"t_ack":t_ack,"fix_min":fix,"t_fix":t_fix,"tl":tl}).head(15).round(1).to_string())
print("time_lost describe:", tl.describe().round(1).to_dict())
