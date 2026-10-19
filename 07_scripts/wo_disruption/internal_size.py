import sys, pandas as pd, numpy as np
pd.set_option("display.width", 250)
D = sys.argv[1]
m = pd.read_pickle(D+"/calib.pkl"); m["model"] = m.cnq_min_setup + m.cnq_min_hands_on
for label, sel in [("complete orders", m.complete), ("all orders in file", m.complete | ~m.complete)]:
    r = m[(m.cnq_rule=="RWK") & sel & (m.Type_NC_auto=="NC Interne")]
    ratio = r.total / r.model
    print(f"{label}: n={len(r)} | planned {r.total.sum():.0f} vs model {r.model.sum():.0f} -> ratio of totals {r.total.sum()/r.model.sum():.2f} | median per-NC ratio {ratio.median():.2f} | planned median {r.total.median():.0f} model median {r.model.median():.0f}")
    print("   per NC (planned, model, defects):", sorted(zip(r.total.round(0), r.model.round(0), r.cnq_defect_lines), reverse=True))
