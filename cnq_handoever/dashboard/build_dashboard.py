# -*- coding: utf-8 -*-
"""
Build the check-sheet dashboard (one self-contained HTML file) from the pipeline outputs.

    python dashboard/build_dashboard.py            (after tests/run_local.py)

Reads sample_output/*.csv and cnq/cnq_params.py, writes dashboard/cnq_dashboard.html and
dashboard/dashboard_data.json (used by tests/test_dashboard.js).
"""
import datetime, json, os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from cnq import cnq_params as P  # noqa: E402

nc = pd.read_csv(os.path.join(ROOT, "sample_output", "fto2_nc_cnq.csv"), low_memory=False)
d = pd.read_csv(os.path.join(ROOT, "sample_output", "fto2_defects_cnq.csv"), low_memory=False)
nc = nc.sort_values("notification_number").reset_index(drop=True)
idx = {n: i for i, n in enumerate(nc.notification_number)}
nn = lambda v: None if pd.isna(v) else v

classes = list(P.DEFECT_TIMES.keys())
cidx = {k: i for i, k in enumerate(classes)}
unknown = sorted(set(d.sous_groupe) - set(classes))
assert not unknown, "defect classes missing from cnq_params.DEFECT_TIMES: %s" % unknown

RULE_FR = {"RWK": "Retouche", "EXC": "Échange", "REJ": "Rejet", "SCR": "Rebut", "DQN": "Demande de modification de conception (DQN)",
           "ACC": "Acceptation en l'état", "PNC": "NC potentielle", "NDC": "Sans décision", "DELETED": "NC supprimée", "UNKNOWN": "Code de décision inconnu"}
AIRBUS_BASIS = {
    "RWK": {"flag": 0, "en": "Official: rework as per design data", "fr": "Officiel : retouche selon la définition (DDS)"},
    "EXC": {"flag": 1, "en": "Assumed: taken as a rework", "fr": "Hypothèse : assimilé à une retouche"},
    "ACC": {"flag": 0, "en": "Official: acceptable as is", "fr": "Officiel : acceptable en l'état"},
    "DQN": {"flag": 1, "en": "Official figure, assumed match: engineering assessment", "fr": "Chiffre officiel, correspondance supposée : évaluation par l'ingénierie"},
    "REJ": {"flag": 1, "en": "Assumed: creation, assessment, decision", "fr": "Hypothèse : création, évaluation, décision"},
    "SCR": {"flag": 1, "en": "Assumed: creation, assessment, decision", "fr": "Hypothèse : création, évaluation, décision"},
    "PNC": {"flag": 1, "en": "Assumed: creation, assessment, decision", "fr": "Hypothèse : création, évaluation, décision"},
    "NDC": {"flag": 1, "en": "Assumed: creation step only", "fr": "Hypothèse : étape de création uniquement"},
    "DELETED": {"flag": 1, "en": "Assumed: creation step only", "fr": "Hypothèse : étape de création uniquement"},
}
BASIS = {
    "TEAM": (0, "Team table", "Table de l'équipe"),
    "BORROWED - 2021 BU1 study, no time in the team table": (1, "Borrowed: 2021 BU1 study, no time in the team table", "Emprunté : étude BU1 de 2021, pas de temps dans la table de l'équipe"),
    "TEAM - material looks too high, check": (1, "Team table: material looks too high, to check", "Table de l'équipe : coût matière à vérifier, semble trop élevé"),
    "TEAM - very mixed class (1 to 120 min in the table)": (1, "Team table: very mixed class (1 to 120 min)", "Table de l'équipe : classe très hétérogène (1 à 120 min)"),
}
def basis(s):
    if s.startswith("TEAM RULE"):
        return {"flag": 0, "en": "Team rule", "fr": "Règle de l'équipe"}
    f, en, fr = BASIS[s]
    return {"flag": f, "en": en, "fr": fr}

