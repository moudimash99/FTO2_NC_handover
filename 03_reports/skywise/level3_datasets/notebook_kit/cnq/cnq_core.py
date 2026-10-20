# -*- coding: utf-8 -*-
"""
Cost of non-quality (CNQ) - calculation.

One function, `compute_cnq(nc, defects)`, takes the two pipeline datasets as pandas
DataFrames and returns them with cost columns added:

    nc       one row per NC            (the "FTO2" dataset)
    defects  one row per defect line   (the "FTO2 defects" dataset, output of the defect parser)

All numbers come from cnq_params.py. No Foundry or Spark dependency here, so it can be
tested on a laptop with two CSV files (see run_local.py).

How one NC is costed
--------------------
  rule          = "DELETED" if the NC is deleted, else its decision code (RWK, EXC, REJ, ...); a rejection whose
                  NC has a rework order (linked_document, see REWORK_ORDER_PREFIXES) becomes "REJ_RW"
  admin minutes = alert + writing the NC (longer at final inspection) + technical support + re-check/close
                  (each charged or not, according to the rule; the alert only when an operator raises one,
                  i.e. not for NCs found at test or at final inspection; customer returns always get it).
                  When the NC dataset carries the declared time of the quality aléas that led to the NC
                  (cnq_disruptions.nc_alea_times, column alea_minutes > 0): the alert is that time, charged
                  whatever the NC type (USE_ALEA_TIME)
  work minutes  = if the rule includes work: fixed setup + sum of minutes of its defect lines
                  (flat figure when the NC has no defect line); the first connection error of an NC takes its
                  class time, each following one MIN_CONNECTION_NEXT; internal NCs x INTERNAL_WORK_FACTOR.
                  When the NC dataset carries the planned time of the NC's rework orders (cnq_orders.nc_order_times)
                  and they are all closed and planned (order_state "used"): setup = the orders' preparation,
                  inspection and closing operations, hands-on = their work and test operations (USE_ORDER_TIME)
  engineering   = hours from the rule (design queries)
  material      = sum of material of its defect lines, if the rule includes work
  part value    = `part_value` column if present and the rule counts the part (else 0)
  total         = each step's minutes / 60 * the rate of who does it (STEP_RATES: production, quality, ME)
                  + engineering hours * engineering rate (Airbus) + material + part
  customer return: + a flat extra (CUSTOMER_RETURN_EXTRA), or replaced by the real amount when the NC dataset
                   has a `customer_return_cost` value for that NC
  AEC cost      = total if liability == AEC plant code, else 0   (others are shown aside)

Two comparison figures are written next to it for every NC:
  cnq_cost_airbus  = level 1, the official Airbus standard cost for that decision (no material)
  cnq_cost_global  = level 2, the same steps with average times (work = 1 hour flat), plus material
  cnq_cost_total   = level 3, the detailed cost described above
"""
import re

import numpy as np
import pandas as pd

from . import cnq_params as P

NC_REQUIRED = ["notification_number", "statut", "decision_status", "liability", "date_creation"]
DEFECT_REQUIRED = ["notification_number", "sous_groupe"]


def _norm_code(s):
    """'[FTO2]' -> 'FTO2'; keeps None."""
    return s.astype("string").str.strip().str.strip("[]").str.strip()


def _first_present(df, names):
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series([None] * len(df), index=df.index, dtype="object")


def _has_rework_order(nc, params):
    """True when linked_document holds an AW_/WO_/RS_ number different from the NC's own work order."""
    if "linked_document" not in nc.columns or "work_order" not in nc.columns:
        return pd.Series(False, index=nc.index)
    pat = re.compile(r"(?:%s)_0*(\d+)" % "|".join(params.REWORK_ORDER_PREFIXES))
    own = nc["work_order"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True).str.lstrip("0").fillna("")
    links = nc["linked_document"].astype("string").fillna("")
    return pd.Series([any(n != o for n in pat.findall(l)) for l, o in zip(links, own)], index=nc.index)


