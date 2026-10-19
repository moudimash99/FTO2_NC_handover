"""Build the FTO2 vision prototype: 09_vision/FTO2_Vision.html, plus expected.json for the page check.

Inputs: the dashboard outputs (05_outputs/fto2_nc.csv, fto2_defects.csv, made by build/build_all.py) and the
2025 NCs (09_vision/data/*_2025.csv, made by prep_2025.py). Every figure on the page is computed in the page from
these rows; this script only packs them and writes the values the check expects for a few filter settings.

    python3 09_vision/build_vision.py
"""
import json
import os
import sys
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from pins import consecutive, pin_pair  # noqa: E402

CATS = ["MEO Câblage", "Erreur Branchement", "Élément Manquant", "Élément Endommagé", "Déverrouillage",
        "Grounding/Bonding", "Kitting Factory", "FOD", "Autre"]
LINES = ["A350", "A330", "A320", "A400M"]
PHASES = ["SERIE", "REC", "FTI"]
# where the NC was found (cnq_where_found) -> the barrier shown on the page
WHERE = ["line", "cables", "final", "test", "other", "client"]
WHERE_OF = {"In-process (internal)": "line", "NC Interne": "line", "Breakage": "line", "Damage": "line",
            "Cables": "cables", "Final inspection": "final", "TEST": "test",
            "Supplier": "other", "Design query request": "other", "Customer return": "client"}
STEPS = ["alert", "writing", "support", "setup", "hands_on", "recheck"]


def load():
    nc = pd.read_csv(os.path.join(REPO, "05_outputs", "fto2_nc.csv"), low_memory=False, dtype={"notification_number": str})
    d = pd.read_csv(os.path.join(REPO, "05_outputs", "fto2_defects.csv"), low_memory=False, dtype={"notification_number": str})
    nc = nc[nc.scope.isin(["serie", "client"])].copy()
    d = d[d.scope.isin(["serie", "client"])].copy()
    n25 = pd.read_csv(os.path.join(HERE, "data", "nc_2025.csv"), dtype={"notification_number": str})
    d25 = pd.read_csv(os.path.join(HERE, "data", "defects_2025.csv"), dtype={"notification_number": str, "pin_a": str, "pin_b": str})
    n25 = n25[(n25.in_scope == 1) & n25.ligne.isin(LINES)].copy()
    d25 = d25[d25.notification_number.isin(n25.notification_number)].copy()
    return nc, d, n25, d25


def truthy(s):
    return s.astype(str).str.lower().isin(["true", "1", "1.0"]).astype(int)


