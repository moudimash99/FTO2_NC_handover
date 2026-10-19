import sys, re, pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 100)
D, REPO = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO + "/cnq_handoever")
from cnq.cnq_core import compute_cnq
wo = pd.read_pickle(D+"/wo.pkl"); ds = pd.read_pickle(D+"/ds2.pkl"); fam = pd.read_pickle(D+"/s03_family.pkl")
nr = pd.read_pickle(D+"/nc_rw.pkl"); n26, n25 = nr["2026"], nr["2025"]; lk = pd.read_pickle(D+"/ds_nc_links.pkl")
wo["h"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0)/100
ds["tl"] = pd.to_numeric(ds.time_lost)
# new-model CNQ for 2026 and 2025
out = {}
for tag in ["nc26", "nc25"]:
    nc = pd.read_pickle(f"{D}/cnq_{tag}.pkl"); d = pd.read_pickle(f"{D}/defs_{tag}.pkl")
    nc = nc[[c for c in nc.columns if not c.startswith("cnq_")]]; d = d[[c for c in d.columns if not c.startswith("cnq_")]]
    links = nr["2025" if tag == "nc25" else "2026"][["notification_number", "linked_document", "work_order"]].astype({"notification_number": str})
    nc = nc.drop(columns=[c for c in ("linked_document", "work_order") if c in nc.columns]).merge(links, on="notification_number", how="left")
    out[tag], _ = compute_cnq(nc, d)
c26, c25 = out["nc26"].set_index("notification_number"), out["nc25"].set_index("notification_number")
R = {}
# ---- missed point a: aléas followed by an NC whose type gets no alert step
lk2 = lk.merge(c26[["type_nc","cnq_alert_raised","cnq_on_aec"]], left_on="notification_number", right_index=True, how="left")
q = lk2[lk2.type_desc.str.startswith("QLS")]
print("quality aléas followed by an NC:", len(q), "| NC has no alert step:", (q.cnq_alert_raised==0).sum(), "h lost", round(q[q.cnq_alert_raised==0].tl.astype(float).sum()/60,1), q[q.cnq_alert_raised==0].type_nc.value_counts().to_dict())
print("declared time on aléas that led to an NC: mean", round(q.tl.astype(float).mean(),1), "median", q.tl.astype(float).median())
# ---- disruption block option B
qb = ds[ds.type_desc.str.startswith("QLS", na=False) & ~ds.has_nc].copy()
print("option B:", len(qb), "aléas,", round(qb.tl.sum()/60,1), "h,", round(qb.tl.sum()/60*50), "EUR")
qb["wf201_like"] = qb.wo_designation.fillna("").str.contains("1101VB|MIP", case=False) | qb.ds_material.fillna("").str.contains("1101", case=False)
print("  of which A30 line:", (qb.line=="A30").sum(), "| MIP/1101VB (where ERMA works):", qb.wf201_like.sum(), "| no work order:", qb.work_order.isna().sum())
R["blockB"] = qb
# ---- M1: other kinds with quality wording, no NC
txt = (ds.comment.fillna("")+" "+ds.solution.fillna("")).str.lower()
qual_words = r"ab[iî]m|endommag|d[ée]t[ée]rior|trop court|coup[ée]|cass[ée]|d[ée]chir|ray[ée]|non.?conform|d[ée]fectu|\bhs\b|\bnc\b|invers|mal (serti|mont|branch|pos)|mauvais(e)? (serti|branch|montage|mise en)|oubli|doublon|erreur de (c[aâ]blage|branchement|montage)"
g3 = ds[~ds.type_desc.str.startswith("QLS", na=False) & ~ds.has_nc & txt.str.contains(qual_words)].copy()
t3 = txt[g3.index]
def cat(t):
    if re.search(r"c[aâ]ble|cable|fil\b|bifilaire|trifilaire", t) and re.search(r"ab[iî]m|endommag|trop court|coup|d[ée]t[ée]rior|doublon", t): return "Cable damaged, cut too short or duplicated"
    if re.search(r"serti|mal mont|mauvais(e)? (montage|mise en)|oubli|invers|erreur de|mal branch|mal pos", t): return "Workmanship error on the line (crimping, forgotten, wrong fitting)"
    if re.search(r"cass|\bhs\b|fissur|d[ée]chir|ray[ée]|endommag|ab[iî]m|d[ée]fectu|d[ée]t[ée]rior", t): return "Part or component broken, damaged or faulty"
    if re.search(r"non.?conform|mauvais|erron|incorrect", t): return "Wrong or non-conforming part or document supplied"
    return "Other wording"
