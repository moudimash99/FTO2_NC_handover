import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 110); pd.set_option("display.max_rows", 100)
D, R = sys.argv[1], sys.argv[2]
wo = pd.read_pickle(D+"/wo.pkl"); ds = pd.read_pickle(D+"/ds.pkl"); nr = pd.read_pickle(D+"/nc_rw.pkl")
n25, n26 = nr["2025"], nr["2026"]
s3 = wo[wo.order_type=="S03"].copy(); s3["im"] = pd.to_numeric(s3.labor_standard_value, errors="coerce").fillna(0)
txt = (s3.operation_short_text.fillna("")+" "+s3.operation_long_text.fillna(""))
s3["t"] = txt
o = s3.groupby("order_number").agg(h=("im", lambda x: x.sum()/100), ops=("im","size"), t=("t"," || ".join), prog=("order_program","first"), msn=("order_msn","first"),
      wcd=("work_center_description", lambda x: " / ".join(sorted(set(x.dropna())))), wc=("work_center", lambda x: ",".join(sorted(set(x.dropna())))),
      sched=("earliest_scheduled_start_wait_date","min"))
# 1. linked from an NC we have
link26 = {ord_: n for n, l in zip(n26.notification_number, n26.rw) for ord_ in l}
link25 = {ord_: n for n, l in zip(n25.notification_number, n25.rw) for ord_ in l}
o["nc_link_2026"] = o.index.map(link26); o["nc_link_2025"] = o.index.map(link25)
# 2. NC number written in the order text
o["nc_in_text"] = o.t.str.findall(r"(?<!\d)(2\d{8})(?!\d)").apply(lambda l: sorted(set(l)))
all26 = set(n26.notification_number.str.lstrip("0")); all25 = set(n25.notification_number.astype(str))
o["text_nc_known"] = o.nc_in_text.apply(lambda l: [x for x in l if x in all26 or x in all25])
# 3. order number written in an NC long text or a disruption
nctext = pd.concat([n26[["notification_number","description_long_text"]], n25[["notification_number","description_long_text"]]])
ment = {}
for n, t in zip(nctext.notification_number, nctext.description_long_text.fillna("")):
    for x in re.findall(r"(?<!\d)(10\d{8})(?!\d)", t): ment.setdefault(x, n)
o["in_nc_text"] = o.index.map(ment)
dtxt = ds.comment.fillna("")+" "+ds.solution.fillna("")
dm = {}
for i, t in zip(ds.disruption_id, dtxt):
    for x in re.findall(r"(?<!\d)(10\d{8})(?!\d)", t): dm.setdefault(x, i)
o["in_disruption"] = o.index.map(dm)
o["nc_word"] = o.t.str.contains(r"\bNC\b|non.?conform", case=False)
def content(r):
    t = r.t.lower(); w = r.wcd.lower()
    if "removed due to compliance" in t: return "redacted (A400M / MT)"
    if "régul" in t or "regul" in t: return "regularisation order (OT régul)"
    if "rec-s/t" in w: return "REC subcontractor (A350-REC-S/T)"
    if re.search(r"rattrapage", t): return "catch-up (rattrapage 929/925)"
    if re.search(r"nc cable|câble|cable", t): return "cable remake"
    if re.search(r"veuillez|merci de", t): return "free-text request (FAL/customer?)"
    if re.search(r"test", t): return "test rework"
    return "other rework"
o["content"] = o.apply(content, axis=1)
def status(r):
    if isinstance(r.nc_link_2026, str): return "A. linked from a 2026 NC we have"
    if isinstance(r.nc_link_2025, str): return "B. linked from a 2025 NC"
    if r.text_nc_known: return "C. names an NC we have"
    if isinstance(r.in_nc_text, str): return "D. named in an NC text"
    if r.nc_in_text: return "E. names an NC we DON'T have"
    if isinstance(r.in_disruption, str): return "F. named in a disruption only"
    if r.nc_word: return "G. says 'NC', no number"
    return "H. no NC trace"
o["status"] = o.apply(status, axis=1)
print(o.groupby("status").agg(orders=("h","size"), hours=("h","sum")).round(0).to_string())
print()
print(pd.crosstab(o.content, o.status, values=o.h, aggfunc="sum").fillna(0).round(0).astype(int).to_string())
print(pd.crosstab(o.content, o.status).to_string())
miss = sorted({x for l in o[o.status=="E. names an NC we DON'T have"].nc_in_text for x in l})
print("\nNC numbers named in S03 text but not in our files:", len(miss), miss[:25])
known26 = sorted(all26); print("our 2026 NC number range:", min(known26), max(known26))
for st in ["E. names an NC we DON'T have", "H. no NC trace", "G. says 'NC', no number"]:
    print("\n==", st)
    g = o[o.status==st].sort_values("h", ascending=False)
    for i, r in g.head(10).iterrows(): print(f"  {i} {r.h:6.1f}h {r.prog} msn {r.msn} | {r.wcd[:60]} | {r.t[:160]!r}".replace("\\r\\n"," "))
o.to_pickle(D+"/s03_status.pkl")
