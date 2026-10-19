import sys, types, copy, pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
D, REPO = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO + "/cnq_handoever")
from cnq.cnq_core import compute_cnq
import cnq.cnq_params as P0
nr = pd.read_pickle(D+"/nc_rw.pkl"); calib = pd.read_pickle(D+"/calib.pkl")
CONN = ["Inversion", "Erreur de branchement", "Non connecté"]
def params(**chg):
    p = types.SimpleNamespace(**{k: copy.deepcopy(getattr(P0, k)) for k in dir(P0) if k.isupper()})
    for k, v in chg.items(): setattr(p, k, v)
    return p
def prep(tag, steps):
    nc = pd.read_pickle(f"{D}/cnq_{tag}.pkl").copy(); d = pd.read_pickle(f"{D}/defs_{tag}.pkl").copy()
    nc = nc[[c for c in nc.columns if not c.startswith("cnq_")]]; d = d[[c for c in d.columns if not c.startswith("cnq_")]]
    rw = nr["2025" if tag=="nc25" else "2026"].assign(notification_number=lambda x: x.notification_number.astype(str)).set_index("notification_number").has_rw
    nc["has_rw"] = nc.notification_number.map(rw).fillna(False)
    p = params()
    dec = nc.decision_status.astype("string").str.strip("[] ").str.upper()
    if "exc" in steps: p.RULES["EXC"] = (1,1,1,0,1,0.0,1,"Exchange","no rework order at FTO2 (0 of 20)")
    if "rej" in steps:
        p.RULES["REJW"] = (1,1,1,1,1,0.0,1,"Rejection with rework order","rework order exists")
        p.AIRBUS_STANDARD["REJW"] = p.AIRBUS_STANDARD["REJ"]
        nc["decision_status"] = np.where((dec=="REJ") & nc.has_rw, "REJW", nc.decision_status)
    if "ret" in steps:
        p.RULES["RET"] = (1,1,1,0,1,0.0,0,"Customer return","FTO2 handling only")
        p.AIRBUS_STANDARD["RET"] = p.AIRBUS_STANDARD["RWK"]
        isret = nc.perimetre.astype("string").eq("Retour client").fillna(False) & dec.isin(["RWK","EXC"])
        nc["decision_status"] = np.where(isret, "RET", nc.decision_status)
        p.CUSTOMER_RETURN_EXTRA = 100.0   # 2 h quality analysis per return (Sept A350 time sheet: 15 h / 8 returns)
    if "alert" in steps:
        p.NO_ALERT_TYPES = ["TEST", "CONTROLE FINAL", "NC RETOUR CLIENT"]
    if "conn" in steps:
        d = d.reset_index(drop=True)
        isc = d.sous_groupe.isin(CONN)
        rank = isc.groupby(d.notification_number).cumsum()
        d.loc[isc & (rank > 1), "sous_groupe"] = "Branchement – erreur suivante"
        p.DEFECT_TIMES["Branchement – erreur suivante"] = (15, 0.0, "Connection error (each after the first)", "WO", "S03 planned: ~15 min per extra error")
    if "cls" in steps:
        p.DEFECT_TIMES["Mesure hors tolérance"] = p.DEFECT_TIMES["Point de masse / mesure"]
        p.DEFECT_TIMES["Dommage – tresse de masse"] = p.DEFECT_TIMES["Dommage – câble"]
    out, dout = compute_cnq(nc, d, params=p)
    if "alert" in steps:   # alert only where an operator raises one
        t = out.type_nc.astype("string").str.upper().fillna("")
        off = t.isin(p.NO_ALERT_TYPES)
        out.loc[off, "cnq_cost_total"] -= out.loc[off, "cnq_cost_alert"]
        out.loc[off, "cnq_cost_aec"] = out.loc[off, "cnq_cost_total"] * out.loc[off, "cnq_on_aec"]
        out.loc[off, "cnq_min_alert"] = 0
    return out
