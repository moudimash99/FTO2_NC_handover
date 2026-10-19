import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 140); pd.set_option("display.max_rows", 200)
D, R = sys.argv[1], sys.argv[2]
wo = pd.read_pickle(D+"/wo.pkl"); o = pd.read_pickle(D+"/s03_status.pkl"); nr = pd.read_pickle(D+"/nc_rw.pkl"); n26 = nr["2026"]; n25 = nr["2025"]
s3 = wo[wo.order_type=="S03"].copy(); s3["im"] = pd.to_numeric(s3.labor_standard_value, errors="coerce").fillna(0)
wcs = s3.groupby("order_number").work_center.apply(set)
def family(ws, t):
    if any(w.startswith(("RECX","SUBR")) for w in ws): return "REC (FAL)"
    if any(w.startswith("IEV") for w in ws): return "IEVB (MSN 700/701)"
    if "regul" in t.lower() or "régul" in t.lower(): return "Regularisation"
    if "removed due to compliance" in t.lower(): return "A400M (redacted)"
    return "FTO2 shop floor"
o["family"] = [family(wcs[i], t) for i, t in zip(o.index, o.t)]
o["traced"] = o.status.str[0].isin(list("ABCDEF"))
print(o.groupby("family").agg(orders=("h","size"), hours=("h","sum"), traced_orders=("traced","sum"), traced_hours=("h", lambda x: x[o.loc[x.index,"traced"]].sum())).round(0).to_string())
print("MSNs of IEVB orders:", o[o.family.str.startswith("IEVB")].msn.value_counts().head(5).to_dict())
fi = n25[n25.msn.astype(str).isin(["700","701"])]
print("2025 NCs on MSN 700/701:", len(fi), "constituent:", fi.constituent_assembly.str[:2].value_counts().head(4).to_dict(), "stations:", fi.station.value_counts().head(4).to_dict())
# shop floor part
sf = o[o.family=="FTO2 shop floor"].copy()
pref = s3.groupby("order_number").work_center.agg(lambda x: x.str[:2].value_counts().index[0])
sf["line"] = sf.index.map(pref).map({"4V":"A350 (4V)","4F":"A330 (4F)","4M":"A320 (4M)","4D":"4D","4T":"Test (4T)","4Q":"Quality (4Q)"}).fillna("other")
sf["prog"] = sf.prog
print("\nshop floor by programme:", sf.groupby("prog").agg(orders=("h","size"), hours=("h","sum"), traced=("traced","sum")).round(0).to_dict("index"))
print("shop floor by content:"); print(sf.groupby(["content","traced"]).agg(orders=("h","size"), hours=("h","sum")).round(0).unstack(fill_value=0).to_string())
# untraced shop-floor orders: read them
u = sf[~sf.traced].copy()
u["first"] = u.t.str.replace(r"\s+"," ",regex=True)
def kind(t):
    t = t.lower()
    if re.search(r"gestion nc|alerte qualit|ad-hoc|accompagnement", t): return "quality admin (NC handling booked)"
    if re.search(r"fagot|stock|débiter du", t): return "cable cutting for stock"
    if re.search(r"nc cable|suite à|suite a", t): return "cable remake (NC ref. without number)"
    if re.search(r"impri|câble|cable|débit", t): return "cable print/remake, no NC reference"
    if re.search(r"test|continuit|emi|sonn", t): return "test / re-test"
    if re.search(r"modif|evol|mod |retrofit|standard", t): return "modification"
    return "other"
u["kind"] = u.first.map(kind)
print("\nUntraced shop-floor orders:", len(u), round(u.h.sum()))
print(u.groupby("kind").agg(orders=("h","size"), hours=("h","sum"), zero_h=("h", lambda x: (x==0).sum())).round(1).to_string())
for k, g in u.groupby("kind"):
    print(f"\n-- {k}")
    for i, r in g.sort_values("h", ascending=False).head(5).iterrows():
        print(f"   {i} {r.h:5.1f}h {r.prog} msn {r.msn} | {r.first[:230]}")
o.to_pickle(D+"/s03_family.pkl")
