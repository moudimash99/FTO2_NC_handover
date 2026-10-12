"""
FTO2 NC dashboard: pipeline logic (parser v4.8).

Reads the SAP NC dataset and builds two datasets:
  fto2_defects  one row per defect: Pareto category, sub-category, RCA, minor flag, plus the NC fields
  fto2_nc       one row per NC: NC fields, number of defects, defects per Pareto category

Everything specific to your Skywise is in the EDIT block below. Nothing else needs changing.
This file is plain pandas (no Foundry import); fto2_transforms.py connects it to Skywise.
"""
import re
import pandas as pd

try:                                    # Code Repository: the parser file sits next to this one
    from . import nc_defect_parser as P
except Exception:
    try:                                # local test
        import nc_defect_parser as P
    except Exception:                   # Code Workbook: the parser is pasted above, in Global code
        P = None

# =============================== EDIT ===============================
# Dataset paths: right-click the dataset in Skywise > Copy path.
SAP_NC_DATASET = "/EDIT/path/of/the/SAP NC dataset your dashboard already uses"
DEFECTS_DATASET = "/EDIT/path/of/your/project folder/fto2_defects"
NC_DATASET = "/EDIT/path/of/your/project folder/fto2_nc"

# Column names in the SAP NC dataset (right-hand side). Open the dataset, Columns tab.
SAP_COLUMNS = {
    "notification_number": "notification_number",     # NC number
    "texte": "description_long_text",                 # NC long text (the one with "DEF 1-T02 : ...")
    "date_creation": "creation_time",                 # creation date
    "programme": "programme",                         # A350 / A330 / A400M / A320 ...
    "plant": "plant",                                 # plant where the NC was raised (FTO2 for us)
    "statut": "status_open_closed",                   # open / closed / deleted
    "responsabilite": "liability_description",        # [PLANT] / [SUPPLIER] / [OTHERS]
    "liabilite": "liability",                         # plant(s) liable, e.g. [FTO2] (array in Skywise)
}
OUR_PLANT = "FTO2"

PERIOD_START = "2026-01-01"    # first creation date counted on the dashboard
PERIOD_END = ""                # empty = up to today. Only for the install check: "2026-07-06", then empty again.

# Line shown on the dashboard: the first pattern found in the programme value wins.
LINES = [("A350", r"350"), ("A330", r"330"), ("A400M", r"400|^MT$"), ("A320", r"32\d")]   # A400M is "MT" in Skywise

# RCA names shown on the charts. Left: code from the parser (do not change). Right: the name shown.
RCA_NAMES = {
    "INVERSION_BRANCHEMENT": "Inversion",
    "ERREUR_BRANCHEMENT": "Mauvaise Borne",
    "OUBLI_VERROUILLAGE": "Déverrouillage",
    "NON_CONNECTE": "Non Connecté",
    "MEO_FRETTAGE_COLLIER": "Frettage Incorrect",
    "MEO_SERRAGE": "Serrage Incorrect",
    "MEO_CHEMINEMENT": "Mauvais Cheminement",
    "MEO_GAINAGE": "MEO Gainage",
    "MEO_FINITION": "Finition Inachevée",
    "MEO_SERTISSAGE_STANDARD": "Défaut de Sertissage sur câble standard",
    "MEO_SERTISSAGE_SPECIFIQUE": "Défaut de Sertissage sur câble spécifique",
    "MESURE_NON_CONFORME": "Défaut de Métallisation",
    "ERREUR_REF_HABILLAGE": "Erreur Fixation ou Protection",
    "ERREUR_REF_ELECTRIQUE": "Erreur Composant Électrique",
    "MANQUANT_HABILLAGE": "Fixation ou Protection Manquante",
    "MANQUANT_OBTURATION": "Obturateur Manquant",
    "MANQUANT_CABLE_ELEMENT": "Câble ou Élément Manquant",
    "MANQUANT_IDENTIFICATION": "Identification Manquante",
    "DOMMAGE_CABLE": "Câble Endommagé",
    "DOMMAGE_COMPOSANT": "Composant Endommagé",
    "DOMMAGE_HABILLAGE": "Protection Endommagée",
    "DOMMAGE_STRUCTURE": "Structure Endommagée",
    "MEO_METALLISATION": "Défaut de Métallisation",
    "AMONT_IMPRESSION": "Défaut d'Impression",
    "FOD": "FOD",
    "PROCESS_DOSSIER": "Erreur Dossier",
    "AUTRE": "Autre",
}
# ====================================================================

PARSER_VERSION = "4.8"
GROUP_COLUMNS = {"MEO Câblage": "nb_meo_cablage", "Erreur Branchement": "nb_erreur_branchement",
                 "Élément Manquant": "nb_element_manquant", "Élément Endommagé": "nb_element_endommage",
                 "Déverrouillage": "nb_deverrouillage", "Grounding/Bonding": "nb_grounding_bonding",
                 "Kitting Factory": "nb_kitting_factory", "FOD": "nb_fod", "Autre": "nb_autre"}

NC_TEXT = ["notification_number", "nc_id", "programme", "ligne", "plant", "statut", "responsabilite", "date_creation", "perimetre"]
DEFECT_TEXT = ["code", "fin", "text", "source_format", "groupe", "sous_groupe", "souscat_source", "rca_type", "rca_nom", "rca_mode",
               "type_reporting", "mode_erreur", "categorie", "famille", "sub_code", "confidence", "resolved_by",
               "cable_preuve", "etat_cable", "provenance", "parser_version"]
DEFECT_COLUMNS = NC_TEXT + ["dans_periode", "seq", "qty"] + DEFECT_TEXT + ["mineur", "cdve", "defaut_cable"]
NC_COLUMNS = NC_TEXT + ["dans_periode", "nb_defauts", "nb_mineurs"] + list(GROUP_COLUMNS.values()) + ["groupe_principal", "parser_version"]


