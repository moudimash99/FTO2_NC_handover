import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120); pd.set_option("display.max_rows", 200)
D = sys.argv[1]
wo = pd.read_pickle(D+"/wo.pkl"); wo["h"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)/100
q = wo[wo.work_center_category=="QUAL"]
print("Quality work-centre operations:", len(q), "| planned h:", round(q.h.sum()), "| by order type:", q.groupby("order_type").h.agg(["size","sum"]).round(0).to_dict("index"))
print(q.groupby(["work_center","work_center_description"]).h.agg(["size","sum"]).sort_values("sum", ascending=False).head(15).round(1).to_string())
print("\nQuality ops by text (top planned h):")
print(q.groupby(q.operation_short_text.str[:45]).h.agg(["size","sum"]).sort_values("sum", ascending=False).head(15).round(1).to_string())
# the two quality-admin orders in full
for o in ["1031243823", "1031225552"]:
    g = wo[wo.order_number==o]
    print(f"\n=== order {o} ({g.order_type.iloc[0]}, {g.order_program.iloc[0]} MSN {g.order_msn.iloc[0]}), planned {g.h.sum():.1f} h, sched {g.earliest_scheduled_start_wait_date.min()}")
    for _, r in g.sort_values("operation_number").iterrows():
        lt = (r.operation_long_text or "").replace("\r\n"," ").strip() if isinstance(r.operation_long_text, str) else ""
        print(f"   {r.operation_number:>5} {r.h:5.1f}h {r.work_center} | {r.operation_short_text} | {lt[:150]}")
# similar wording anywhere in the file
t = (wo.operation_short_text.fillna("")+" "+wo.operation_long_text.fillna("")).str.lower()
hit = wo[t.str.contains(r"retours? client|alerte qualit|gestion nc|revue qa|\bnoe\b|ad-hoc|accompagnement prod|analyse qualit")]
print("\nops anywhere mentioning customer returns / quality alerts / NC management:", len(hit), "orders", hit.order_number.nunique(), "hours", round(hit.h.sum(),1))
print(hit.groupby(["order_number","order_type","order_program","order_msn"]).h.sum().round(1).to_string())
# S99 and S02 content
for ty in ["S99","S02"]:
    g = wo[wo.order_type==ty]
    print(f"\n{ty}: {g.order_number.nunique()} orders, {g.h.sum():.0f} h | top texts:", g.groupby(g.operation_short_text.str[:40]).h.sum().sort_values(ascending=False).head(8).round(0).to_dict())
