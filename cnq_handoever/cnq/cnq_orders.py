# -*- coding: utf-8 -*-
"""
Planned time of each NC's rework orders, from the SAP work-order operations.

    times = nc_order_times(nc, ops)
    nc_out, defects_out = compute_cnq(nc.merge(times, on="notification_number", how="left"), defects)

nc    NC dataset with notification_number, linked_document, work_order
ops   work-order operations (the Skywise work-order operations dataset, or its CSV export) with order_number, order_type,
      operation_short_text, labor_standard_value and setup_standard_value with their units
      (unit_of_measure_for_the_standard_value_labor / _setup)

Returns one row per NC that has a rework-order link:
    rework_orders         the order numbers, space-separated
    order_state           used      every linked order is in ops, has its closing operation and planned time > 0
                          open      an order is in ops without its closing operation (not finished, or only partly in ops)
                          no_time   the orders are closed but carry no planned time
                          not_found an order is not in ops (outside the extract)
                          ""        no operations given (ops is None): the links only
    order_minutes_setup   planned minutes of the preparation, inspection and closing operations (ORDER_SETUP_KINDS)
    order_minutes_work    planned minutes of the work and test operations
compute_cnq uses the two times only when order_state is "used".
"""
import re

import numpy as np
import pandas as pd

from . import cnq_params as P


def rework_orders(linked_document, work_order, params=P):
    """Order numbers (no leading zeros) of the AW_/WO_/RS_ links that are not the NC's own work order."""
    own = re.sub(r"\.0$", "", str(work_order or "").strip()).lstrip("0")
    pat = r"(%s)_0*(\d+)" % "|".join(params.REWORK_ORDER_PREFIXES)
    return sorted({n for _, n in re.findall(pat, str(linked_document or "")) if n != own})


def order_times(ops, params=P):
    """One row per order: planned minutes per kind of operation, closed (has a closing operation)."""
    o = ops[ops["order_type"].astype(str).isin(params.ORDER_TYPES)].copy()
    o["order_number"] = o["order_number"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.lstrip("0")
    minutes = 0.0
    for v, u in (("labor_standard_value", "unit_of_measure_for_the_standard_value_labor"),
                 ("setup_standard_value", "unit_of_measure_for_the_standard_value_setup")):
        val = pd.to_numeric(o[v], errors="coerce").fillna(0.0) if v in o.columns else 0.0
        unit = o[u].astype(str).str.strip().str.upper().map(params.ORDER_UNIT_MINUTES) if u in o.columns else np.nan
        minutes = minutes + val * pd.Series(unit, index=o.index).fillna(0.0)
    o["_min"] = minutes
    t = o["operation_short_text"].fillna("").astype(str).str.lower()
    o["_kind"] = np.select([t.str.contains(rx) for _, rx in params.ORDER_OP_KINDS], [k for k, _ in params.ORDER_OP_KINDS], "work")
    is_setup = o["_kind"].isin(params.ORDER_SETUP_KINDS)
    o["_su"], o["_wk"], o["_cl"] = o["_min"].where(is_setup, 0.0), o["_min"].where(~is_setup, 0.0), o["_kind"] == "close"
    return o.groupby("order_number").agg(setup=("_su", "sum"), work=("_wk", "sum"), closed=("_cl", "any"))


def nc_order_times(nc, ops, params=P):
    """Per NC with a rework-order link: the order numbers, their state and planned minutes (see the module notes)."""
    ot = order_times(ops, params) if ops is not None else pd.DataFrame(columns=["setup", "work", "closed"])
    rows = []
    for n, ld, wo in zip(nc["notification_number"].astype(str), nc["linked_document"], nc["work_order"]):
        orders = rework_orders(ld, wo, params)
        if not orders:
            continue
        found = [o for o in orders if o in ot.index]
        setup = float(ot.loc[found, "setup"].sum()) if found else 0.0
        work = float(ot.loc[found, "work"].sum()) if found else 0.0
        if ops is None:
            state = ""
        elif len(found) < len(orders):
            state = "not_found"
        elif not ot.loc[found, "closed"].all():
            state = "open"
        elif setup + work <= 0:
            state = "no_time"
        else:
            state = "used"
        rows.append((n, " ".join(orders), state, round(setup, 1), round(work, 1)))
    return pd.DataFrame(rows, columns=["notification_number", "rework_orders", "order_state", "order_minutes_setup", "order_minutes_work"])