g3["category"] = t3.map(cat)
print("\nM1 categories:"); print(g3.groupby("category").agg(n=("tl","size"), hours=("tl", lambda x: round(x.sum()/60,1))).to_string())
print("  by kind:", pd.crosstab(g3.category, g3.type_desc.str[:8]).to_dict())
R["m1"] = g3
# ---- customer returns: where are their rework orders
cr = c26[(c26.cnq_on_aec==1) & (c26.cnq_customer_return==1)].copy()
rw = n26.set_index("notification_number").rw
cr["rework_orders"] = cr.index.map(lambda n: ", ".join(rw.get(n, [])) if isinstance(rw.get(n, []), list) else "")
cr["in_file"] = cr.index.map(lambda n: [o for o in (rw.get(n, []) or []) if o in fam.index])
cr["fam"] = cr.in_file.apply(lambda l: ", ".join(sorted(set(fam.loc[l].family))) if l else "")
cr["planned_h"] = cr.in_file.apply(lambda l: fam.loc[l].h.sum() if l else np.nan)
print("\ncustomer returns 2026:", len(cr), "| with a rework order link:", (cr.rework_orders!="").sum(), "| order in Sept file:", (cr.in_file.str.len()>0).sum(), cr.fam.value_counts().to_dict())
print("  cost now:", round(cr.cnq_cost_total.sum()), "admin", round(cr.cnq_cost_admin.sum()), "work", round(cr.cnq_cost_work.sum()), "material", round(cr.cnq_cost_material.sum()))
print("  REC orders mentioning client/retour:", fam[(fam.family=="REC (FAL)") & fam.t.str.contains("client|retour", case=False)].shape[0])
R["cr"] = cr
# ---- H6: rework orders with no planned time
z = fam[fam.h == 0]
print("\nrework orders with no planned time:", len(z), "of", len(fam), z.family.value_counts().to_dict(), "| traced to NC:", z.traced.sum())
R["noplan"] = z
# ---- exceptional NCs: planned >> model (new model)
m = pd.read_pickle(D+"/calib.pkl")
m = m.join(c26[["cnq_min_setup","cnq_min_hands_on"]].rename(columns=lambda c: c+"_new"))
m["model_new"] = m.cnq_min_setup_new + m.cnq_min_hands_on_new
ex = m[(m.cnq_rule=="RWK") & (m.total >= 180) & (m.total > 2.5*m.model_new)].sort_values("total", ascending=False)
print("\nexceptional (planned >= 3h and > 2.5x model):", len(ex)); print(ex[["total","model_new","cnq_defect_lines","Type_NC_auto"]].round(0).to_string())
R["exc"] = ex
# ERMA with new model
erma = n25[n25.user_department.str.contains("ERMA", na=False)].notification_number.astype(str)
e = c25.loc[c25.index.isin(erma)]; e = e[(e.cnq_on_aec==1) & (pd.to_datetime(e.date_creation, utc=True).dt.year==2025)]
print("\nERMA 2025 (new model):", len(e), round(e.cnq_cost_total.sum()))
pd.to_pickle({"R": R, "c26": c26, "c25": c25}, D+"/sheet_data.pkl")
