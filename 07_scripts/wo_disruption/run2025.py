import sys, re, pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
D, REPO = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO + "/02_dashboard_pack/skywise_nc_dashboard_v48/1_pipeline")
sys.path.insert(0, REPO + "/cnq_handoever")
import fto2_logic as L
from cnq.cnq_core import compute_cnq
L.PERIOD_START = "2025-01-01"; L.PERIOD_END = ""
def type_nc(df):
    wf = df.workflow_list.fillna(""); dsh = df.description_short.fillna(""); art = df.article_version_description.fillna("")
    ud = df.user_department.fillna("")
    is_rew = wf.str.startswith("REW-LIGNE"); is_test = wf.str.contains("TEST", case=False); deri = ud.str.contains("DERICHEBOURG", case=False)
    ca = wf.str.contains(r"^R[E]?W-CA-IMP", flags=re.I); lab = dsh.str.contains(r"etiquette|plaquette", flags=re.I) | art.str.contains(r"etiquette|plaquette", flags=re.I)
    expl = dsh.str.contains(r"c[aâ]ble|harnais|wire", flags=re.I) | art.str.contains(r"c[aâ]ble|harnais|wire", flags=re.I)
    cab = (ca & ~lab) | (expl & wf.str.startswith("REW-MP-IMP"))
    conds = [df.status_open_closed.fillna("").str.contains("Deleted", case=False) & (df.plant=="FTO2"),
             ud.str.strip().str.upper()=="OLMEP14/AIRBUS OPERATIONS SAS", ~df.plant.fillna("").isin(["FTO2","FT02"]),
             (df.liability_description.fillna("")=="[SUPPLIER]") | (df.responsible_defect_level1.fillna("")=="Y4"),
             cab, wf.str.startswith("REJ-LO-BP") | (is_rew & deri), wf.str.startswith("LIGNE-F-DQN"), is_rew & ~deri, is_test]
    return np.select(conds, ["QUALITE","TEST","NC Retour client","NC Fournisseur","CABLES","NC Interne","DEMANDE DE DQN","CONTROLE FINAL","CONTROLE FINAL"], default="NC Interne")
def run(sap, tag):
    sap = sap.copy()
    if "Type_NC_auto" not in sap.columns: sap["Type_NC_auto"] = type_nc(sap)
    defs = L.build_defects(sap); ncb = L.build_nc(sap, defs)
    nc = ncb.merge(sap[["notification_number","decision_status","liability","liability_description","Type_NC_auto","station"]].astype({"notification_number":str}), on="notification_number", how="left")
    nc = nc.rename(columns={"Type_NC_auto":"type_nc"})
    out, d = compute_cnq(nc, defs)
    out.to_pickle(f"{D}/cnq_{tag}.pkl"); d.to_pickle(f"{D}/defs_{tag}.pkl")
    return out, d
nc25 = pd.read_pickle(D+"/nc.pkl")
nc25["notification_number"] = nc25.notification_number.astype(str)
o25, d25 = run(nc25, "nc25")
R = REPO + "/06_input_data"
nc26 = pd.concat([pd.read_csv(R+f, dtype=str, keep_default_na=False, na_values=[""]) for f in ["/fto2_dashboard_data_12.csv","/fto2_dashboard_data_missing_ids_3.csv"]]).drop_duplicates("notification_number")
o26, d26 = run(nc26, "nc26")
print("unknown classes 2025:", d25[d25.cnq_time_known==0].sous_groupe.value_counts().to_dict())
overlap = set(o25.notification_number) & set(o26.notification_number)
print("NCs in both files:", len(overlap))
def summ(o, d, lab, start, end):
    o = o.copy(); o["dt"] = pd.to_datetime(o.date_creation, errors="coerce", utc=True)
    o = o[(o.dt>=pd.Timestamp(start,tz="UTC"))&(o.dt<pd.Timestamp(end,tz="UTC"))&(o.plant=="FTO2")]
    a = o[o.cnq_on_aec==1]
    months = o.dt.dt.to_period("M").nunique()
    dd = d[d.notification_number.isin(a.notification_number)]
    return {"period": lab, "months": months, "NCs plant FTO2": len(o), "AEC-liable NCs": len(a), "AEC NCs / month": round(len(a)/months),
            "defects on AEC NCs": len(dd), "defects / NC": round(len(dd)/len(a),2),
            "L3 EUR": round(a.cnq_cost_total.sum()), "L3 EUR / month": round(a.cnq_cost_total.sum()/months), "L3 EUR / NC": round(a.cnq_cost_total.mean()),
            "L2 EUR / NC": round(a.cnq_cost_global.mean()), "L1 EUR / NC": round(a.cnq_cost_airbus.mean()),
            "RWK %": round(100*(a.cnq_rule=="RWK").mean()), "REJ+SCR+EXC %": round(100*a.cnq_rule.isin(["REJ","SCR","EXC"]).mean()),
            "deleted %": round(100*(a.cnq_rule=="DELETED").mean()), "final insp %": round(100*a.cnq_final_inspection.mean()),
            "work share %": round(100*a.cnq_cost_work.sum()/a.cnq_cost_total.sum())}
rows = [summ(o25, d25, "2025 (Jan-Dec)", "2025-01-01", "2026-01-01"),
        summ(o26, d26, "2026 (Feb-Sep)*", "2026-02-01", "2026-10-01")]
print(pd.DataFrame(rows).set_index("period").T.to_string())
o = o25.copy(); o["dt"]=pd.to_datetime(o.date_creation, utc=True); a=o[(o.cnq_on_aec==1)&(o.dt<pd.Timestamp("2026-01-01",tz="UTC"))]
print("\n2025 by rule:", a.groupby("cnq_rule").cnq_cost_total.agg(["size","sum"]).round(0).to_dict("index"))
print("2025 monthly L3:", a.groupby(a.dt.dt.strftime("%m")).cnq_cost_total.sum().round(0).to_dict())
print("2025 liability (plant FTO2 NCs):", o[o.dt<pd.Timestamp("2026-01-01",tz="UTC")].cnq_liability_group.value_counts().to_dict())
print("2025 data gaps:", a.cnq_complete.value_counts().to_dict())