def pack(nc, d, n25, d25):
    asof = pd.to_datetime(nc.date_creation).max().date()
    y0, y25 = date(asof.year, 1, 1), date(asof.year - 1, 1, 1)
    nc = nc.sort_values(["date_creation", "notification_number"]).reset_index(drop=True)
    row_of = {n: i for i, n in enumerate(nc.notification_number)}
    d = d[d.notification_number.isin(row_of)].sort_values(["notification_number", "seq"]).reset_index(drop=True)
    n25 = n25.sort_values(["date", "notification_number"]).reset_index(drop=True)
    row25 = {n: i for i, n in enumerate(n25.notification_number)}
    d25 = d25.sort_values(["notification_number", "seq"]).reset_index(drop=True)

    rcas = sorted(set(d.llm_rca_nom) | set(d.rca_nom) | set(d25.rca), key=lambda r: (CATS.index(cat_of(r, d, d25)), r))
    fins = sorted(set(d.fin.dropna()) | set(d25.fin.dropna()))
    fin_ix = {f: i for i, f in enumerate(fins)}
    products = sorted(nc.produit.fillna("Other").unique())
    decisions = sorted(nc.decision_label.fillna("No decision").unique())

    pins26 = d.text.map(pin_pair)
    day = lambda s, y: (pd.to_datetime(s).dt.date - y).map(lambda t: t.days)
    close_days = (pd.to_datetime(nc.closure_time, utc=True) - pd.to_datetime(nc.creation_ts, utc=True)).dt.total_seconds() / 86400

    D = {
        "meta": {"asof": asof.isoformat(), "y": asof.year, "built": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                 "ncFile": "05_outputs/fto2_nc.csv", "n2025": int(len(n25))},
        "dict": {"line": LINES, "cat": CATS, "rca": rcas, "rcaCat": [CATS.index(cat_of(r, d, d25)) for r in rcas],
                 "where": WHERE, "phase": PHASES, "fin": fins, "product": products, "decision": decisions, "step": STEPS},
        "nc": {
            "id": nc.notification_number.tolist(),
            "d": day(nc.date_creation, y0).tolist(),
            "l": nc.ligne.map(LINES.index).tolist(),
            "m": nc.msn.astype(int).tolist(),
            "ph": nc.phase.map(PHASES.index).tolist(),
            "sc": (nc.scope == "client").astype(int).tolist(),
            "w": nc.cnq_where_found.map(WHERE_OF).map(WHERE.index).tolist(),
            "dec": nc.decision_label.fillna("No decision").map(decisions.index).tolist(),
            "pr": nc.produit.fillna("Other").map(products.index).tolist(),
            "op": (nc.statut == "open").astype(int).tolist(),
            "cd": [round(x, 1) if x == x else -1 for x in close_days],
            "nd": [int(x) if x == x else -1 for x in nc.nb_defauts],
            "c": nc.cnq_cost_total.round(2).tolist(),
            "cA": nc.cnq_cost_airbus.round(2).tolist(),
            "cG": nc.cnq_cost_global.round(2).tolist(),
            "eng": nc.cnq_cost_engineering.round(2).tolist(),
            "mat": nc.cnq_cost_material.round(2).tolist(),
            **{"t_" + s: nc["cnq_min_" + s].round(1).tolist() for s in STEPS},
        },
        "df": {
            "n": d.notification_number.map(row_of).tolist(),
            "k": d.llm_categorie.map(CATS.index).tolist(),
            "r": d.llm_rca_nom.map(rcas.index).tolist(),
            "pk": d.groupe.map(CATS.index).tolist(),
            "pr": d.rca_nom.map(rcas.index).tolist(),
            "cb": truthy(d.llm_defaut_cable).tolist(),
            "pcb": truthy(d.defaut_cable).tolist(),
            "mi": truthy(d.llm_mineur).tolist(),
            "f": [fin_ix.get(f, -1) for f in d.fin],
            "pa": [p[0] if p else "" for p in pins26],
            "pb": [p[1] if p else "" for p in pins26],
            "c": d.cnq_cost_allocated_llm.round(2).tolist(),
        },
        "nc25": {
            "d": day(n25.date, y25).tolist(),
            "l": n25.ligne.map(LINES.index).tolist(),
            "m": n25.msn.astype(int).tolist(),
            "ph": n25.phase.map(PHASES.index).tolist(),
        },
        "df25": {
            "n": d25.notification_number.map(row25).tolist(),
            "pk": d25.categorie.map(CATS.index).tolist(),
            "pr": d25.rca.map(rcas.index).tolist(),
            "pcb": d25.cable.astype(int).tolist(),
            "f": [fin_ix.get(f, -1) for f in d25.fin],
            "pa": d25.pin_a.fillna("").tolist(),
            "pb": d25.pin_b.fillna("").tolist(),
        },
    }
    frames = {"nc": nc, "d": d, "n25": n25, "d25": d25, "pins26": pins26, "asof": asof}
    return D, frames


_CAT_OF = {}


def cat_of(rca, d, d25):
    if not _CAT_OF:
        for a, b in [(d.llm_rca_nom, d.llm_categorie), (d.rca_nom, d.groupe), (d25.rca, d25.categorie)]:
            for r, c in zip(a, b):
                _CAT_OF.setdefault(r, c)
    return _CAT_OF[rca]


