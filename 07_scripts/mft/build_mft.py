"""MFT page for the weekly QLS review: one line at a time, the week's Pareto, a short analysis and the action follow-up.

Reads the dashboard's two tables (05_outputs/fto2_dash_nc.csv, fto2_dash_defects.csv) and the A330 / A350 MFT trackers
(config/1_actions_mft.csv, written from the trackers by scripts/actions_mft_depuis_suivis.py).
Writes 03_reports/FTO2_MFT.html (and build/artifacts/FTO2_MFT.html) from 07_scripts/mft/mft_template.html, its Slate
version in 03_reports/skywise/mft/ (build_mft_slate.py), and the tracker actions as 05_outputs/mft_actions_seed.json: the page keeps its actions in its own store (seeded once from that
file); the page itself carries no action.

Scope as the dashboard's default: NCs raised at FTO2 (plant FTO2 or FT02), created in the year followed; the phase is a filter in
the page (Série by default).

    python3 -I 07_scripts/mft/build_mft.py
"""
import datetime as dt
import json
import os
import re

import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from fto2 import config   # noqa: E402   the settings in config/
from fto2 import reference as REF   # noqa: E402   the pages' settings


def week(d):
    y, w, _ = dt.date.fromisoformat(d[:10]).isocalendar()
    return "%d-W%02d" % (y, w)


def tidy(s, n=320):
    if s is None or (isinstance(s, float) and s != s):   # empty cells read as NaN
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()[:n]


def data():
    n = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_nc.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    d = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_defects.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    home, since = config.parameter_list("usines_maison"), config.first_day()   # config/2_parametres.csv: the plant, the year followed
    n = n[n.plant.str.strip().str.upper().isin(home) & (n.created >= since)].sort_values("created")
    dic = {k: [] for k in ("line", "phase", "msn", "station", "where", "cat", "rca", "sub", "code", "fin", "prod")}
    plan_prod = plan_products()
    idx = {k: {} for k in dic}

    def code(k, v):
        v = tidy(v, 120)
        if v not in idx[k]:
            idx[k][v] = len(dic[k])
            dic[k].append(v)
        return idx[k][v]

    ncs, pos = [], {}
    for r in n.itertuples():
        pos[r.nc] = len(ncs)   # [nc, date, line, phase, msn, station, where found, plan product]
        ncs.append([r.nc, r.created[:10], code("line", r.line or "—"), code("phase", r.phase), code("msn", r.msn), code("station", r.station),
                    code("where", r.where_found), code("prod", plan_prod(r.line, r.product, r.station))])
    defs = []
    for r in d.itertuples():
        i = pos.get(r.nc)
        if i is None:
            continue   # [NC index, category, cause, sub-category, sub-code, FIN, minor, text]
        defs.append([i, code("cat", r.cat), code("rca", r.rca), code("sub", r.sub), code("code", r.subcode), code("fin", r.fin), int(r.minor or 0), tidy(r.text)])
    fr = config.frame("3_souscodes_fr.csv").set_index("sous_code").description_fr.to_dict()
    en = codes_en()
    to = n.created.max()[:10]
    return {"to": to, "toWeek": week(to), "ncs": ncs, "defs": defs, "dic": dic,
            "codes": {c: tidy(fr.get(c, ""), 90) for c in dic["code"] if c},
            "codesEn": {c: en[c] for c in dic["code"] if c in en},   # the English page (2 Nov)
            "vol": weekly_volume(), "msnEnd": msn_end(), "settings": REF.page_settings()}



def codes_en():
    """English sub-code descriptions for the English page (2 Nov): the official sheet's, as the dashboard (fto2_core.official_subcode)."""
    ref = config.frame("3_souscodes.csv")
    out = {str(c): tidy(d, 90) for c, d in zip(ref.sous_code, ref.object_desc) if not str(c).startswith("(") and tidy(d, 90)}
    out.update({"Q11 (composant)": "Component (sub-code not specified)", "Non codé": "No code"})
    out.update({str(c)[:3] + " (non précisé)": "Sub-code not specified" for c in ref.sous_code if not str(c).startswith("(")})
    return out


