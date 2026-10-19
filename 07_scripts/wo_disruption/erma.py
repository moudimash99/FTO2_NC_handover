import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120); pd.set_option("display.max_rows", 100)
D = sys.argv[1]
nr = pd.read_pickle(D+"/nc_rw.pkl"); n25 = nr["2025"]; o = pd.read_pickle(D+"/s03_status.pkl"); wo = pd.read_pickle(D+"/wo.pkl")
c25 = pd.read_pickle(D+"/cnq_nc25.pkl").set_index("notification_number")
e = n25[n25.user_department.str.contains("ERMA", na=False)]
print("ERMA 2025 NCs:", len(e))
for c in ["Type_NC_auto","workflow_list","station","trigger","cnq_rule","programme","constituent_assembly"]:
    print(c, e[c].value_counts().head(8).to_dict())
print("ERMA with rework order:", e.has_rw.mean().round(2))
print("ERMA short texts:", e.description_short.value_counts().head(12).to_dict())
print(e.description_long_text.dropna().str.replace(r"\s+"," ",regex=True).str[:220].head(5).to_string())
ce = c25.loc[e.notification_number.astype(str)]
ce = ce[ce.cnq_on_aec==1]; ce = ce[pd.to_datetime(ce.date_creation, utc=True).dt.year==2025]
print("ERMA FTO2-liable 2025: n", len(ce), "L3 EUR", round(ce.cnq_cost_total.sum()), "per NC", round(ce.cnq_cost_total.mean()), "defects", int(ce.cnq_defect_lines.sum()))
# no-trace S03 test/cable orders: what are they?
for k in ["test rework", "cable remake", "free-text request (FAL/customer?)"]:
    g = o[(o.content==k) & o.status.str[0].isin(list("GH"))]
    print(f"\n== {k}, no NC trace: {len(g)} orders, {g.h.sum():.0f} h | wc:", pd.Series([w for x in g.wc for w in x.split(",")]).value_counts().head(6).to_dict())
    print("   sched month:", pd.to_datetime(g.sched).dt.strftime("%Y-%m").value_counts().sort_index().to_dict(), "| prog", g.prog.value_counts().to_dict())
    for i, r in g.sort_values("h", ascending=False).head(6).iterrows(): print(f"   {i} {r.h:5.1f}h msn {r.msn} | {r.wcd[:70]} | {r.t[:200]!r}")
# what does the NC word in the catch-up orders say
g = o[(o.content=="catch-up (rattrapage 929/925)") & (o.status.str[0]=="G")]
m = g.t.str.extract(r"(.{80}\bNC\b.{80})", flags=re.S)[0].str.replace(r"\s+"," ",regex=True)
print("\ncatch-up 'NC' context:", m.value_counts().head(3).to_dict())
print("catch-up wc:", pd.Series([w for x in g.wc for w in x.split(",")]).value_counts().head(8).to_dict())