dates = pd.to_datetime(nc.date_creation)
data = {
    "meta": {"version": P.MODEL_VERSION, "built": datetime.date.today().isoformat(),
             "from": dates.min().strftime("%Y-%m-%d"), "to": dates.max().strftime("%Y-%m-%d"),
             "source": {"en": "FTO2 NC and defect datasets, parser v4.7", "fr": "jeux de données NC et défauts FTO2, parseur v4.7"}},
    "rules": {k: dict(alert=v[0], write=v[1], support=v[2], work=v[3], recheck=v[4], eng=v[5], part=v[6], label={"en": v[7], "fr": RULE_FR[k]}) for k, v in P.RULES.items()},
    "airbusBasis": AIRBUS_BASIS,
    "classes": [{"k": k, "en": P.DEFECT_TIMES[k][2], "ref": P.DEFECT_TIMES[k][3], "basis": basis(P.DEFECT_TIMES[k][4])} for k in classes],
    "nc": [[int(r.notification_number), nn(r.cnq_month), nn(r.programme), nn(r.get("produit")), r.cnq_rule, int(r.cnq_on_aec), r.cnq_liability_group,
            int(r.cnq_final_inspection), int(r.cnq_customer_return), r.cnq_where_found, nn(r.statut),
            int(r.cnq_alert_raised), int(r.cnq_work_factor != 1)] for _, r in nc.iterrows()],
    # same line order as the pipeline (the first connection error of an NC is the first in this order)
    "lines": [[idx[r.notification_number], cidx[r.sous_groupe], int(r.qty) if "qty" in d.columns and not pd.isna(r.qty) else 1,
               "" if pd.isna(r.text) else " ".join(str(r.text).split())[:150]] for _, r in d.sort_values(["notification_number", "seq"], kind="mergesort").iterrows()],
}
# default parameters = the pipeline's. Base minutes are the values BEFORE the "2 x" rule; derived classes point to their base.
base_min = {k: v[0] for k, v in P.DEFECT_TIMES.items()}
p = {"rate": P.RATE_STANDARD, "rateEng": P.RATE_ENGINEERING, "alert": P.MIN_ALERT, "write": P.MIN_WRITE_NC, "writeFinal": P.MIN_WRITE_NC_FINAL,
     "support": P.MIN_SUPPORT, "setup": P.MIN_SETUP, "floor": P.MIN_WORK_FLOOR, "recheck": P.MIN_RECHECK_CLOSE, "noDefect": P.MIN_HANDS_ON_NO_DEFECT,
     "writeGlobal": P.MIN_WRITE_NC_GLOBAL, "workGlobal": P.MIN_WORK_GLOBAL, "crExtra": P.CUSTOMER_RETURN_EXTRA, "airbus": dict(P.AIRBUS_STANDARD),
     "connNext": P.MIN_CONNECTION_NEXT, "internalFactor": P.INTERNAL_WORK_FACTOR,
     "classes": [{"min": base_min[k], "mat": P.DEFECT_TIMES[k][1], "conn": k in P.CONNECTION_CLASSES,
                  "of": cidx[P.DERIVED_TIMES[k][0]] if k in P.DERIVED_TIMES else None,
                  "factor": P.DERIVED_TIMES[k][1] if k in P.DERIVED_TIMES else None} for k in classes]}

# worked examples offered as buttons: real NCs, chosen by simple rules
a = nc[nc.cnq_on_aec == 1]
def first(q, by=None, asc=True):
    s = a.query(q)
    if by: s = s.sort_values(by, ascending=asc)
    return None if s.empty else idx[s.notification_number.iloc[0]]
ex = [(("Retouche à un défaut", "A one-defect rework"), first("cnq_rule=='RWK' and cnq_defect_lines==1 and cnq_where_found=='In-process (internal)' and cnq_min_hands_on==10")),
      (("Retouche au contrôle final", "A final-inspection rework"), first("cnq_rule=='RWK' and cnq_final_inspection==1 and cnq_defect_lines>=6 and cnq_defect_lines<=9", "cnq_cost_total", False)),
      (("Rejet", "A reject"), first("cnq_rule=='REJ'")), (("NC supprimée", "A deleted NC"), first("cnq_rule=='DELETED'")),
      (("Demande DQN", "A design query"), first("cnq_rule=='DQN'")), (("Retour client", "A customer return"), first("cnq_customer_return==1 and cnq_rule=='RWK'"))]
data["examples"] = [{"label": {"fr": l[0], "en": l[1]}, "i": i} for l, i in ex if i is not None]

logic = open(os.path.join(HERE, "dashboard_logic.js"), encoding="utf-8").read()
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
js = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = tpl.replace("/*__LOGIC__*/", logic).replace("/*__DATA__*/null", js(data)).replace("/*__P__*/null", js(p))
open(os.path.join(HERE, "cnq_dashboard.html"), "w", encoding="utf-8").write(html)
json.dump({"DATA": data, "P": p}, open(os.path.join(HERE, "dashboard_data.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("dashboard written: %d NCs, %d lines, %.0f kB" % (len(data["nc"]), len(data["lines"]), len(html.encode("utf-8")) / 1024))
print("examples:", [(e["label"]["en"], data["nc"][e["i"]][0]) for e in data["examples"]])