def compute_cnq(nc, defects, params=P):
    """Return (nc_out, defects_out) with CNQ columns added. Inputs are not modified."""
    missing = [c for c in NC_REQUIRED if c not in nc.columns]
    if missing:
        raise ValueError("NC dataset is missing column(s) needed for the cost: %s" % ", ".join(missing))
    missing = [c for c in DEFECT_REQUIRED if c not in defects.columns]
    if missing:
        raise ValueError("Defect dataset is missing column(s) needed for the cost: %s" % ", ".join(missing))
    if nc["notification_number"].duplicated().any():
        raise ValueError("NC dataset has duplicated notification_number: one row per NC is required")

    nc = nc.copy()
    d = defects.copy()
    rules = pd.DataFrame.from_dict(params.RULES, orient="index", columns=list(params.RULE_FIELDS))
    times = pd.DataFrame.from_dict(params.DEFECT_TIMES, orient="index", columns=list(params.DEFECT_FIELDS))

    # ------------------------------------------------------------ NC: rule, liability, where found
    statut = nc["statut"].astype("string").str.strip().str.lower()
    decision = _norm_code(nc["decision_status"]).str.upper()
    has_master = statut.notna()
    rule = decision.where(decision.isin(rules.index), "UNKNOWN")
    rule = rule.where((statut != "deleted").fillna(True), "DELETED")
    rule = rule.where(has_master, "NO_DATA")
    has_order = _has_rework_order(nc, params)
    nc["cnq_rework_order"] = has_order.astype(int)
    rule = rule.where(~((rule == "REJ") & has_order).fillna(False), "REJ_RW")
    nc["cnq_rule"] = rule.astype(object)
    nc["cnq_decision_label"] = nc["cnq_rule"].map(rules["label"]).fillna("No master data")

    liab = _norm_code(nc["liability"]).str.upper()
    liab_type = _norm_code(_first_present(nc, ["liability_description", "responsabilite"])).str.upper()
    on_aec = (liab == params.AEC_PLANT_CODE.upper()) & has_master
    nc["cnq_on_aec"] = on_aec.fillna(False).astype(int)
    group = np.select(
        [~has_master, on_aec.fillna(False), liab_type.fillna("") == "PLANT", liab_type.fillna("") == "SUPPLIER"],
        ["No master data", "AEC", "Other Airbus plant", "Supplier"], default="Other or blank")
    nc["cnq_liability_group"] = group

    type_nc = _first_present(nc, ["type_nc", "GPS_Type_NC"])
    if "type_nc" not in nc.columns and "Type_NC_auto" in nc.columns:
        type_nc = type_nc.where(type_nc.notna(), nc["Type_NC_auto"])
    type_nc = type_nc.astype("string").str.strip()
    nc["cnq_final_inspection"] = type_nc.str.upper().isin([t.upper() for t in params.FINAL_INSPECTION_TYPES]).fillna(False).astype(int)
    # customer return: column customer_return (1/0), set by the dashboard's data step from the pipeline's Type_NC_auto
    # ("NC Retour client") with FTO2 in the liability list
    cr = pd.to_numeric(_first_present(nc, ["customer_return"]), errors="coerce")
    nc["cnq_customer_return"] = (cr.fillna(0) > 0).astype(int)
    labelled = type_nc.str.upper().map(params.WHERE_FOUND_LABELS).astype(object)
    labelled = labelled.where(labelled.notna(), type_nc.astype(object)).where(type_nc.notna(), "Not recorded")
    nc["cnq_where_found"] = np.where(nc["cnq_customer_return"] == 1, "Customer return",
                             np.where(nc["cnq_final_inspection"] == 1, "Final inspection", labelled))
    nc.loc[~has_master, "cnq_where_found"] = "No master data"
    type_up = type_nc.str.upper()
    no_alert = type_up.isin([t.upper() for t in params.NO_ALERT_TYPES]).fillna(False) & (nc["cnq_customer_return"] == 0)
    nc["cnq_alert_raised"] = (~no_alert).astype(int)
    # declared time of the quality aléas that led to the NC: an aléa was raised, whatever the NC type; 0 = not filled
    a_min = pd.to_numeric(_first_present(nc, ["alea_minutes"]), errors="coerce").fillna(0.0)
    use_alea = (a_min > 0) & (nc["cnq_customer_return"] == 0) & bool(getattr(params, "USE_ALEA_TIME", False))
    nc.loc[use_alea, "cnq_alert_raised"] = 1
    internal = type_up.isin([t.upper() for t in params.INTERNAL_TYPES]).fillna(False)
    nc["cnq_work_factor"] = np.where(internal, params.INTERNAL_WORK_FACTOR, 1.0)

    # ------------------------------------------------------------ defect lines: minutes and material
    known = d["sous_groupe"].isin(times.index)
    qty = pd.to_numeric(d["qty"], errors="coerce").fillna(1) if "qty" in d.columns else pd.Series(1.0, index=d.index)
    d["cnq_time_known"] = known.astype(int)
    d["cnq_label_en"] = d["sous_groupe"].map(times["label_en"]).fillna("Unknown class")
    d["cnq_min_per_defect"] = d["sous_groupe"].map(times["minutes"]).fillna(params.MIN_DEFAULT_DEFECT).astype(float)
    d["cnq_mat_per_defect"] = d["sous_groupe"].map(times["material_eur"]).fillna(0.0).astype(float)
    # connection errors: only the first one of the NC (in line order) takes the class time
    conn_qty = qty.where(d["sous_groupe"].isin(params.CONNECTION_CLASSES), 0.0)
    order = d.assign(_seq=pd.to_numeric(d["seq"], errors="coerce") if "seq" in d.columns else 0.0).sort_values(
        ["notification_number", "_seq"], kind="mergesort").index
    before = (conn_qty.loc[order].groupby(d.loc[order, "notification_number"], dropna=False).cumsum() - conn_qty.loc[order]).reindex(d.index).fillna(0.0)
    first = np.minimum(conn_qty, (1 - before).clip(lower=0))
    d["cnq_conn_next"] = conn_qty - first
    d["_min"] = d["cnq_min_per_defect"] * (qty - d["cnq_conn_next"]) + d["cnq_conn_next"] * params.MIN_CONNECTION_NEXT
    d["_mat"] = d["cnq_mat_per_defect"] * qty
    d["_n"] = qty
    agg = d.groupby("notification_number").agg(_lines=("_n", "sum"), _min=("_min", "sum"), _mat=("_mat", "sum"))
    nc = nc.merge(agg, left_on="notification_number", right_index=True, how="left")
    for c in ("_lines", "_min", "_mat"):
        nc[c] = nc[c].fillna(0.0)

    # ------------------------------------------------------------ NC: minutes per step
    flag = lambda f: nc["cnq_rule"].map(rules[f]).fillna(0).astype(float)
    work = flag("work")
    nc["cnq_defect_lines"] = nc["_lines"].astype(int)
    alert = flag("alert") * nc["cnq_alert_raised"]
    nc["cnq_min_alert"] = alert * np.where(use_alea, a_min, params.MIN_ALERT)
    nc["cnq_alert_source"] = np.where(alert == 0, "", np.where(use_alea, "alea", "flat"))
    nc["cnq_min_writing"] = flag("write") * np.where(nc["cnq_final_inspection"] == 1, params.MIN_WRITE_NC_FINAL, params.MIN_WRITE_NC)
    nc["cnq_min_support"] = flag("support") * params.MIN_SUPPORT
    hands = np.where(nc["_lines"] == 0, params.MIN_HANDS_ON_NO_DEFECT, nc["_min"])
    nc["cnq_min_hands_on"] = work * nc["cnq_work_factor"] * hands
    # time around the job: the fixed setup, or more if needed so that the work is never under the floor (1 hour)
    nc["cnq_min_setup"] = work * nc["cnq_work_factor"] * np.maximum(params.MIN_SETUP, params.MIN_WORK_FLOOR - hands)
    # planned time of the rework orders, when known, replaces the model's setup and hands-on (no connection rule, no factor)
    state = _first_present(nc, ["order_state"]).astype("string")
    use_order = (work == 1) & (state == "used").fillna(False) & bool(getattr(params, "USE_ORDER_TIME", False))
    o_setup = pd.to_numeric(_first_present(nc, ["order_minutes_setup"]), errors="coerce").fillna(0.0)
    o_work = pd.to_numeric(_first_present(nc, ["order_minutes_work"]), errors="coerce").fillna(0.0)
    nc["cnq_work_source"] = np.where(work == 0, "", np.where(use_order, "order", "model"))
    # the defect lines' own minutes follow the order's hands-on time, for sharing the cost among lines
    nc["_k"] = np.where(use_order, np.where(nc["_min"] > 0, o_work / nc["_min"].where(nc["_min"] > 0, 1.0), 0.0), 1.0)
    nc["cnq_min_hands_on"] = np.where(use_order, o_work, nc["cnq_min_hands_on"])
    nc["cnq_min_setup"] = np.where(use_order, o_setup, nc["cnq_min_setup"])
    nc["cnq_min_recheck"] = flag("recheck") * params.MIN_RECHECK_CLOSE
    nc["cnq_hours_engineering"] = flag("eng_hours")

    # ------------------------------------------------------------ NC: euros
    R = getattr(params, "STEP_RATES", None) or {k: params.RATE_STANDARD for k in ("alert", "writing", "support", "setup", "hands_on", "recheck")}
    part_in = pd.to_numeric(nc["part_value"], errors="coerce") if "part_value" in nc.columns else pd.Series(np.nan, index=nc.index)
    part_flag = flag("part")
    for step in ("alert", "writing", "support", "setup", "hands_on", "recheck"):
        nc["cnq_cost_" + step] = nc["cnq_min_" + step] / 60.0 * R[step]   # each step at the rate of who does it
    nc["cnq_cost_admin"] = nc[["cnq_cost_alert", "cnq_cost_writing", "cnq_cost_support", "cnq_cost_recheck"]].sum(axis=1)
    nc["cnq_cost_work"] = nc[["cnq_cost_setup", "cnq_cost_hands_on"]].sum(axis=1)
    nc["cnq_cost_engineering"] = nc["cnq_hours_engineering"] * params.RATE_ENGINEERING
    nc["cnq_cost_material"] = work * nc["_mat"]
    nc["cnq_cost_part"] = part_flag * part_in.fillna(0.0)
    modelled = nc[["cnq_cost_admin", "cnq_cost_work", "cnq_cost_engineering", "cnq_cost_material", "cnq_cost_part"]].sum(axis=1)
    # customer returns: flat extra per return, or the real amount when the dataset carries one
    is_return = (nc["cnq_customer_return"] == 1) & has_master
    col = params.CUSTOMER_RETURN_COST_COLUMN
    real = pd.to_numeric(nc[col], errors="coerce") if col in nc.columns else pd.Series(np.nan, index=nc.index)
    final = np.where(is_return & real.notna(), real.fillna(0.0), modelled + np.where(is_return, params.CUSTOMER_RETURN_EXTRA, 0.0))
    nc["cnq_cost_modelled"] = modelled
    nc["cnq_cost_customer_adjust"] = final - modelled
    nc["cnq_customer_amount_known"] = (is_return & real.notna()).astype(int)
    nc["cnq_cost_total"] = final
    # ---- comparison level 2 "Global": average times for every NC, same material
    global_eur = (alert * params.MIN_ALERT * R["alert"] + flag("write") * params.MIN_WRITE_NC_GLOBAL * R["writing"]
                  + flag("support") * params.MIN_SUPPORT * R["support"] + work * params.MIN_WORK_GLOBAL * R["hands_on"]
                  + flag("recheck") * params.MIN_RECHECK_CLOSE * R["recheck"]) / 60.0
    nc["cnq_cost_global"] = global_eur + nc["cnq_cost_engineering"] + nc["cnq_cost_material"] + nc["cnq_cost_part"]
    # ---- comparison level 1 "Airbus transnational": official standard cost per NC, no material
    nc["cnq_cost_airbus"] = nc["cnq_rule"].map(params.AIRBUS_STANDARD).fillna(0.0).astype(float)
    nc["cnq_cost_aec"] = nc["cnq_cost_total"] * nc["cnq_on_aec"]
    nc["cnq_complete"] = np.select(
        [~has_master, (part_flag == 1) & part_in.isna(), (work == 1) & (nc["_lines"] == 0) & ~use_order],
        ["No master data", "Part value unknown", "Work time is a flat estimate (no defect line)"], default="Complete")

    # ------------------------------------------------------------ NC: calendar helpers for the charts
    dt = pd.to_datetime(nc["date_creation"], errors="coerce", utc=True).dt.tz_localize(None)
    iso = dt.dt.isocalendar()
    nc["cnq_month"] = dt.dt.strftime("%Y-%m")
    nc["cnq_week"] = (iso["year"].astype("Int64").astype("string") + "-W" + iso["week"].astype("Int64").astype("string").str.zfill(2))
    nc["cnq_model_version"] = params.MODEL_VERSION
    k_line = nc.set_index("notification_number")["_k"]
    nc = nc.drop(columns=["_lines", "_min", "_mat", "_k"])

    # ------------------------------------------------------------ defect lines: what is actually charged
    back = nc.set_index("notification_number")
    d["cnq_on_aec"] = d["notification_number"].map(back["cnq_on_aec"]).fillna(0).astype(int)
    d["cnq_rule"] = d["notification_number"].map(back["cnq_rule"]).fillna("NO_DATA")
    d["cnq_work_costed"] = d["cnq_rule"].map(rules["work"]).fillna(0).astype(int)
    d["cnq_line_costed"] = d["cnq_on_aec"] * d["cnq_work_costed"]
    d["cnq_min_hands_on"] = d["cnq_line_costed"] * d["_min"] * d["notification_number"].map(k_line).fillna(1.0)
    d["cnq_cost_material"] = d["cnq_line_costed"] * d["_mat"]
    d["cnq_cost_hands_on"] = d["cnq_min_hands_on"] / 60.0 * R["hands_on"]
    d["cnq_cost_direct"] = d["cnq_cost_hands_on"] + d["cnq_cost_material"]
    d["cnq_month"] = d["notification_number"].map(back["cnq_month"])
    d["cnq_week"] = d["notification_number"].map(back["cnq_week"])
    d["cnq_model_version"] = params.MODEL_VERSION
    d = d.drop(columns=["_min", "_mat", "_n"])
    return _clean(nc), _clean(d)


