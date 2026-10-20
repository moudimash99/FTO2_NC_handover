# -*- coding: utf-8 -*-
"""
FTO2 NC dashboard: from the Skywise NC exports to the dashboard's two tables.

The same file runs in two places:
    - on the laptop: build/build_all.py runs it on the CSV exports of 06_input_data;
    - in Skywise (Level 3): the notebook runs it unchanged on the datasets fto2_dashboard_data and
      fto2_dashboard_data_missing_ids that the pipeline notebook already writes.
The NC selection is the pipeline's: nothing here adds or removes an NC (the scope column only labels them).

    nc_t, def_t, dis_t, info, to_label = fto2_core.build(frames, labels, ref_dir, ops, dis)

frames   the NC exports (standard + missing IDs) as pandas DataFrames, with the pipeline's columns
labels   root-cause labels per defect line (04_reference/llm_labels_longtext.csv; a dataset in Skywise)
ref_dir  folder holding reference_souscodes_pareto.csv and souscodes_fr.csv (04_reference/)

ops      the rework orders' operations (Work_Order_Operation, S03 at FTO2), or None: the model's work times
dis      the MES disruptions (MES Disruptions, plant FTO2), or None: the flat alert time and no disruption block

nc_t     one row per NC, columns NC_COLUMNS          -> dataset fto2_dash_nc
def_t    one row per defect line, columns DEF_COLUMNS -> dataset fto2_dash_defects
dis_t    one row per quality aléa that led to no NC, columns DIS_COLUMNS -> dataset fto2_dash_disruptions

Needs on the import path: fto2_logic.py and nc_defect_parser.py (02_dashboard_pack/.../1_pipeline) and the cnq package
(cnq_handoever/cnq). The dashboard's JavaScript (fto2FromTables) turns the two tables back into the page's data.
"""
import os
import re

import numpy as np
import pandas as pd

import fto2_logic as L

HOME_PLANTS = ("FTO2", "FT02")   # the pipeline's own test for our plant (Type_NC_auto: both spellings)
import nc_defect_parser as PARSER
from cnq.cnq_core import compute_cnq
from cnq.cnq_orders import nc_order_times
from cnq.cnq_disruptions import nc_alea_times
import cnq.cnq_params as CNQP

S_ = lambda v: "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)
CAT_RENAME = {"MEO Câblage": "MEO Facteur humain"}   # the parser's category -> the dashboard's name