erma = set(nr["2025"][nr["2025"].user_department.str.contains("ERMA", na=False)].notification_number.astype(str))
def total(out, tag):
    o = out.copy(); o["dt"] = pd.to_datetime(o.date_creation, utc=True, errors="coerce")
    if tag == "nc25": a = o[(o.cnq_on_aec==1)&(o.plant=="FTO2")&(o.dt.dt.year==2025)&(~o.notification_number.isin(erma))]
    else: a = o[(o.cnq_on_aec==1)&(o.plant=="FTO2")&(o.dt>=pd.Timestamp("2026-02-01",tz="UTC"))&(o.dt<pd.Timestamp("2026-10-01",tz="UTC"))]
    return a
def vs_planned(out):
    o = out.set_index("notification_number"); r = calib[(calib.cnq_rule=="RWK") & calib.complete]
    w = (o.cnq_min_setup + o.cnq_min_hands_on).reindex(r.index)
    return pd.DataFrame({"planned": r.total, "model": w, "type": r.Type_NC_auto}).groupby("type")[["planned","model"]].sum().round(0)
scen = [("Today", []), ("+ Exchange: no rework", ["exc"]), ("+ Rejection: rework only if order", ["exc","rej"]),
        ("+ Customer return: handling + 2 h analysis", ["exc","rej","ret"]), ("+ Alert only when operator raises it", ["exc","rej","ret","alert"]),
        ("+ Connection errors 35 then 15 min", ["exc","rej","ret","alert","conn"]), ("+ Missing classes", ["exc","rej","ret","alert","conn","cls"])]
rows = []
for name, st in scen:
    o26 = prep("nc26", st); o25 = prep("nc25", st)
    a26, a25 = total(o26, "nc26"), total(o25, "nc25")
    rows.append({"scenario": name, "2026 Feb-Sep EUR": round(a26.cnq_cost_total.sum()), "2026 EUR/NC": round(a26.cnq_cost_total.mean()),
                 "2025 (no ERMA) EUR": round(a25.cnq_cost_total.sum()), "2025 EUR/NC": round(a25.cnq_cost_total.mean())})
    if name in ("Today", "+ Missing classes"):
        print(f"\n{name}: planned vs model (setup + defects) on the 84 complete rework orders"); print(vs_planned(o26).to_string())
    if name == "+ Missing classes": final26 = a26
print(); print(pd.DataFrame(rows).set_index("scenario").to_string())
b = total(prep("nc26", []), "nc26").set_index("notification_number").cnq_cost_total; f = final26.set_index("notification_number").cnq_cost_total
ty = total(prep("nc26", []), "nc26").set_index("notification_number").type_nc
print("\n2026 change by NC type (EUR):"); print(pd.DataFrame({"today": b.groupby(ty).sum(), "after": f.groupby(ty).sum()}).assign(diff=lambda x: x.after-x.today).round(0).to_string())

# customer returns (plant != FTO2), 2026 all months
def returns(out):
    o = out[(out.cnq_on_aec==1) & out.perimetre.astype("string").eq("Retour client").fillna(False)]
    return len(o), round(o.cnq_cost_total.sum()), round(o.cnq_cost_total.mean())
print("\ncustomer returns 2026 (n, EUR, EUR/NC): today", returns(prep("nc26", [])), "| after", returns(prep("nc26", ["exc","rej","ret","alert","conn","cls"])))
# cable / internal gap: outliers?
r = calib[(calib.cnq_rule=="RWK") & calib.complete].copy(); r["model"] = r.cnq_min_setup + r.cnq_min_hands_on
for ty in ["CABLES", "NC Interne"]:
    g = r[r.Type_NC_auto==ty].sort_values("total", ascending=False)
    print(f"\n{ty}: n={len(g)} planned {g.total.sum():.0f} vs model {g.model.sum():.0f} | medians planned {g.total.median():.0f} model {g.model.median():.0f}")
    print("  top 3 planned:", [(i, round(a), round(b), int(c)) for i, a, b, c in zip(g.index[:3], g.total[:3], g.model[:3], g.cnq_defect_lines[:3])])
    h = g.iloc[2:]; print(f"  without the 2 largest: planned {h.total.sum():.0f} vs model {h.model.sum():.0f}")
