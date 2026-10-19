import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250)
D = sys.argv[1]
nr = pd.read_pickle(D+"/nc_rw.pkl"); n25, n26 = nr["2025"], nr["2026"]
c25 = pd.read_pickle(D+"/cnq_nc25.pkl"); d25 = pd.read_pickle(D+"/defs_nc25.pkl"); c26 = pd.read_pickle(D+"/cnq_nc26.pkl")
print("2025 defects:", len(d25), "| sub_code filled:", d25.sub_code.notna().mean().round(2), "| code written in text:", d25.code.notna().mean().round(2))
print("resolved_by:", d25.resolved_by.value_counts(normalize=True).round(2).head(6).to_dict())
print("CNQ time found for sous_groupe:", d25.cnq_time_known.mean().round(3))
erma = set(n25[n25.user_department.str.contains("ERMA", na=False)].notification_number.astype(str))
def s(c, lab, start, end, drop=None):
    c = c.copy(); c["dt"] = pd.to_datetime(c.date_creation, utc=True, errors="coerce")
    a = c[(c.cnq_on_aec==1) & (c.plant=="FTO2") & (c.dt>=pd.Timestamp(start,tz="UTC")) & (c.dt<pd.Timestamp(end,tz="UTC"))]
    if drop is not None: a = a[~a.notification_number.isin(drop)]
    mo = a.dt.dt.to_period("M").nunique()
    return {"scope": lab, "NCs": len(a), "per month": round(len(a)/mo), "defects/NC": round(a.cnq_defect_lines.mean(),2), "L3 EUR": round(a.cnq_cost_total.sum()), "EUR/month": round(a.cnq_cost_total.sum()/mo), "EUR/NC": round(a.cnq_cost_total.mean())}
rows = [s(c25, "2025 all", "2025-01-01","2026-01-01"), s(c25, "2025 without ERMA", "2025-01-01","2026-01-01", erma),
        s(c25[c25.notification_number.isin(erma)], "2025 ERMA only", "2025-01-01","2026-01-01"),
        s(c26, "2026 Feb-Sep (pipeline, no ERMA)", "2026-02-01","2026-10-01")]
print(pd.DataFrame(rows).set_index("scope").to_string())
# Jan 2026 overlap: ERMA NCs in the 2025 file for Jan 2026 vs 2026 export
j = c25[pd.to_datetime(c25.date_creation, utc=True).dt.strftime("%Y-%m")=="2026-01"]
print("Jan 2026 in 2025 file:", len(j), "of which ERMA:", j.notification_number.isin(erma).sum(), "| in 2026 export:", j.notification_number.isin(c26.notification_number).sum())
# NC texts referencing a disruption id
for name, n in [("2025", n25), ("2026", n26)]:
    k = n.description_long_text.fillna("").str.contains(r"\bOZ\d{7}\b") | n.description_short.fillna("").str.contains(r"\bOZ\d{7}\b")
    print(name, "NCs quoting a disruption id (OZxxxxxxx):", k.sum())
