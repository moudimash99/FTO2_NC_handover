"""MFT page for the weekly QLS review: one line at a time, the week's Pareto, a short analysis and the action follow-up.

Reads the dashboard's two tables (05_outputs/fto2_dash_nc.csv, fto2_dash_defects.csv) and the A330 / A350 MFT trackers
(06_input_data/MFT_actions_*.csv, tied to the problem each action targets by 04_reference/mft_actions_mapping.csv).
Writes 03_reports/FTO2_MFT.html (and build/artifacts/FTO2_MFT.html) from 07_scripts/mft/mft_template.html, and the
tracker actions as 05_outputs/mft_actions_seed.json: the page keeps its actions in its own store (seeded once from that
file); the page itself carries no action.

Scope as the dashboard's default: NCs raised at FTO2 (plant FTO2 or FT02), created in 2026; the phase is a filter in
the page (Série by default).

    python3 -I 07_scripts/mft/build_mft.py
"""
import datetime as dt
import json
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
FR_MONTHS = {"janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
             "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12}


def week(d):
    y, w, _ = dt.date.fromisoformat(d[:10]).isocalendar()
    return "%d-W%02d" % (y, w)


def tidy(s, n=320):
    if s is None or (isinstance(s, float) and s != s):   # empty cells read as NaN
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()[:n]


def month_day(s):
    """'février 2026' -> '2026-02-01'; '' when no month is written."""
    m = re.search(r"([A-Za-zÀ-ÿ]+)\s+(20\d\d)", str(s or ""))
    if not m or m.group(1).lower() not in FR_MONTHS:
        return ""
    return "%s-%02d-01" % (m.group(2), FR_MONTHS[m.group(1).lower()])


def status(s):
    s = tidy(s).lower()
    if not s:
        return ""
    if s.startswith("clos") or s.startswith("ferm") or s.startswith("termin"):
        return "Clos"
    if s in ("e/c", "ec") or s.startswith("en cours"):
        return "En cours"
    return "À lancer" if s.startswith("à lancer") or s.startswith("a lancer") else tidy(s).capitalize()


def data():
    n = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_nc.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    d = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_defects.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    n = n[n.plant.str.strip().str.upper().isin(["FTO2", "FT02"]) & (n.created >= "2026-01-01")].sort_values("created")
    dic = {k: [] for k in ("line", "phase", "msn", "station", "where", "cat", "rca", "sub", "code", "fin")}
    idx = {k: {} for k in dic}

    def code(k, v):
        v = tidy(v, 120)
        if v not in idx[k]:
            idx[k][v] = len(dic[k])
            dic[k].append(v)
        return idx[k][v]

    ncs, pos = [], {}
    for r in n.itertuples():
        pos[r.nc] = len(ncs)   # [nc, date, line, phase, msn, station, where found]
        ncs.append([r.nc, r.created[:10], code("line", r.line or "—"), code("phase", r.phase), code("msn", r.msn), code("station", r.station),
                    code("where", r.where_found)])
    defs = []
    for r in d.itertuples():
        i = pos.get(r.nc)
        if i is None:
            continue   # [NC index, category, cause, sub-category, sub-code, FIN, minor, text]
        defs.append([i, code("cat", r.cat), code("rca", r.rca), code("sub", r.sub), code("code", r.subcode), code("fin", r.fin), int(r.minor or 0), tidy(r.text)])
    fr = pd.read_csv(os.path.join(ROOT, "04_reference", "souscodes_fr.csv"), encoding="utf-8-sig").set_index("sous_code").description_fr.to_dict()
    to = n.created.max()[:10]
    return {"to": to, "toWeek": week(to), "ncs": ncs, "defs": defs, "dic": dic,
            "codes": {c: tidy(fr.get(c, ""), 90) for c in dic["code"] if c}, "vol": weekly_volume()}


def weekly_volume():
    """MSN built per line and ISO week of 2026 (working days, as the dashboard: 05_outputs/fto2_msn_semaine.csv from
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
    """The trackers' actions in the page's own shape, each tied to the problem it targets."""
    mp = pd.read_csv(os.path.join(ROOT, "04_reference", "mft_actions_mapping.csv"), encoding="utf-8-sig", dtype=str)
    out = []
    for line in ("A330", "A350"):
        t = pd.read_csv(os.path.join(ROOT, "06_input_data", "MFT_actions_%s.csv" % line), skiprows=2, dtype=str).dropna(how="all")
        two = "Statut.1" in t.columns   # A350: analysis status, then action status; A330: one status, the action's
        for k, a in enumerate(t.itertuples(index=False)):
            a = dict(zip(t.columns, a))
            cat, dft = tidy(a.get("NC Category (Type)")), tidy(a.get("Défauts"), 1200)
            m = mp[(mp.programme == line) & (mp.nc_category.str.strip() == cat) & mp.defauts_debut.map(lambda p: dft.startswith(p))]
            prob = {"level": m.iloc[0].niveau, "values": m.iloc[0].valeur.split("|")} if not m.empty else {"level": "", "values": []}
            st = status(a.get("Statut.1") if two else a.get("Statut")) or status(a.get("Statut"))
            out.append({"id": "trk-%s-%d" % (line.lower(), k + 1), "line": line, "category": cat, "title": m.iloc[0].libelle_fr if not m.empty else cat,
                        "problem": prob, "defects": dft, "rootCause": tidy(a.get("Analyse de cause racine"), 2000),
                        "analysisOwner": tidy(a.get("Porteur de l'analyse")), "analysisStart": month_day(a.get("Début de l'analyse")),
                        "analysisStatus": status(a.get("Statut")) if two else "", "action": tidy(a.get("Action"), 2000),
                        "actionOwner": tidy(a.get("Porteur de l'action")), "actionStart": month_day(a.get("Début de l'action")),
                        "status": st or "En cours", "expected": month_day(a.get("Quand (bénéfices estimés)")) or tidy(a.get("Quand (bénéfices estimés)")),
                        "note": tidy(a.get("Informations complémentaires"), 600), "source": "Tracker MFT %s" % line,
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


if __name__ == "__main__":
    main()
