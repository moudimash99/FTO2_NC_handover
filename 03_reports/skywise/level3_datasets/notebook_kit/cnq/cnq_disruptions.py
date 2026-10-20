# -*- coding: utf-8 -*-
"""
MES disruptions (aléas) and the cost of non-quality: the declared aléa time of each NC, and the disruption block.

    times, block = nc_alea_times(nc, ds)
    nc_out, defects_out = compute_cnq(nc.merge(times, on="notification_number", how="left"), defects)

nc   NC dataset with notification_number, work_order and the creation timestamp (creation_time)
ds   MES disruptions (the Skywise "MES Disruptions" dataset, or its CSV export) with disruption_id, work_order,
     open_date_time, open_date_time_tz, type_desc, time_lost (minutes typed by the operator), program, physical_station,
     wo_designation, ds_material, comment, status

Link: an aléa leads to an NC when the NC is on the same work order and was created between ALEA_LINK_HOURS[0] and
ALEA_LINK_HOURS[1] hours after the aléa opened; an aléa goes to the first such NC (Jan-Sep 2026: 214 of 322 quality aléas).

times  one row per NC with a linked quality aléa: aleas (ids, space-separated), alea_minutes (declared time lost, summed)
block  one row per quality aléa that led to no NC, with in_block = False for the possible ERMA aléas (MIP / 1101VB)
"""
import numpy as np
import pandas as pd

from . import cnq_params as P


def _wo(s):
    return s.astype("string").fillna("").str.strip().str.replace(r"\.0$", "", regex=True).str.lstrip("0")


def _opened(ds):
    tz = ds["open_date_time_tz"].astype("string").fillna("") if "open_date_time_tz" in ds.columns else ""
    return pd.to_datetime(ds["open_date_time"].astype("string").fillna("") + tz, errors="coerce", utc=True)


def link(nc, ds, params=P):
    """Every aléa with the NC it led to (empty when none): disruption_id, notification_number, hours from aléa to NC."""
    d = pd.DataFrame({"disruption_id": ds["disruption_id"].astype(str), "wo": _wo(ds["work_order"]), "opened": _opened(ds)})
    n = pd.DataFrame({"notification_number": nc["notification_number"].astype(str), "wo": _wo(nc["work_order"]),
                      "created": pd.to_datetime(nc["creation_time"], errors="coerce", utc=True)})
    m = d[d.wo != ""].merge(n[n.wo != ""], on="wo")
    m["hours"] = (m["created"] - m["opened"]).dt.total_seconds() / 3600
    lo, hi = params.ALEA_LINK_HOURS
    return m[(m.hours >= lo) & (m.hours <= hi)].sort_values("hours", kind="mergesort").drop_duplicates("disruption_id")[
        ["disruption_id", "notification_number", "hours"]]


def nc_alea_times(nc, ds, params=P):
    """(times, block): see the module notes."""
    ds = ds.copy()
    ds["disruption_id"] = ds["disruption_id"].astype(str)
    quality = ds["type_desc"].astype("string").fillna("").str.startswith(tuple(params.ALEA_TYPES))
    lk = link(nc, ds, params)
    q = ds[quality].copy()
    q["minutes"] = pd.to_numeric(q["time_lost"], errors="coerce").fillna(0.0)
    led = q.merge(lk, on="disruption_id")
    times = led.groupby("notification_number").agg(aleas=("disruption_id", lambda x: " ".join(sorted(x))), alea_minutes=("minutes", "sum")).reset_index()
    block = q[~q["disruption_id"].isin(lk["disruption_id"])].copy()
    erma = block.get("wo_designation", pd.Series("", index=block.index)).astype("string").fillna("").str.contains(params.ALEA_ERMA_DESIGNATION, case=False)
    erma |= block.get("ds_material", pd.Series("", index=block.index)).astype("string").fillna("").str.contains("1101")
    block["opened"] = _opened(block)
    block["in_block"] = ~erma.fillna(False).astype(bool)
    block["reason"] = np.where(block["in_block"], "", "erma")
    return times, block.reset_index(drop=True)
