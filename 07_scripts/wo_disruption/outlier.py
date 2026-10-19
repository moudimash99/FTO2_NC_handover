import sys, pandas as pd
D = sys.argv[1]
n26 = pd.read_pickle(D+"/nc_rw.pkl")["2026"].set_index("notification_number"); wo = pd.read_pickle(D+"/wo.pkl")
for nc in ["218233692", "218248460"]:
    r = n26.loc[nc]
    print(f"=== NC {nc} {str(r.creation_time)[:10]} {r.programme} {r.Type_NC_auto} {r.workflow_list} | {r.description_short}")
    print("   text:", " ".join(str(r.description_long_text).split())[150:600])
    for o in r.rw:
        g = wo[wo.order_number==o]
        for _, x in g.iterrows():
            print(f"   order {o} op {x.operation_number} {float(x.labor_standard_value or 0)*0.6:6.0f} min | {x.work_center_description} | {x.operation_short_text} | {' '.join(str(x.operation_long_text).split())[:160]}")
