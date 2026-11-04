"""Cost of non-quality (CNQ): the settings, read from the tables in config/.

  2_cout_parametres.csv        hourly rates and minutes per step (everyday adjustments by a team lead)
  2_cout_qui_fait_quoi.csv     which function (production, quality, ME) does each step, so which rate it is charged at
  2_cout_decisions.csv         which steps each decision (Rework, Scrap, DQN...) charges
  2_libelles_lieu_detection.csv English label of each "where found" value
  3_cout_temps_defauts.csv     minutes and material per defect type (expert)
  3_cout_airbus.csv            the official Airbus standard cost per decision (expert)
  3_cout_ordres_operations.csv how the rework-order operations are read (expert)
  3_cout_avance.csv            the model's other switches and lists (expert)

This module gives the model the same names it has always used (RATE_PROD, MIN_ALERT, RULES, DEFECT_TIMES...), so the
calculation in model.py does not depend on how the settings are stored.

Where each figure comes from is written in the tables ("base" column): LOCAL (AEC's own estimate), TEAM (the team's code
table), OFFICIAL (Airbus cost model MC.QU.02), BORROWED, WO (planned time on the rework orders), MES (aléas), ASSUMED.
"""
from .. import config


def _number(text, where):
    t = str(text).strip().replace(",", ".")
    try:
        return int(t) if t.lstrip("-").isdigit() else float(t)
    except ValueError:
        raise config.ConfigError("%s: '%s' is not a number" % (where, text))


def _values(name, key="nom", value="valeur"):
    t = config.table(name, [key, value])
    return {r[key].strip(): r[value].strip() for _, r in t.iterrows()}


def _need(d, name, keys):
    missing = [k for k in keys if k not in d]
    if missing:
        raise config.ConfigError("%s: the line(s) %s are missing" % (name, ", ".join(missing)))


def _list(text):
    return [x.strip() for x in str(text).split("|") if x.strip()]


def _yes(text, where):
    t = str(text).strip().lower()
    if t not in ("oui", "non"):
        raise config.ConfigError("%s: write 'oui' or 'non', found '%s'" % (where, text))
    return t == "oui"


# ---------------------------------------------------------------- 2_cout_parametres.csv
_F = "2_cout_parametres.csv"
_p = _values(_F)
_need(_p, _F, ["taux_production", "taux_qualite", "taux_me", "taux_ingenierie", "minutes_alerte", "minutes_redaction",
               "minutes_redaction_controle_final", "minutes_support", "minutes_preparation", "minutes_travail_minimum",
               "minutes_recontrole", "minutes_travail_sans_defaut", "minutes_defaut_inconnu", "minutes_branchement_suivant",
               "facteur_travail_nc_interne", "minutes_redaction_niveau2", "minutes_travail_niveau2", "forfait_retour_client"])
_n = {k: _number(v, "%s, %s" % (_F, k)) for k, v in _p.items()}

RATES = {"prod": float(_n["taux_production"]), "quality": float(_n["taux_qualite"]), "me": float(_n["taux_me"])}
RATE_ENGINEERING = float(_n["taux_ingenierie"])
MIN_ALERT = _n["minutes_alerte"]
MIN_WRITE_NC = _n["minutes_redaction"]
MIN_WRITE_NC_FINAL = _n["minutes_redaction_controle_final"]
MIN_SUPPORT = _n["minutes_support"]
MIN_SETUP = _n["minutes_preparation"]
MIN_WORK_FLOOR = _n["minutes_travail_minimum"]
MIN_RECHECK_CLOSE = _n["minutes_recontrole"]
MIN_HANDS_ON_NO_DEFECT = _n["minutes_travail_sans_defaut"]
MIN_DEFAULT_DEFECT = _n["minutes_defaut_inconnu"]
MIN_CONNECTION_NEXT = _n["minutes_branchement_suivant"]
INTERNAL_WORK_FACTOR = float(_n["facteur_travail_nc_interne"])
MIN_WRITE_NC_GLOBAL = _n["minutes_redaction_niveau2"]
MIN_WORK_GLOBAL = _n["minutes_travail_niveau2"]
CUSTOMER_RETURN_EXTRA = float(_n["forfait_retour_client"])

# ---------------------------------------------------------------- 2_cout_qui_fait_quoi.csv
_F = "2_cout_qui_fait_quoi.csv"
_WHO = {"production": "prod", "qualite": "quality", "me": "me"}
STEP_WHO = {}
for _, _r in config.table(_F, ["etape", "fonction"]).iterrows():
    if _r["fonction"].strip() not in _WHO:
        raise config.ConfigError("%s, step %s: function must be one of %s" % (_F, _r["etape"], ", ".join(_WHO)))
    STEP_WHO[_r["etape"].strip()] = _WHO[_r["fonction"].strip()]
_need(STEP_WHO, _F, ["alert", "writing", "support", "setup", "hands_on", "recheck"])
STEP_RATES = {step: RATES[who] for step, who in STEP_WHO.items()}
RATE_PROD, RATE_QUALITY, RATE_ME = RATES["prod"], RATES["quality"], RATES["me"]
RATE_STANDARD = RATE_PROD   # the former single rate; kept for readers that still use one rate