def plan_products():
    """The production plan's product of an NC, as the dashboard reads it: the product alias rules, then the plan's names
    (04_reference/produits_alias.csv, eqmsn_produits.csv); '' when it is not in the plan. For the alarm on aircraft."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "build"))
    import build_all as B
    ref = config.frame("2_produits_plan.csv")
    plan = {str(a).upper(): B.EQ_NAMES.get(b, b) for a, b in zip(ref.produit_nc, ref.produit_eqmsn)}
    rules = B.product_alias_rules()
    return lambda line, prod, station: plan.get(B.alias_product(rules, set(plan), line, prod or "Other", station).upper(), "")


def msn_end():
    """When each aircraft's build ends (production table, as the dashboard): {line|msn: date}."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "build"))
    import build_all as B
    asof, pm = B.production_msn()
    return {k: v[1] for k, v in (pm or {}).items()}


def weekly_volume():
    """MSN built per line and ISO week of the year followed (working days, as the dashboard: 05_outputs/fto2_msn_semaine.csv from
    build/build_all.py), the alarms' denominator: {line: 53 weeks, week 1 first}. None without the file."""
    path = os.path.join(ROOT, "05_outputs", "fto2_msn_semaine.csv")
    if not os.path.exists(path):
        return None
    t = pd.read_csv(path, encoding="utf-8")
    out = {}
    for r in t[t.niveau == "line"].itertuples():
        out.setdefault(r.nom, [0.0] * 53)[int(r.semaine[-2:]) - 1] = float(r.msn)
    return out


def alarm_parts():
    """The alarm rule and its styles, copied from the dashboard's template so that both pages raise the same alarms."""
    t = open(os.path.join(ROOT, "build", "templates", "dashboard.html"), encoding="utf-8").read()
    cut = lambda a, b: t[t.index(a):t.index(b) + len(b)]
    return (cut("/* ===== ALARM ENGINE START ===== */", "/* ===== ALARM ENGINE END ===== */"),
            cut("/* ===== ALARM CSS START ===== */", "/* ===== ALARM CSS END ===== */"))


def seed_actions():
    """The MFT actions (config/1_actions_mft.csv) in the page's own shape, each tied to the problem it targets."""
    out = []
    for _, a in config.table("1_actions_mft.csv").iterrows():
        out.append({"id": a["id"], "line": a["ligne"], "category": a["categorie"], "title": a["titre"],
                    "problem": {"level": a["niveau"], "values": a["valeurs"].split("|") if a["valeurs"] else []},
                    "defects": a["defauts"], "rootCause": a["cause_racine"], "analysisOwner": a["porteur_analyse"],
                    "analysisStart": a["debut_analyse"], "analysisStatus": a["statut_analyse"], "action": a["action"],
                    "actionOwner": a["porteur_action"], "actionStart": a["debut_action"], "status": a["statut"],
                    "expected": a["benefices_attendus"], "note": a["note"], "source": a["suivi"],
                    "log": [], "createdBy": "", "createdAt": "2026-10-23"})
    return out

def main():
    D = data()
    seeds = seed_actions()
    with open(os.path.join(ROOT, "05_outputs", "mft_actions_seed.json"), "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=1)
    tpl = open(os.path.join(HERE, "mft_template.html"), encoding="utf-8").read()
    blob = json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    js, css = alarm_parts()
    page = tpl.replace("/*@@DATA@@*/null", blob, 1).replace("/*@@ALARMS@@*/", js, 1).replace("/*@@ALARMCSS@@*/", css, 1)
    assert "@@ALARMS@@" not in page and "@@ALARMCSS@@" not in page
    for out in (os.path.join(ROOT, "03_reports", "FTO2_MFT.html"), os.path.join(ROOT, "build", "artifacts", "FTO2_MFT.html")):
        os.makedirs(os.path.dirname(out), exist_ok=True)   # build/artifacts is not in git
        with open(out, "w", encoding="utf-8") as f:
            f.write(page)
    print("NCs", len(D["ncs"]), "| defect lines", len(D["defs"]), "| data to", D["to"], D["toWeek"], "| tracker actions", len(seeds),
          "| page", round(len(page) / 1024), "KB")
    import sys
    sys.path.insert(0, HERE)
    import build_mft_slate   # the same page for a Slate code sandbox, fed by the level-3 queries: 03_reports/skywise/mft/
    build_mft_slate.build()
    sys.path.insert(0, os.path.join(ROOT, "build"))
    import install_zip   # the Skywise set-up's zip, with this page's new files
    install_zip.write()


if __name__ == "__main__":
    main()