def _clean(df):
    """Make the frame safe to hand to Spark: no NaN inside text columns, plain Python types."""
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype).startswith("string"):
            df[c] = df[c].astype(object).where(df[c].notna(), None)
    return df


def parameters_as_tables(params=P):
    """The parameters as three small tables, for review or to publish next to the datasets."""
    steps = pd.DataFrame([
        ("RATE_PROD", params.RATE_PROD, "EUR/hour", "AEC"), ("RATE_QUALITY", params.RATE_QUALITY, "EUR/hour", "AEC"),
        ("RATE_ME", params.RATE_ME, "EUR/hour", "AEC"), ("RATE_ENGINEERING", params.RATE_ENGINEERING, "EUR/hour", "OFFICIAL"),
        ("MIN_ALERT", params.MIN_ALERT, "minutes", "MES"), ("MIN_WRITE_NC", params.MIN_WRITE_NC, "minutes", "LOCAL"),
        ("MIN_WRITE_NC_FINAL", params.MIN_WRITE_NC_FINAL, "minutes", "LOCAL"), ("MIN_SUPPORT", params.MIN_SUPPORT, "minutes", "LOCAL"),
        ("MIN_SETUP", params.MIN_SETUP, "minutes", "LOCAL"), ("MIN_RECHECK_CLOSE", params.MIN_RECHECK_CLOSE, "minutes", "LOCAL"),
        ("MIN_HANDS_ON_NO_DEFECT", params.MIN_HANDS_ON_NO_DEFECT, "minutes", "LOCAL"), ("MIN_DEFAULT_DEFECT", params.MIN_DEFAULT_DEFECT, "minutes", "ASSUMED"),
        ("MIN_CONNECTION_NEXT", params.MIN_CONNECTION_NEXT, "minutes", "WO"), ("INTERNAL_WORK_FACTOR", params.INTERNAL_WORK_FACTOR, "factor", "WO"),
    ], columns=["parameter", "value", "unit", "basis"])
    rules = pd.DataFrame.from_dict(params.RULES, orient="index", columns=list(params.RULE_FIELDS)).rename_axis("rule").reset_index()
    times = pd.DataFrame.from_dict(params.DEFECT_TIMES, orient="index", columns=list(params.DEFECT_FIELDS)).rename_axis("sous_groupe").reset_index()
    return steps, rules, times