# ---------------------------------------------------------------- 2_cout_decisions.csv
_F = "2_cout_decisions.csv"
RULE_FIELDS = ("alert", "write", "support", "work", "recheck", "eng_hours", "part", "label", "basis")
_cols = ["code", "alerte", "redaction", "support", "travail", "recontrole", "heures_ingenierie", "valeur_piece", "libelle", "base"]
RULES = {}
for _, _r in config.table(_F, _cols).iterrows():
    _w = "%s, decision %s" % (_F, _r["code"])
    _steps = [_number(_r[c], _w) for c in ("alerte", "redaction", "support", "travail", "recontrole")]
    if any(v not in (0, 1) for v in _steps):
        raise config.ConfigError("%s: the step columns take 1 (charged) or 0 (not charged)" % _w)
    RULES[_r["code"].strip()] = tuple(_steps) + (float(_number(_r["heures_ingenierie"], _w)), _number(_r["valeur_piece"], _w),
                                                 _r["libelle"], _r["base"])
_need(RULES, _F, ["DELETED", "UNKNOWN"])

# ---------------------------------------------------------------- 3_cout_temps_defauts.csv (derived classes: factor x their base)
_F = "3_cout_temps_defauts.csv"
DEFECT_FIELDS = ("minutes", "material_eur", "label_en", "reference_code", "basis")
DEFECT_TIMES, DERIVED_TIMES = {}, {}
_rows = config.table(_F, ["classe", "minutes", "materiel_eur", "libelle_en", "code_reference", "base", "calcule_depuis", "facteur"])
for _, _r in _rows.iterrows():
    _k, _w = _r["classe"].strip(), "%s, %s" % (_F, _r["classe"])
    if _r["calcule_depuis"].strip():
        DERIVED_TIMES[_k] = (_r["calcule_depuis"].strip(), _number(_r["facteur"], _w))
        DEFECT_TIMES[_k] = (None, float(_number(_r["materiel_eur"], _w)), _r["libelle_en"], None, None)
    else:
        DEFECT_TIMES[_k] = (_number(_r["minutes"], _w), float(_number(_r["materiel_eur"], _w)), _r["libelle_en"],
                            _r["code_reference"], _r["base"])
for _k, (_base, _factor) in DERIVED_TIMES.items():
    if _base not in DEFECT_TIMES or _base in DERIVED_TIMES:
        raise config.ConfigError("%s, %s: 'calcule_depuis' must name a class of the table that is not itself derived" % (_F, _k))
    _m, _mat, _en, _ref, _basis = DEFECT_TIMES[_k]
    DEFECT_TIMES[_k] = (DEFECT_TIMES[_base][0] * _factor, _mat, _en, DEFECT_TIMES[_base][3],
                        "TEAM RULE - %d x \"%s\"" % (_factor, DEFECT_TIMES[_base][2]))

# ---------------------------------------------------------------- 3_cout_airbus.csv
_F = "3_cout_airbus.csv"
AIRBUS_STANDARD = {k: float(_number(v, "%s, %s" % (_F, k))) for k, v in _values(_F, "code", "eur_par_nc").items()}

# ---------------------------------------------------------------- 2_libelles_lieu_detection.csv
WHERE_FOUND_LABELS = _values("2_libelles_lieu_detection.csv", "valeur", "libelle_en")

# ---------------------------------------------------------------- 3_cout_ordres_operations.csv
_F = "3_cout_ordres_operations.csv"
ORDER_OP_KINDS, ORDER_SETUP_KINDS = [], []
for _, _r in config.table(_F, ["genre", "texte_regex", "etape"]).iterrows():
    ORDER_OP_KINDS.append((_r["genre"].strip(), _r["texte_regex"]))
    if _r["etape"].strip() == "setup":
        ORDER_SETUP_KINDS.append(_r["genre"].strip())

# ---------------------------------------------------------------- 3_cout_avance.csv
_F = "3_cout_avance.csv"
_a = _values(_F)
_need(_a, _F, ["version_modele", "usine_responsable", "types_controle_final", "types_sans_alerte", "prefixes_ordre_retouche",
               "classes_branchement", "types_internes", "utiliser_temps_ordres", "types_ordres", "unites_minutes",
               "utiliser_temps_aleas", "types_aleas", "fenetre_alea_heures", "aleas_erma_regex", "colonne_cout_retour_client"])
MODEL_VERSION = _a["version_modele"]
AEC_PLANT_CODE = _a["usine_responsable"]
FINAL_INSPECTION_TYPES = _list(_a["types_controle_final"])
NO_ALERT_TYPES = _list(_a["types_sans_alerte"])
REWORK_ORDER_PREFIXES = _list(_a["prefixes_ordre_retouche"])
CONNECTION_CLASSES = _list(_a["classes_branchement"])
INTERNAL_TYPES = _list(_a["types_internes"])
USE_ORDER_TIME = _yes(_a["utiliser_temps_ordres"], _F + ", utiliser_temps_ordres")
ORDER_TYPES = _list(_a["types_ordres"])
ORDER_UNIT_MINUTES = {u.split("=")[0].strip(): float(_number(u.split("=")[1], _F + ", unites_minutes")) for u in _list(_a["unites_minutes"])}
USE_ALEA_TIME = _yes(_a["utiliser_temps_aleas"], _F + ", utiliser_temps_aleas")
ALEA_TYPES = _list(_a["types_aleas"])
ALEA_LINK_HOURS = tuple(_number(x, _F + ", fenetre_alea_heures") for x in _list(_a["fenetre_alea_heures"]))
ALEA_ERMA_DESIGNATION = _a["aleas_erma_regex"]
CUSTOMER_RETURN_COST_COLUMN = _a["colonne_cout_retour_client"]