def expected(F, line=None, phase="SERIE", cable=False):
    """The figures the page must show for one filter setting (same rules as the page script)."""
    nc, d, n25, d25, asof = F["nc"], F["d"], F["n25"], F["d25"], F["asof"]
    cut = asof.strftime("%m-%d")
    ok = lambda df: (df.ligne == line if line else df.ligne.notna()) & (df.phase == phase if phase else df.phase.notna())
    s = nc[ok(nc) & (nc.scope == "serie")]
    sd = d[d.notification_number.isin(s.notification_number)]
    cl = nc[ok(nc) & (nc.scope == "client")]
    cd = d[d.notification_number.isin(cl.notification_number)]
    if cable:
        sd = sd[truthy(sd.llm_defaut_cable) == 1]
        cd = cd[truthy(cd.llm_defaut_cable) == 1]
        s = s[s.notification_number.isin(sd.notification_number)]
        cl = cl[cl.notification_number.isin(cd.notification_number)]
    a25 = n25[(n25.ligne == line if line else n25.ligne.notna()) & (n25.phase == phase if phase else n25.phase.notna())
              & (n25.date.str[5:] <= cut)]
    a25d = d25[d25.notification_number.isin(a25.notification_number)]
    s_pd = d[d.notification_number.isin(nc[ok(nc) & (nc.scope == "serie")].notification_number)]   # parser view, 2026
    if cable:
        a25d = a25d[a25d.cable == 1]
        a25 = a25[a25.notification_number.isin(a25d.notification_number)]
        s_pd = s_pd[truthy(s_pd.defaut_cable) == 1]
    w = s.cnq_where_found.map(WHERE_OF)
    found = sd.merge(s[["notification_number", "cnq_where_found"]], on="notification_number")
    esc = pd.concat([found.assign(stage=found.cnq_where_found.map(WHERE_OF)), cd.assign(stage="client")])
    by_cat = esc.groupby("llm_categorie").stage.apply(lambda x: (x == "client").sum()).to_dict()
    mins = {st: round(float(s["cnq_min_" + st].mean()), 1) if len(s) else 0 for st in STEPS}
    cost = float(sd.cnq_cost_allocated_llm.sum()) if cable else float(s.cnq_cost_total.sum())
    return {
        "nc": int(len(s)), "defects": int(len(sd)), "cost": round(cost), "clientNc": int(len(cl)), "clientDefects": int(len(cd)),
        "cableDefects": int(truthy(sd.llm_defaut_cable).sum()),
        "nc2025": int(len(a25)), "defects2025": int(len(a25d)), "defects2026parser": int(len(s_pd)),
        "found": {k: int(v) for k, v in w.value_counts().items()},
        "escapesByCat": {k: int(v) for k, v in by_cat.items() if v},
        "minutesPerNc": mins,
        "methods": {"airbus": round(float(s.cnq_cost_airbus.sum())), "detail": round(float(s.cnq_cost_total.sum())), "aec": round(float(s.cnq_cost_global.sum()))},
    }


def main():
    nc, d, n25, d25 = load()
    D, F = pack(nc, d, n25, d25)
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    data = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    page = tpl.replace("/*__DATA__*/null", data)
    out = os.path.join(HERE, "FTO2_Vision.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    exp = {"default": expected(F), "A350": expected(F, line="A350"), "cable": expected(F, cable=True),
           "allPhases": expected(F, phase=None)}
    with open(os.path.join(HERE, "expected.json"), "w", encoding="utf-8") as f:
        json.dump(exp, f, ensure_ascii=False, indent=1)
    p = F["pins26"].dropna()
    print("page:", out, round(os.path.getsize(out) / 1024), "KB | data", round(len(data) / 1024), "KB")
    print("default:", {k: v for k, v in exp["default"].items() if not isinstance(v, dict)})
    print("pins: %d of %d inversion-type defects named two pins, %d consecutive" % (
        len(p), int((d.llm_rca_nom == "Inversion").sum()), sum(consecutive(*x) for x in p)))


if __name__ == "__main__":
    main()
