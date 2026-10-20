# -*- coding: utf-8 -*-
"""
FTO2 NC dashboard: from the Skywise NC exports to the dashboard's two tables.

The same file runs in two places:
    - on the laptop: build/build_all.py runs it on the CSV exports of 06_input_data;
    - in Skywise (Level 3): the notebook runs it unchanged on the datasets fto2_dashboard_data and
      fto2_dashboard_data_missing_ids that the pipeline notebook already writes.
The NC selection is the pipeline's: nothing here adds or removes an NC (the scope columns only label them).

    nc_t, def_t, info, to_label = fto2_core.build(frames, labels, ref_dir)

frames   the NC exports (standard + missing IDs) as pandas DataFrames, with the pipeline's columns
labels   root-cause labels per defect line (04_reference/llm_labels_longtext.csv; a dataset in Skywise)
ref_dir  folder holding reference_souscodes_pareto.csv and souscodes_fr.csv (04_reference/)

nc_t     one row per NC, columns NC_COLUMNS          -> dataset fto2_dash_nc
def_t    one row per defect line, columns DEF_COLUMNS -> dataset fto2_dash_defects

Needs on the import path: fto2_logic.py and nc_defect_parser.py (02_dashboard_pack/.../1_pipeline) and the cnq package
(cnq_handoever/cnq). The dashboard's JavaScript (fto2FromTables) turns the two tables back into the page's data.
"""
import os
import re

import numpy as np
import pandas as pd

import fto2_logic as L
import nc_defect_parser as PARSER
from cnq.cnq_core import compute_cnq
import cnq.cnq_params as CNQP

S_ = lambda v: "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)