def _parser(name):
    return getattr(P, name) if P is not None else globals()[name]


def _ligne(programme):
    p = str(programme or "")
    for name, pat in LINES:
        if re.search(pat, p, re.I):
            return name
    return p.strip() or "Autre"


def _perimetre(statut, plant, resp, liab=None):
    statut, plant, resp = str(statut or "").upper(), str(plant or "").strip().upper(), str(resp or "").upper()
    if "DELET" in statut or "SUPPRIM" in statut:
        return "Supprimée"
    if "SUPPLIER" in resp:
        return "Fournisseur"
    if plant != OUR_PLANT.upper():
        # a customer return only when our plant is in the liability list; "[PLANT]" alone means some plant is liable.
        # NCs fetched by number (MISSING_IDS) can belong to other plants: they go to "Hors périmètre", not counted.
        if OUR_PLANT.upper() not in str(liab if liab is not None else "").upper():
            return "Hors périmètre"
        return "Retour client" if "PLANT" in resp else "Autre"
    return "FTO2"


def nc_fields(sap_nc: pd.DataFrame) -> pd.DataFrame:
    """One row per NC with the NC fields the dashboard needs (and the long text)."""
    nc = pd.DataFrame({ours: (sap_nc[theirs] if theirs in sap_nc.columns else "") for ours, theirs in SAP_COLUMNS.items()})
    nc["notification_number"] = nc["notification_number"].astype(str).str.strip()
    nc = nc.drop_duplicates("notification_number").reset_index(drop=True)
    nc["texte"] = nc["texte"].fillna("").astype(str)
    nc["nc_id"] = nc["notification_number"].str.lstrip("0")
    dt = pd.to_datetime(nc["date_creation"], errors="coerce", utc=True)
    nc["date_creation"] = dt.dt.strftime("%Y-%m-%d").fillna("")
    keep = dt.dt.strftime("%Y-%m-%d") >= PERIOD_START
    if PERIOD_END:
        keep &= dt.dt.strftime("%Y-%m-%d") <= PERIOD_END
    nc["dans_periode"] = keep.fillna(False).astype(bool)
    nc["ligne"] = nc["programme"].map(_ligne)
    nc["perimetre"] = [_perimetre(s, p, r, l) for s, p, r, l in zip(nc["statut"], nc["plant"], nc["responsabilite"], nc["liabilite"])]
    for c in NC_TEXT:
        nc[c] = nc[c].fillna("").astype(str)
    return nc


def _types(df, text_cols, int_cols, bool_cols):
    for c in text_cols:
        df[c] = df[c].fillna("").astype(str) if c in df else ""
    for c in int_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int64") if c in df else 0
    for c in bool_cols:
        df[c] = df[c].fillna(False).astype(bool) if c in df else False
    return df


def build_defects(sap_nc: pd.DataFrame) -> pd.DataFrame:
    """SAP NC rows in, one row per defect out."""
    nc = nc_fields(sap_nc)
    src = nc[["notification_number", "texte"]].rename(columns={"texte": "description_long_text"})
    _, d = _parser("explode_dataframe")(src)
    return finish_defects(d, nc)


def finish_defects(d: pd.DataFrame, nc: pd.DataFrame) -> pd.DataFrame:
    """Parsed defects + NC fields -> the fto2_defects columns, with fixed types."""
    if d.empty:
        return _types(pd.DataFrame(columns=DEFECT_COLUMNS), NC_TEXT + DEFECT_TEXT, ["seq", "qty"],
                      ["dans_periode", "mineur", "cdve", "defaut_cable"])[DEFECT_COLUMNS]
    d = d.copy()
    d["notification_number"] = d["notification_number"].astype(str)
    d = d.drop(columns=[c for c in NC_TEXT + ["dans_periode"] if c in d and c != "notification_number"])
    d = d.merge(nc.drop(columns="texte"), on="notification_number", how="left")
    d["rca_nom"] = d["rca_type"].map(RCA_NAMES).fillna(d["rca_type"])
    d["parser_version"] = PARSER_VERSION
    d = _types(d, NC_TEXT + DEFECT_TEXT, ["seq", "qty"], ["dans_periode", "mineur", "cdve", "defaut_cable"])
    d.loc[d["qty"] < 1, "qty"] = 1
    return d[DEFECT_COLUMNS].reset_index(drop=True)


def build_nc(sap_nc: pd.DataFrame, defects: pd.DataFrame) -> pd.DataFrame:
    """One row per NC: NC fields plus defect counts per Pareto category."""
    nc = nc_fields(sap_nc).drop(columns="texte")
    d = defects.copy()
    d["notification_number"] = d["notification_number"].astype(str)
    g = d.groupby("notification_number")
    counts = pd.DataFrame({"nb_defauts": g.size(), "nb_mineurs": g["mineur"].sum()})
    per = pd.crosstab(d["notification_number"], d["groupe"]) if len(d) else pd.DataFrame()
    for grp, col in GROUP_COLUMNS.items():
        counts[col] = per[grp] if grp in per else 0
    counts["groupe_principal"] = counts[list(GROUP_COLUMNS.values())].idxmax(axis=1).map(
        {v: k for k, v in GROUP_COLUMNS.items()}) if len(counts) else ""
    nc = nc.merge(counts, left_on="notification_number", right_index=True, how="left")
    nc["parser_version"] = PARSER_VERSION
    nc = _types(nc, NC_TEXT + ["groupe_principal", "parser_version"], ["nb_defauts", "nb_mineurs"] + list(GROUP_COLUMNS.values()),
                ["dans_periode"])
    return nc[NC_COLUMNS].reset_index(drop=True)