# ============================================================ the two tables (the contract with the page and with Slate)
# name, type, meaning. Types: text, int, num (decimal), date (text YYYY-MM-DD). Same names in the datasets, the SQL and the JS.
NC_COLUMNS = [
    ("nc", "text", "NC number"),
    ("created", "date", "creation date"),
    ("line", "text", "aircraft line: A350, A330, A320, A400M, Autre"),
    ("plant", "text", "plant of the NC"),
    ("on_aec", "int", "1 when AEC (FTO2) is in the liability, so the NC is costed"),
    ("rule", "text", "CNQ rule: RWK, REJ, REJ_RW, EXC, SCR, DQN, ..., DELETED"),
    ("decision_label", "text", "CNQ rule label"),
    ("where_found", "text", "where the NC was found (CNQ model)"),
    ("cost_airbus", "num", "CNQ level 1, Airbus standard (EUR)"),
    ("cost_global", "num", "CNQ level 2, average times (EUR)"),
    ("cost_total", "num", "CNQ level 3, per defect (EUR): the dashboard's cost"),
    ("cost_admin", "num", "level 3: alert, writing, support, re-check (EUR)"),
    ("cost_work", "num", "level 3: setup and hands-on work (EUR)"),
    ("cost_material", "num", "level 3: material (EUR)"),
    ("cost_engineering", "num", "level 3: engineering (EUR)"),
    ("cable", "int", "1 when a defect line is a cable defect (root-cause labels)"),
    ("defect_lines", "int", "number of defect lines"),
    ("title", "text", "NC title (80 characters)"),
    ("scope", "text", "serie = plant FTO2 or FT02; client = customer return (Type_NC_auto 'NC Retour client' with FTO2 in the liability); autre = the rest"),
    ("phase", "text", "production type: SERIE, REC, FTI"),
    ("msn", "text", "aircraft MSN"),
    ("product", "text", "product family (Produit_auto)"),
    ("station", "text", "station description"),
    ("hour", "int", "creation hour, Paris time (-1 if unknown)"),
    ("lead_days", "num", "days to close (empty while open)"),
    ("is_open", "int", "1 while the NC is open"),
    ("age_days", "num", "days open at the data date (empty when closed)"),
    ("closed", "date", "closure date (empty while open)"),
    ("type_nc", "text", "NC type: CABLES, TEST, INTERNE, CONTROLE FINAL, NC Interne, FOURNISSEUR, ..."),
    ("liability", "text", "liability"),
    ("sap_defect", "text", "SAP defect code"),
    ("sap_cause_group", "text", "SAP cause group"),
    ("sap_cause", "text", "SAP cause"),
    ("status", "text", "open, closed, deleted"),
    ("source", "text", "sky (Skywise only), gps (also in the GPS register), test (also in the Test list)"),
    ("min_alert", "num", "CNQ minutes: alert"),
    ("min_writing", "num", "CNQ minutes: writing the NC"),
    ("min_support", "num", "CNQ minutes: technical support"),
    ("min_setup", "num", "CNQ minutes: around the job"),
    ("min_hands_on", "num", "CNQ minutes: hands-on work"),
    ("min_recheck", "num", "CNQ minutes: re-check and closing"),
    ("hours_engineering", "num", "CNQ engineering hours"),
    ("final_inspection", "int", "1 when found at final inspection"),
    ("long_text", "text", "NC long text, customer returns only (2,500 characters)"),
    ("work_source", "text", "where the setup and hands-on minutes come from: order (planned time of the rework orders), model, or empty (no work)"),
    ("order_state", "text", "rework orders: used, open (not closed yet), no_time, not_found (not in the operations), empty (no link or no operations)"),
    ("rework_orders", "text", "rework order numbers (S03) linked to the NC, space-separated"),
    ("alert_source", "text", "alert step: alea (declared time of the quality aléas that led to the NC), flat (the model's time), empty (not charged)"),
    ("aleas", "text", "quality aléas (MES disruptions) that led to the NC, space-separated"),
    ("origin", "text", "pipeline output the NC comes from: normal (fto2_dashboard_data) or missing_ids (fto2_dashboard_data_missing_ids)"),
]
DEF_COLUMNS = [
    ("nc", "text", "NC number"),
    ("seq", "int", "defect line number in the NC"),
    ("cat", "text", "category (root-cause labels)"),
    ("rca", "text", "root cause"),
    ("sub", "text", "sub-category"),
    ("minor", "int", "1 for a minor defect (tie-wrap, cap, ...)"),
    ("cable", "int", "1 for a cable defect"),
    ("cost_alloc", "num", "the NC's level-3 cost shared on this line (EUR)"),
    ("qty", "int", "quantity written on the line"),
    ("text", "text", "defect text (220 characters)"),
    ("subcode", "text", "official sub-code"),
    ("fin", "text", "FIN read by the parser"),
    ("label_src", "text", "ai (stored root-cause label) or parser (no label yet)"),
    ("ai_conf", "text", "confidence of the stored label: high, medium, low"),
    ("cr_nature", "text", "customer returns: damage type (phys, hs, nc, recu)"),
    ("cr_detection", "text", "customer returns: moment of detection"),
    ("cr_symptom", "text", "customer returns: observed symptom"),
]
DIS_COLUMNS = [
    ("id", "text", "aléa (MES disruption) number"),
    ("opened", "date", "day the aléa opened, Paris time"),
    ("line", "text", "aircraft line, from the aléa's programme: A350, A330, A320, Autre"),
    ("station", "text", "physical station"),
    ("work_order", "text", "work order of the aléa"),
    ("minutes", "num", "time lost, typed by the operator (minutes)"),
    ("in_block", "int", "1 when counted in the disruption block; 0 for the possible ERMA aléas (MIP / 1101VB), out until checked"),
    ("reason", "text", "why out of the block: erma, or empty"),
    ("status", "text", "status of the aléa in MES"),
    ("comment", "text", "what the operator wrote (200 characters)"),
]


# ============================================================ 1. exports -> one row per NC
def as_export(x):
    """A dataset read in Skywise, put in the form of the CSV exports the build was written and tested on: list columns as
    '[a, b]', timestamps as ISO text ending in Z, and empty text as missing, as a CSV read gives it (the pipeline writes its
    empty GPS / Test columns as ''; read as a value, '' would be taken for a GPS NC type)."""
    x = x.copy()
    for c in x.columns:
        s = x[c]
        if pd.api.types.is_datetime64_any_dtype(s):
            t = pd.to_datetime(s, utc=True)
            x[c] = t.dt.strftime("%Y-%m-%dT%H:%M:%SZ").where(t.notna(), None)
        elif s.dtype == object:
            seq = s.map(lambda v: isinstance(v, (list, tuple, np.ndarray)))
            if seq.any():
                x[c] = [("[" + ", ".join(str(e) for e in v) + "]") if f else v for v, f in zip(s, seq)]
            ts = s.map(lambda v: isinstance(v, (pd.Timestamp, np.datetime64)) or hasattr(v, "isoformat") and not isinstance(v, str))
            if ts.any():
                t = pd.to_datetime(s.where(ts), utc=True, errors="coerce")
                x[c] = np.where(ts, t.dt.strftime("%Y-%m-%dT%H:%M:%SZ"), x[c])
        if x[c].dtype == object or pd.api.types.is_string_dtype(x[c]):   # object (pandas 1-2) or str (pandas 3)
            blank = x[c].map(lambda v: isinstance(v, str) and not v.strip())
            if blank.any():
                x[c] = x[c].where(~blank, None)
    return x