# ============================================================ the two tables (the contract with the page and with Slate)
# name, type, meaning. Types: text, int, num (decimal), date (text YYYY-MM-DD). Same names in the datasets, the SQL and the JS.
NC_COLUMNS = [
    ("nc", "text", "NC number"),
    ("created", "date", "creation date"),
    ("line", "text", "aircraft line: A350, A330, A320, A400M, Autre"),
    ("plant_scope", "text", "perimetre: FTO2, Retour client, Fournisseur, Supprimée, Hors périmètre"),
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
    ("scope", "text", "report scope: serie, client, or empty (outside the report)"),
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


# ============================================================ 1. exports -> one row per NC
def as_export(x):
    """A dataset read in Skywise, put in the form of the CSV exports the build was written and tested on: list columns as
    '[a, b]', timestamps as ISO text ending in Z. Text columns are left as they are."""
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
    return x


def merge_exports(frames):
    """The NC exports (standard + missing IDs) merged; when an NC is in several, the most recently changed row wins."""
    out = []
    for i, x in enumerate(frames):
        x = as_export(x)
        if "_source" not in x.columns:
            x["_source"] = "export_%d" % (i + 1)
        out.append(x)
    x = pd.concat(out, ignore_index=True)
    x["notification_number"] = x["notification_number"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
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
def prepare(x, lab, ref_dir):
    """Steps 1-3 of the build: parser v4.8, the stored root-cause labels, the CNQ model for both classifications, the report
    scope. Returns a dict: d (one row per defect), nc (one row per NC), lt (long texts), nc_in (the model's NC input),
    codes (sub-code descriptions) and report (counts)."""
    report = {}
    defects = L.build_defects(x)
    nc = L.build_nc(x, defects)
    defects["notification_number"] = defects["notification_number"].astype(str)
    report["parser"] = {"defect_lines": int(len(defects)), "ncs": int(defects.notification_number.nunique())}

    # NC fields from the export that the parser datasets do not carry
    keep = {"decision_status": "decision_status", "decision_status_description_en": "decision_label", "liability": "liability",
            "liability_description": "liability_description", "responsible_defect_level1": "responsible_level1",
            "responsible_defect_level1_name": "responsible_level1_name", "station": "station", "station_description": "station_description",
            "work_ctr": "work_ctr", "user_department": "user_department", "description_short": "description_short",
            "msn": "msn", "trigger": "trigger", "notification_type": "notification_type", "closure_time": "closure_time",
            "Type_NC_auto": "type_nc_auto", "GPS_Type_NC": "gps_type_nc", "Programme_auto": "phase", "Produit_auto": "produit",
            "Origin_auto": "origin_auto", "Ext_Source": "ext_source", "defect_code_description_en": "sap_defect_code",
            "cause_group_description_en": "sap_cause_group", "cause_code_description_en": "sap_cause_code", "creation_time": "creation_ts", "_source": "source_file",
            "linked_document": "linked_document", "work_order": "work_order"}   # the CNQ model's rejection-with-rework-order rule reads these two
    for c in keep:   # a column the export lacks stays empty rather than failing
        if c not in x.columns:
            x[c] = None
    ex = x[["notification_number"] + list(keep)].rename(columns=keep)
    ex["type_nc"] = ex["gps_type_nc"].where(ex["gps_type_nc"].notna(), ex["type_nc_auto"])
    nc = nc.merge(ex, on="notification_number", how="left")
    lt = dict(zip(x.notification_number, x.description_long_text.map(clean_long_text)))

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
    d["llm_rca_type"] = d["llm_sous_categorie"].map(lambda s: PARSER.SOUS_CATEGORIES.get(s, (None, "AUTRE"))[1])
    d["llm_rca_nom"] = d["llm_rca_type"].map(L.RCA_NAMES).fillna("Non classé")
    d["llm_mineur"] = d["llm_sous_categorie"].map(PARSER.est_mineur)
    d["sous_code_officiel"], codes, report["subcodes"] = official_subcode(d, ref_dir)
    d = d.drop(columns=["snippet"])
    report["labels"] = d["llm_status"].value_counts().to_dict()

    # CNQ, both classifications
    nc_in = nc[["notification_number", "statut", "decision_status", "liability", "date_creation", "type_nc", "produit",
                "responsabilite", "perimetre", "programme", "plant", "linked_document", "work_order"]].copy()
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
    # the reporting scope used by every page, so all of them count the same NCs:
    #   serie  = raised at FTO2, FTO2 in the liability, not deleted
    #   client = customer return (raised elsewhere, FTO2 in the liability, not deleted)
    liab_f = nc_ref["liability"].fillna("").astype(str).str.upper().str.contains("FTO2")
    nc_ref["scope"] = np.select([(nc_ref.perimetre == "FTO2") & liab_f, nc_ref.perimetre == "Retour client"], ["serie", "client"], default="")
    d["scope"] = d.notification_number.map(nc_ref.set_index("notification_number")["scope"]).fillna("")
    d["phase"] = d.notification_number.map(nc_ref.set_index("notification_number")["phase"]).fillna("")
    return {"d": d, "nc": nc_ref, "lt": lt, "nc_in": nc_in, "nc_parser": np_, "nc_llm": nl_, "def_llm": dl_, "codes": codes, "report": report}


# ============================================================ 4. the page's NC fields and customer-return fields
def nc_extras(r, created_to):
    """NC fields for the aircraft, product, lead-time, time-of-day and NC charts: [msn, product family, station, creation hour (Paris),
    days to close (None while open), open, age in days if open, closure date, NC type, liability, SAP defect code, SAP cause group,
    SAP cause, status, data source, CNQ steps]. CNQ steps = the model's minutes [alert, writing, support, setup, hands-on, re-check],
    engineering hours and the final-inspection flag, for the "explain the calculation" part. SAP labels lose their brackets. Data source: every NC comes from Skywise; Ext_Source says whether it
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
                                                r.cnq_min_recheck, r.cnq_hours_engineering)] + [int(r.cnq_final_inspection or 0)]]


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
        rows.append([r.notification_number, r.date_creation, S_(r.ligne), S_(r.perimetre), S_(r.plant), int(r.cnq_on_aec), r.cnq_rule,
                     r.cnq_decision_label, r.cnq_where_found, round(r.cnq_cost_airbus, 2), round(r.cnq_cost_global, 2), round(r.cnq_cost_total, 2),
                     round(r.cnq_cost_admin, 2), round(r.cnq_cost_work, 2), round(r.cnq_cost_material, 2), round(r.cnq_cost_engineering, 2),
                     int(r.nc_cable_llm), int(r.cnq_defect_lines), S_(r.description_short)[:80], r.scope, S_(r.phase)]
                    + e[:15] + e[15] + [(lt.get(r.notification_number, "") or "")[:2500] if r.scope == "client" else ""])
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


def build(frames, labels, ref_dir):
    """Everything in one call, as the Skywise notebook uses it: (nc_t, def_t, info, to_label)."""
    x, info = merge_exports(frames)
    p = prepare(x, labels, ref_dir)
    nc_t, def_t = tables(p["d"], p["nc"], p["lt"], info["created_to"])
    aec = p["nc"][p["nc"].cnq_on_aec == 1]
    info.update(p["report"])
    info.update({"nc_table": int(len(nc_t)), "defect_table": int(len(def_t)), "level3_aec": round(float(aec.cnq_cost_total.sum()), 2),
                 "to_label": int((def_t.label_src == "parser").sum())})
    return nc_t, def_t, info, lines_to_label(p["d"], p["lt"])


def lines_to_label(d, lt):
    """Defect lines without a usable stored label (new, or text changed since it was labelled), for the periodic AI pass.
    snippet is the line's full text: a label is used only while the line's text stays the same as its snippet."""
    t = d[d.llm_status != "ok"]
    out = pd.DataFrame({"notification_number": t.notification_number, "seq": t.seq, "snippet": t.text.fillna(""),
                        "parser_sous_categorie": t.sous_groupe, "ligne": t.ligne, "date_creation": t.date_creation,
                        "long_text": t.notification_number.map(lambda n: (lt.get(n, "") or "")[:4000])})
    return out.reset_index(drop=True)
