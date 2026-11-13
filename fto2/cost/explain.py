"""The cost explanation of each NC ("Expliquer le calcul" on the dashboard's cost tab), worked out by the notebook.

The dashboard can work it out itself (build/templates/model.js, coutNc) or read it from this table, fto2_dash_cout. Reading it is
the second way of the Skywise set-up (03_reports/skywise/level3_datasets/fonctions/README.md): the page then only draws it.

Same rules as the page, from the same inputs: the dashboard's NC and defect tables and the cost settings the page receives
(fto2/reference.py, cnq_explain). tests/test_slate_functions.py checks that both give the same figures.

    one row per NC (seq 0)              the euros of each step, the work factor, the adjustment (what the cost holds beyond the
                                        steps, engineering and material: the customer-return extra)
    one row per defect line (seq 1...)  its minutes, its material, its class (in French as in config/, and in English)
"""
import math

import pandas as pd

COLUMNS = [
    ("nc", "text", "NC number"),
    ("seq", "int", "0 for the NC itself, else the number of its defect line"),
    ("eur_alert", "num", "NC: alert step (EUR)"),
    ("eur_writing", "num", "NC: writing the NC (EUR)"),
    ("eur_support", "num", "NC: technical support (EUR)"),
    ("eur_setup", "num", "NC: work around the job (EUR)"),
    ("eur_hands_on", "num", "NC: hands-on work (EUR)"),
    ("eur_recheck", "num", "NC: re-check and closing (EUR)"),
    ("work_factor", "num", "NC: factor on the work time (internal NCs)"),
    ("adjust", "num", "NC: what its cost holds beyond the steps, engineering, material and the part (customer-return extra), EUR"),
    ("minutes", "num", "defect line: minutes of work from its class (connection errors: only the first one takes the class time)"),
    ("material", "num", "defect line: material (EUR)"),
    ("defect_class", "text", "defect line: its class (sub-category)"),
    ("defect_class_en", "text", "defect line: its class in English (empty when the class is not in the cost settings)"),
]
# the six steps: the rate's name in the cost settings, the minutes' column in fto2_dash_nc
STEPS = [("alert", "min_alert"), ("writing", "min_writing"), ("support", "min_support"), ("setup", "min_setup"),
         ("hands", "min_hands_on"), ("recheck", "min_recheck")]


def _text(v):
    return "" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(x) else x


def table(nc_t, def_t, cnqp):
    """fto2_dash_cout from the dashboard's two tables (fto2/core.py, NC_COLUMNS and DEF_COLUMNS) and the cost settings."""
    p, rules, cls = cnqp["p"], cnqp["rules"], cnqp["cls"]
    rates = p.get("rates") or {}
    rate = lambda k: rates[k] if rates.get(k) is not None else p["rate"]
    internal = {str(t).upper() for t in p.get("intTypes") or []}
    conn = set(p.get("connCls") or [])
    lines = {}
    for r in def_t.itertuples():
        lines.setdefault(_text(r.nc), []).append(r)
    rows = []
    for n in nc_t.itertuples():
        nid, st = _text(n.nc), [_num(getattr(n, c)) for _, c in STEPS]
        # the adjustment, summed in the page's order so that both give the same figure to the cent
        f, adj = rules.get(n.rule), 0.0
        if f:
            on, e = [f[0], f[1], f[2], f[3], f[3], f[4]], 0.0
            for j, (k, _) in enumerate(STEPS):
                e = e + (st[j] / 60 * rate(k) if on[j] else 0)
            d = _num(n.cost_total) - (e + _num(n.cost_engineering) + _num(n.cost_material) + _num(getattr(n, "cost_part", 0)))
            adj = d if abs(d) >= 0.05 else 0.0
        factor = (p.get("intFactor") or 1) if _text(n.type_nc).upper() in internal else 1
        rows.append([nid, 0] + [st[j] / 60 * rate(k) for j, (k, _) in enumerate(STEPS)] + [factor, adj, None, None, "", ""])
        seen = 0
        for r in sorted(lines.get(nid, []), key=lambda r: int(r.seq)):
            sub, q = _text(r.sub), _num(r.qty)
            q = int(math.floor(q + 0.5)) or 1   # as the page reads the quantity: rounded, and 1 when it is 0 or missing
            c = cls.get(sub)
            per = c[0] if c else p["defDefault"]
            m = per * q
            if conn and sub in conn:   # connection errors: the first one of the NC takes the class time, each next one less
                first = max(0, min(q, 1 - seen))
                seen += q
                m = per * first + p["connNext"] * (q - first)
            rows.append([nid, int(r.seq)] + [None] * 8 + [m, (c[1] if c else 0) * q, sub, c[2] if (sub and c) else ""])
    return pd.DataFrame(rows, columns=[c[0] for c in COLUMNS])