def merge_exports(frames):
    """The NC exports (standard + missing IDs) merged; when an NC is in several, the most recently changed row wins. _origin says
    which pipeline output the NC comes from: missing_ids when its export's name (_source) holds "missing", else normal; an NC in both
    outputs is normal (the pipeline's standard selection has it)."""
    out = []
    for i, x in enumerate(frames):
        x = as_export(x)
        if "_source" not in x.columns:
            x["_source"] = "export_%d" % (i + 1)
        out.append(x)
    x = pd.concat(out, ignore_index=True)
    x["notification_number"] = x["notification_number"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    normal = set(x.loc[~x["_source"].astype(str).str.contains("missing", case=False), "notification_number"])
    x["_origin"] = np.where(x["notification_number"].isin(normal), "normal", "missing_ids")
    x["_changed"] = pd.to_datetime(x["changed_time"], errors="coerce", utc=True)
    x = x.sort_values("_changed").drop_duplicates("notification_number", keep="last").reset_index(drop=True)
    created = pd.to_datetime(x["creation_time"], errors="coerce", utc=True)
    info = {"nc_rows": int(len(x)), "created_from": str(created.min().date()), "created_to": str(created.max().date())}
    return x, info


def clean_long_text(t):
    t = str(t or "")
    t = re.sub(r"(?:--\s*){3,}", "", t)
    t = re.sub(r"Tél\.\s*[^\n]*", "", t)
    t = re.sub(r"#(UID|TEL|PRS)~", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\*?\s*\n", "\n", t)
    return t.strip()


def week_of(iso):
    d = pd.Timestamp(iso)
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


# ============================================================ 2. official sub-code of each defect line
def official_subcode(d, ref_dir):
    """Official sub-code of each defect line: the one chosen by the long-text labelling; for the approved exceptions,
    which have no sub-code of their own, the parent code (E1 = part of Q06-001; E2 = a Q11 component code).
    Returns the codes, the code descriptions [en, fr] (every code the page can meet) and counts."""
    ref = pd.read_csv(os.path.join(ref_dir, "reference_souscodes_pareto.csv"), encoding="utf-8-sig")
    ref = ref[~ref.sous_code.astype(str).str.startswith("(")]
    fr = pd.read_csv(os.path.join(ref_dir, "souscodes_fr.csv"), encoding="utf-8-sig").set_index("sous_code").description_fr
    missing = sorted(set(ref.sous_code) - set(fr.index))
    assert not missing, "French description missing in souscodes_fr.csv for: %s" % missing
    desc = {c: [en, fr[c]] for c, en in zip(ref.sous_code, ref.object_desc)}
    first = ref.groupby("sous_categorie").sous_code.first()
    fallback = {"Câble à refaire (ligne)": "Q06-001", "Composant HS": "Q11 (composant)", "Composant – cause non écrite": "Q11 (composant)",
                "Non classé": "Non codé"}
    desc.update({"Q11 (composant)": ["Component (sub-code not specified)", "Composant (sous-code non précisé)"], "Non codé": ["No code", "Sans code"]})
    for c in first:   # the parent codes, so the description list holds every code whatever the data
        desc.setdefault(c[:3] + " (non précisé)", ["Sub-code not specified", "Sous-code non précisé"])
    out = []
    for code, sub, status in zip(d.llm_sous_code.fillna("").astype(str).str.strip(), d.llm_sous_categorie, d.llm_status):
        if status == "ok" and code in desc:
            out.append(code)
        elif sub in fallback:
            out.append(fallback[sub])
        elif sub in first.index:
            out.append(first[sub][:3] + " (non précisé)")
        else:
            out.append("Non codé")
    s = pd.Series(out, index=d.index)
    return s, desc, {"exact": int(s.isin(ref.sous_code).sum()), "parent_or_none": int((~s.isin(ref.sous_code)).sum())}


# ============================================================ 3. parser, labels, CNQ
def prepare(x, lab, ref_dir, ops=None, dis=None, say=None):
    """Steps 1-3 of the build: parser v4.8, the stored root-cause labels, the CNQ model for both classifications, the report
    scope. ops: the rework orders' operations (SAP order type S03), or None; an NC whose rework orders are closed and planned
    gets their planned time instead of the model's setup and hands-on. dis: the MES disruptions, or None; an NC that a quality
    aléa led to gets that aléa's declared time for the alert step. Returns a dict: d (one row per defect), nc (one row per NC),
    lt (long texts), nc_in (the model's NC input), dis (the quality aléas with no NC), codes (sub-code descriptions) and report.
    say: optional progress printer (the Skywise notebook passes its step())."""
    say = say or (lambda msg: None)
    report = {}
    say("   parser v4.8 on %d NCs..." % len(x))
    defects = L.build_defects(x)
    nc = L.build_nc(x, defects)
    # the parser pack's own perimetre label is not used by the dashboard (20 Oct): only the pipeline's columns decide
    defects = defects.drop(columns=["perimetre"], errors="ignore")
    nc = nc.drop(columns=["perimetre"], errors="ignore")
    defects["notification_number"] = defects["notification_number"].astype(str)
    report["parser"] = {"defect_lines": int(len(defects)), "ncs": int(defects.notification_number.nunique())}

    say("   %d defect lines" % len(defects))
    # NC fields from the export that the parser datasets do not carry
    keep = {"decision_status": "decision_status", "decision_status_description_en": "decision_label", "liability": "liability",
            "liability_description": "liability_description", "responsible_defect_level1": "responsible_level1",
            "responsible_defect_level1_name": "responsible_level1_name", "station": "station", "station_description": "station_description",
            "work_ctr": "work_ctr", "user_department": "user_department", "description_short": "description_short",
            "msn": "msn", "trigger": "trigger", "notification_type": "notification_type", "closure_time": "closure_time",
            "Type_NC_auto": "type_nc_auto", "GPS_Type_NC": "gps_type_nc", "Programme_auto": "phase", "Produit_auto": "produit",
            "Origin_auto": "origin_auto", "Ext_Source": "ext_source", "defect_code_description_en": "sap_defect_code",
            "cause_group_description_en": "sap_cause_group", "cause_code_description_en": "sap_cause_code", "creation_time": "creation_ts", "_source": "source_file",
            "linked_document": "linked_document", "work_order": "work_order",   # the CNQ model's rejection-with-rework-order rule reads these two
            "_origin": "origin"}
    for c in keep:   # a column the export lacks stays empty rather than failing
        if c not in x.columns:
            x[c] = None
    ex = x[["notification_number"] + list(keep)].rename(columns=keep)
    ex["type_nc"] = ex["gps_type_nc"].where(ex["gps_type_nc"].notna(), ex["type_nc_auto"])
    nc = nc.merge(ex, on="notification_number", how="left")
    lt = dict(zip(x.notification_number, x.description_long_text.map(clean_long_text)))
    say("   rework orders...")
    # rework orders: the links, and with the operations their state and planned minutes (cnq/cnq_orders.py)
    ot = nc_order_times(nc, ops)
    nc = nc.merge(ot, on="notification_number", how="left")
    nc["rework_orders"] = nc["rework_orders"].fillna("")
    nc["order_state"] = nc["order_state"].fillna("")
    report["rework_orders"] = {"ncs_with_link": int((nc.rework_orders != "").sum()),
                               "operations": int(len(ops)) if ops is not None else 0,
                               "state": nc.loc[nc.rework_orders != "", "order_state"].value_counts().to_dict()}
    say("   aléas...")
    # MES aléas: the declared time of the quality aléas that led to each NC, and those that led to none (cnq/cnq_disruptions.py)
    block = None
    if dis is not None:
        at, block = nc_alea_times(nc[["notification_number", "work_order", "creation_ts"]].rename(columns={"creation_ts": "creation_time"}), dis)
        nc = nc.merge(at, on="notification_number", how="left")
        report["aleas"] = {"rows": int(len(dis)), "ncs_with_alea": int(len(at)), "quality_without_nc": int(len(block)),
                           "block": int(block.in_block.sum()), "block_hours": round(float(pd.to_numeric(block.loc[block.in_block, "time_lost"], errors="coerce").sum()) / 60, 1)}
    else:
        nc["aleas"], nc["alea_minutes"] = None, np.nan
    nc["aleas"] = nc["aleas"].fillna("")

    say("   root-cause labels...")
    # long-text labels; a line whose text changed or that is new is marked "to label" and keeps the parser label
    lab = lab.copy()
    lab["notification_number"] = lab["notification_number"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    lab["seq"] = pd.to_numeric(lab["seq"], errors="coerce").astype("Int64")
    defects["seq"] = pd.to_numeric(defects["seq"], errors="coerce").astype("Int64")
    d = defects.merge(lab, on=["notification_number", "seq"], how="left")
    d["seq"] = d["seq"].astype(int)
    norm = lambda s: s.fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    same_text = (norm(d["text"]) == norm(d["snippet"])) | (norm(d["text"]).isin(["", "N/A"]) & (norm(d["snippet"]) == ""))
    d["llm_status"] = np.where(d["llm_sous_categorie"].isna(), "a_labelliser", np.where(same_text, "ok", "texte_change"))
    use = d["llm_status"] == "ok"
    for c_llm, c_par in (("llm_sous_categorie", "sous_groupe"), ("llm_defaut_cable", "defaut_cable")):
        d[c_llm] = d[c_llm].where(use, d[c_par])
    d["llm_defaut_cable"] = d["llm_defaut_cable"].astype(str).str.lower().isin(["true", "1"])
    d["llm_categorie"] = d["llm_sous_categorie"].map(lambda s: PARSER.SOUS_CATEGORIES.get(s, ("Autre",))[0])
    for c in ("llm_categorie", "groupe"):   # the dashboard's names for the parser's categories (decided 20 Oct)
        if c in d.columns:
            d[c] = d[c].replace(CAT_RENAME)
    d["llm_rca_type"] = d["llm_sous_categorie"].map(lambda s: PARSER.SOUS_CATEGORIES.get(s, (None, "AUTRE"))[1])
    d["llm_rca_nom"] = d["llm_rca_type"].map(L.RCA_NAMES).fillna("Non classé")
    d["llm_mineur"] = d["llm_sous_categorie"].map(PARSER.est_mineur)
    d["sous_code_officiel"], codes, report["subcodes"] = official_subcode(d, ref_dir)
    d = d.drop(columns=["snippet"])
    report["labels"] = d["llm_status"].value_counts().to_dict()

    say("   cost model (both classifications)...")
    # CNQ, both classifications
    # customer return: the pipeline's own NC type (Type_NC_auto "NC Retour client" = plant not FTO2 / FT02) with FTO2 in the
    # liability list. The cost model and the customer-returns tab use it; the plant switch reads the plant column itself.
    ours = nc["liability"].fillna("").astype(str).str.upper().str.contains(L.OUR_PLANT.upper(), regex=False)
    nc["customer_return"] = ((nc["type_nc_auto"].fillna("").astype(str).str.strip() == "NC Retour client") & ours).astype(int)
    nc_in = nc[["notification_number", "statut", "decision_status", "liability", "date_creation", "type_nc", "produit",
                "responsabilite", "customer_return", "programme", "plant", "linked_document", "work_order",
                "rework_orders", "order_state", "order_minutes_setup", "order_minutes_work", "aleas", "alea_minutes"]].copy()
    runs = {}
    for key, sub, cab in (("parser", "sous_groupe", "defaut_cable"), ("llm", "llm_sous_categorie", "llm_defaut_cable")):
        dd = d[["notification_number", "seq", "qty", sub, cab]].rename(columns={sub: "sous_groupe", cab: "cable"})
        n_out, d_out = compute_cnq(nc_in, dd)
        # share each NC's cost among its defect lines: the line's own work and material + an equal part of the rest
        a = n_out.set_index("notification_number")
        lines = d_out.groupby("notification_number")["seq"].transform("size")
        direct_sum = d_out.groupby("notification_number")["cnq_cost_direct"].transform("sum")
        nc_cost = d_out["notification_number"].map(a["cnq_cost_total"]) * d_out["cnq_on_aec"]
        d_out["cnq_cost_allocated"] = d_out["cnq_cost_direct"] + (nc_cost - direct_sum * d_out["cnq_on_aec"]) / lines
        runs[key] = (n_out, d_out)
    np_, dp_ = runs["parser"]
    nl_, dl_ = runs["llm"]          # root-cause labels: the main figures
    report["unknown_cnq_classes"] = sorted(set(d.sous_groupe) - set(CNQP.DEFECT_TIMES))

    dp_i = dp_.set_index(["notification_number", "seq"])
    dl_i = dl_.set_index(["notification_number", "seq"])
    k = list(zip(d.notification_number, d.seq))
    d["cnq_cost_direct"] = [dp_i.at[i, "cnq_cost_direct"] for i in k]
    d["cnq_cost_allocated"] = [dp_i.at[i, "cnq_cost_allocated"] for i in k]
    d["cnq_cost_direct_llm"] = [dl_i.at[i, "cnq_cost_direct"] for i in k]
    d["cnq_cost_allocated_llm"] = [dl_i.at[i, "cnq_cost_allocated"] for i in k]
    d["nb_defauts_nc"] = d.groupby("notification_number")["seq"].transform("size")
    d["semaine"] = d["date_creation"].map(lambda s: week_of(s) if s else "")
    cnq_cols = [c for c in np_.columns if c.startswith("cnq_")]
    nc_ref = nc.merge(nl_[["notification_number"] + cnq_cols], on="notification_number", how="left")
    pc = np_.set_index("notification_number")
    for c in ("cnq_cost_total", "cnq_cost_work", "cnq_cost_material", "cnq_cost_global"):
        nc_ref[c + "_parser"] = nc_ref.notification_number.map(pc[c])
    nc_ref["nc_cable"] = nc_ref.notification_number.isin(set(d[d.defaut_cable].notification_number))
    nc_ref["nc_cable_llm"] = nc_ref.notification_number.isin(set(d[d.llm_defaut_cable].notification_number))
    nc_ref["long_text"] = nc_ref.notification_number.map(lt)
    # where the NC was raised, only from the pipeline's columns. Every NC of the pipeline's selection counts (deleted, supplier
    # and not-liable ones included, decided 20 Oct); the cost is FTO2's only where FTO2 is liable.
    #   serie  = plant FTO2 or FT02 (the pipeline's own plant test, Type_NC_auto)
    #   client = customer return (customer_return above)
    #   autre  = the rest: raised at another plant, not a customer return
    home = nc_ref["plant"].fillna("").astype(str).str.strip().str.upper().isin(HOME_PLANTS)
    nc_ref["scope"] = np.select([nc_ref.customer_return == 1, home], ["client", "serie"], default="autre")
    d["scope"] = d.notification_number.map(nc_ref.set_index("notification_number")["scope"]).fillna("")
    d["phase"] = d.notification_number.map(nc_ref.set_index("notification_number")["phase"]).fillna("")
    return {"d": d, "nc": nc_ref, "lt": lt, "nc_in": nc_in, "nc_parser": np_, "nc_llm": nl_, "def_llm": dl_, "dis": block, "codes": codes, "report": report}


# ============================================================ 4. the page's NC fields and customer-return fields
def nc_extras(r, created_to):
    """NC fields for the aircraft, product, lead-time, time-of-day and NC charts: [msn, product family, station, creation hour (Paris),
    days to close (None while open), open, age in days if open, closure date, NC type, liability, SAP defect code, SAP cause group,
    SAP cause, status, data source, CNQ steps]. CNQ steps = the model's minutes [alert, writing, support, setup, hands-on, re-check],
    engineering hours, the final-inspection flag, then where the work minutes come from (order / model), the rework orders' state and
    numbers, where the alert time comes from (alea / flat) and the aléas, for the "explain the calculation" part; then the pipeline
    output the NC comes from (normal / missing_ids). SAP labels lose their brackets. Data source: every NC comes from Skywise; Ext_Source says whether it
    is also in a manual list (gps = GPS register, test = Test list) or only in Skywise (sky)."""
    msn = S_(r.msn)
    msn = msn[:-2] if msn.endswith(".0") else msn
    created = pd.to_datetime(r.creation_ts, errors="coerce", utc=True)
    closed = pd.to_datetime(r.closure_time, errors="coerce", utc=True)
    hour = int(created.tz_convert("Europe/Paris").hour) if pd.notna(created) else -1
    is_open = int(r.statut == "open")
    lead = round((closed - created).total_seconds() / 86400, 2) if pd.notna(created) and pd.notna(closed) and not is_open else None
    end = pd.Timestamp(created_to + "T23:59:59", tz="UTC")
    age = round((end - created).total_seconds() / 86400, 1) if is_open and pd.notna(created) else None
    sap = lambda v: S_(v).strip().strip("[]").strip()
    return [msn, S_(r.produit) or "Other", S_(r.station_description).strip(), hour, lead, is_open, age,
            closed.strftime("%Y-%m-%d") if pd.notna(closed) else "", S_(r.type_nc).strip(), sap(r.liability), sap(r.sap_defect_code),
            sap(r.sap_cause_group), sap(r.sap_cause_code), S_(r.statut), {"GPS": "gps", "Test": "test"}.get(S_(r.ext_source).strip(), "sky"),
            [round(float(x or 0), 1) for x in (r.cnq_min_alert, r.cnq_min_writing, r.cnq_min_support, r.cnq_min_setup, r.cnq_min_hands_on,
                                                r.cnq_min_recheck, r.cnq_hours_engineering)] + [int(r.cnq_final_inspection or 0)]
            + [S_(r.cnq_work_source), S_(r.order_state), S_(r.rework_orders), S_(r.cnq_alert_source), S_(r.aleas)], S_(r.origin) or "normal"]


def customer_return_extras(d, nc, lt):
    """Customer-return tab: damage type, detection, observed consequence, cause text, plant, liability; and the NC texts."""
    ncd = nc.set_index("notification_number")
    r = d[d.scope == "client"]
    extra, texts = {}, {}
    for x in r.itertuples():
        n = ncd.loc[x.notification_number]
        L_ = lt.get(x.notification_number, "")
        det = re.search(r"Moment of Detection\s*:\s*([^\n]+)", L_)
        det = det.group(1).strip() if det else ""
        nat = ""
        if x.llm_categorie == "Élément Endommagé":
            if re.search(r"unpacking|reception", det, re.I):
                nat = "recu"
            elif x.llm_sous_categorie == "Composant HS":
                nat = "hs"
            elif x.llm_sous_categorie == "Composant – cause non écrite":
                nat = "nc"
            else:
                nat = "phys"
        sym = S_(x.llm_symptome)
        extra["%s|%d" % (x.notification_number, x.seq)] = [nat, det, sym[:1].upper() + sym[1:], "", S_(n.plant), S_(n.liability)]
        texts[x.notification_number] = L_[:2500]
    stats = {"ncs": int((nc.scope == "client").sum()), "defects": int(len(r)),
             "damage_types": pd.Series([v[0] for v in extra.values() if v[0]]).value_counts().to_dict()}
    return extra, texts, stats


# ============================================================ 5. the two tables
def tables(d, nc, lt, created_to):
    """The dashboard's two tables, in the order of NC_COLUMNS and DEF_COLUMNS. NCs without a creation date are left out."""
    extra, _, _ = customer_return_extras(d, nc, lt)
    rows = []
    for r in nc.itertuples():
        if not r.date_creation:
            continue
        e = nc_extras(r, created_to)
        rows.append([r.notification_number, r.date_creation, S_(r.ligne), S_(r.plant), int(r.cnq_on_aec), r.cnq_rule,
                     r.cnq_decision_label, r.cnq_where_found, round(r.cnq_cost_airbus, 2), round(r.cnq_cost_global, 2), round(r.cnq_cost_total, 2),
                     round(r.cnq_cost_admin, 2), round(r.cnq_cost_work, 2), round(r.cnq_cost_material, 2), round(r.cnq_cost_engineering, 2),
                     int(r.nc_cable_llm), int(r.cnq_defect_lines), S_(r.description_short)[:80], r.scope, S_(r.phase)]
                    + e[:15] + e[15][:8] + [(lt.get(r.notification_number, "") or "")[:2500] if r.scope == "client" else ""] + e[15][8:] + [e[16]])
    nc_t = pd.DataFrame(rows, columns=[c[0] for c in NC_COLUMNS])
    rows = []
    for r in d.itertuples():
        ok = r.llm_status == "ok"
        x = extra.get("%s|%d" % (r.notification_number, r.seq), ["", "", ""])
        rows.append([r.notification_number, int(r.seq), r.llm_categorie, r.llm_rca_nom, r.llm_sous_categorie, int(bool(r.llm_mineur)),
                     int(bool(r.llm_defaut_cable)), round(float(r.cnq_cost_allocated_llm), 2), int(r.qty) if pd.notna(r.qty) else 1,
                     S_(r.text)[:220], r.sous_code_officiel, S_(r.fin), "ai" if ok else "parser", S_(r.llm_confiance) if ok else "", x[0], x[1], x[2]])
    def_t = pd.DataFrame(rows, columns=[c[0] for c in DEF_COLUMNS])
    return nc_t, def_t


LINES = {"A350": "A350", "A330": "A330", "A320": "A320", "A400M": "A400M", "MT": "A400M"}


def dis_table(block):
    """The disruption block's table (DIS_COLUMNS): the quality aléas that led to no NC, those counted and the possible ERMA ones."""
    if block is None or not len(block):
        return pd.DataFrame(columns=[c[0] for c in DIS_COLUMNS])
    b = block.sort_values("opened")
    paris = b["opened"].dt.tz_convert("Europe/Paris")
    one = lambda v: " ".join(S_(v).split())[:200]
    return pd.DataFrame({"id": b["disruption_id"].astype(str), "opened": paris.dt.strftime("%Y-%m-%d").fillna(""),
                         "line": b.get("program", pd.Series("", index=b.index)).map(lambda v: LINES.get(S_(v).strip().upper(), "Autre")),
                         "station": b.get("physical_station", pd.Series("", index=b.index)).map(S_),
                         "work_order": b["work_order"].map(S_).str.replace(r"\.0$", "", regex=True),
                         "minutes": pd.to_numeric(b["time_lost"], errors="coerce").fillna(0.0).round(1),
                         "in_block": b["in_block"].astype(int), "reason": b["reason"],
                         "status": b.get("status", pd.Series("", index=b.index)).map(S_), "comment": b.get("comment", pd.Series("", index=b.index)).map(one)})


def build(frames, labels, ref_dir, ops=None, dis=None, say=None):
    """Everything in one call, as the Skywise notebook uses it: (nc_t, def_t, dis_t, info, to_label). ops: rework-order operations or
    None; dis: MES disruptions or None; say: optional progress printer."""
    say = say or (lambda msg: None)
    x, info = merge_exports(frames)
    say("   %d NCs after merging the selections" % len(x))
    p = prepare(x, labels, ref_dir, ops, dis, say)
    say("   building the tables...")
    nc_t, def_t = tables(p["d"], p["nc"], p["lt"], info["created_to"])
    aec = p["nc"][p["nc"].cnq_on_aec == 1]
    info.update(p["report"])
    info.update({"nc_table": int(len(nc_t)), "defect_table": int(len(def_t)), "level3_aec": round(float(aec.cnq_cost_total.sum()), 2),
                 "to_label": int((def_t.label_src == "parser").sum())})
    dis_t = dis_table(p["dis"])
    info.update({"disruption_table": int(len(dis_t)), "origin": nc_t.origin.value_counts().to_dict()})
    return nc_t, def_t, dis_t, info, lines_to_label(p["d"], p["lt"])


def lines_to_label(d, lt):
    """Defect lines without a usable stored label (new, or text changed since it was labelled), for the periodic AI pass.
    snippet is the line's full text: a label is used only while the line's text stays the same as its snippet."""
    t = d[d.llm_status != "ok"]
    out = pd.DataFrame({"notification_number": t.notification_number, "seq": t.seq, "snippet": t.text.fillna(""),
                        "parser_sous_categorie": t.sous_groupe, "ligne": t.ligne, "date_creation": t.date_creation,
                        "long_text": t.notification_number.map(lambda n: (lt.get(n, "") or "")[:4000])})
    return out.reset_index(drop=True)


# ============================================================ 7. a past year (2025): the pipeline's rules on a raw extract
# The 2026 exports come out of the pipeline notebook with its selection and its *_auto columns. The 2025 extract is the raw Skywise
# NC table (plant FTO2, Jan 2025 to Jan 2026), so it goes through the same rules here, copied from 06_input_data/pipeline_notebook.py
# (STANDARD mode). Keep them in step with the notebook. The notebook's head(1000) is left out: it trims the dashboard's export, not a year.
STATUT_MAP = {"RWK": "Rework", "REJ": "Reject", "EXC": "Echange", "NDC": "DQN", "SCR": "Scrap",
              "ACC": "Accept as is i.a.w design criteria", "PNC": "Potential Non Conformity", "DQN": "Request for Design Change"}


def pipeline_rules(raw, station_desc):
    """The notebook's selection and *_auto columns on a raw extract. station_desc: {station: description} (the notebook reads
    data/fto2_station_mapping.csv; on the laptop the pairs come from the 2026 exports)."""
    df = raw.copy()
    for c in ("decision_status", "workflow_list", "article_version_description", "user_department"):
        df[c] = df[c].fillna("")
    df = df[~df["user_department"].str.contains("ERMA", case=False)].copy()                       # ERMA out
    deleted = df["status_open_closed"].fillna("").str.contains("Deleted", case=False)
    df = df[~(deleted & (df["plant"] != "FTO2"))].copy()                                           # deleted NCs of other plants out
    df["station_description"] = df["station"].map(station_desc)
    wf = df["workflow_list"].fillna("")
    df["Programme_auto"] = "SERIE"
    df.loc[wf.str.contains(r"\bREC\b|-CRE|-PNC|A30-REJ-PVU2", case=False, regex=True), "Programme_auto"] = "REC"
    df.loc[df["constituent_assembly"].fillna("").str.upper().str.startswith(("WY", "WA")), "Programme_auto"] = "FTI"
    df["Statut_decision_auto"] = df["decision_status"].map(STATUT_MAP).fillna("Unknown")
    df["Origin_auto"] = np.where(df["user_department"].str.strip().str.upper() == "OLMEP14/AIRBUS OPERATIONS SAS", "Test", "Qualite")
    # NC type, in the notebook's priority order
    is_rew = wf.str.startswith("REW-LIGNE")
    deri = df["user_department"].str.contains("DERICHEBOURG", case=False)
    dsh, art = df["description_short"].fillna(""), df["article_version_description"].fillna("")
    label = dsh.str.contains(r"etiquette|plaquette", flags=re.I) | art.str.contains(r"etiquette|plaquette", flags=re.I)
    cable_word = dsh.str.contains(r"c[aâ]ble|harnais|wire", flags=re.I) | art.str.contains(r"c[aâ]ble|harnais|wire", flags=re.I)
    cables = (wf.str.contains(r"^R[E]?W-CA-IMP", flags=re.I) & ~label) | (cable_word & wf.str.startswith("REW-MP-IMP"))
    conds = [df["status_open_closed"].fillna("").str.contains("Deleted", case=False) & (df["plant"] == "FTO2"),
             df["Origin_auto"] == "Test",
             ~df["plant"].fillna("").isin(["FTO2", "FT02"]),
             (df["liability_description"].fillna("") == "[SUPPLIER]") | (df["responsible_defect_level1"].fillna("") == "Y4"),
             cables,
             wf.str.startswith("REJ-LO-BP") | (is_rew & deri),
             wf.str.startswith("LIGNE-F-DQN"),
             is_rew & ~deri,
             wf.str.contains("TEST", case=False)]
    df["Type_NC_auto"] = np.select(conds, ["QUALITE", "TEST", "NC Retour client", "NC Fournisseur", "CABLES", "NC Interne",
                                           "DEMANDE DE DQN", "CONTROLE FINAL", "CONTROLE FINAL"], default="NC Interne")
    # product: the article first, the station as a fallback
    desc = df["article_version_description"].fillna("") + " | " + df["station_description"].fillna("")
    a400 = df["programme"].fillna("").isin(["MT", "A400M"])
    mip = desc.str.contains("MIP|1101VB|1212VB|2200VB", case=False, regex=True)
    vbvu = desc.str.extract(r"(\d{3,4}V[UB])", expand=False, flags=re.I)
    conds = [desc.str.contains("4714VB|4715VB|4716VB|4717VB|E-RUDDER", case=False, regex=True),
             desc.str.contains("5883VB|5893VB|MDCD", case=False, regex=True),
             desc.str.contains("OHP", case=False, regex=False),
             desc.str.contains("30[0-5]VU|M8753254100000", case=False, regex=True),
             desc.str.contains("WIRE BUNDLE|MFRL", case=False, regex=True),
             desc.str.contains("ELEC ASSY", case=False, regex=False),
             mip & a400, mip & ~a400, vbvu.notna()]
    df["Produit_auto"] = np.select(conds, ["E-RUDDER", "MDCD", "OHP", "300VU", "MFRL", "PTVU", "MIP A400M", "MIP A350", vbvu], default="Other")
    return df.reset_index(drop=True)


def station_pairs(frames):
    """{station: description} from exports that went through the pipeline (the notebook's station mapping, as it was applied)."""
    s = pd.concat([f[["station", "station_description"]] for f in frames if "station_description" in f.columns], ignore_index=True)
    s = s.dropna().astype(str)
    s = s[s.station.str.strip() != ""]
    return dict(s.drop_duplicates("station").values)


def year_baseline(raw, station_desc, ref_dir, year):
    """One year of NCs through the pipeline's rules, the parser and the CNQ model (no stored labels: parser classes), summed per
    month, report scope, phase, line and product: [month, scope, phase, line, product, NCs, defect lines, major defect lines,
    level-3 cost, level-2, level-1]. The work minutes are the model's (no rework-order operations for that year).
    Same scope rule as the dashboard (serie = plant FTO2 or FT02; client = customer return)."""
    x, _ = merge_exports([pipeline_rules(raw, station_desc)])
    empty = pd.DataFrame(columns=["notification_number", "seq", "snippet", "llm_sous_categorie", "llm_sous_code", "llm_defaut_cable", "llm_confiance", "llm_symptome"])
    p = prepare(x, empty, ref_dir)
    nc, d = p["nc"], p["d"]
    nc = nc[nc.date_creation.str.startswith(str(year))].copy()
    for c in ("cnq_cost_total", "cnq_cost_global", "cnq_cost_airbus"):   # FTO2's cost: only where FTO2 is liable
        nc[c] = nc[c] * nc["cnq_on_aec"]
    maj = d[~d.llm_mineur.astype(bool)].groupby("notification_number").size()
    nc["major"] = nc.notification_number.map(maj).fillna(0).astype(int)
    nc["month"] = nc.date_creation.str[:7]
    nc["prod"] = nc.produit.fillna("").astype(str).replace("", "Other")
    g = nc.groupby(["month", "scope", "phase", "ligne", "prod"], dropna=False).agg(
        n=("notification_number", "size"), d=("cnq_defect_lines", "sum"), dm=("major", "sum"),
        c3=("cnq_cost_total", "sum"), c2=("cnq_cost_global", "sum"), c1=("cnq_cost_airbus", "sum")).reset_index()
    rows = [[r.month, r.scope, S_(r.phase), S_(r.ligne), r.prod, int(r.n), int(r.d), int(r.dm), round(float(r.c3), 2), round(float(r.c2), 2), round(float(r.c1), 2)]
            for r in g.itertuples()]
    aec = nc[nc.cnq_on_aec == 1]
    info = {"ncs": int(len(nc)), "serie": int((nc.scope == "serie").sum()), "client": int((nc.scope == "client").sum()), "autre": int((nc.scope == "autre").sum()),
            "level3_aec": round(float(aec.cnq_cost_total.sum()), 2), "created_from": nc.date_creation.min(), "created_to": nc.date_creation.max()}
    return rows, info, p
