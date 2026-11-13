"""The reference data the pages need besides the NC and defect tables: the production plan (EqMSN per product and month, each
aircraft's build dates, the volume on working days), the comparison year (2025), the cable team's requests, the MFT actions,
the cost model's settings for "Expliquer le calcul" and the cause tree with its definitions.

Everything is read from config/ and from the NC data, so the laptop build and the Skywise notebook make the same block
(reference_block). REPORT collects counts for the build report.
"""
import datetime as dt
import os
import re

import numpy as np
import pandas as pd

from . import config, core
from .parser import fto2_logic as L

REPORT = {}
S_ = lambda v: "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def say(*a):
    print(*a, flush=True)


def year_2025(raw, station_desc):
    """The comparison year (2025) for the year comparisons: the raw Skywise NCs of that year through the
    pipeline's rules, the parser and the CNQ model, summed per month, scope, phase, line and product; and the 2025 deliveries per
    product (config/1_livraisons_2025.csv, from the Livraisons 2025 sheet)."""
    rules, plan = product_alias_rules(), {str(k).upper() for k in config.frame("2_produits_plan.csv").produit_nc}
    alias = lambda line, prod, station: alias_product(rules, plan, line, prod, station)   # products off the plan put back on their plan product
    rows, info, p = core.year_baseline(raw, station_desc, int(config.parameter("annee_comparaison")), alias)
    out = {"cols": ["month", "scope", "phase", "line", "product", "nc", "def", "defMajor", "cost", "cost2", "cost1", "liab", "costAll"], "rows": rows,
           "from": info["created_from"], "to": info["created_to"], "prod": None, "msn": None}
    out["rcaCols"], out["rca"] = core.year_causes(p, 2025)   # 2025 defects by cause (parser labels), for the 2025 / 2026 cause charts
    n25 = p["nc"][p["nc"].date_creation.astype(str).str.startswith("2025") & (p["nc"].scope == "serie")]
    msn = n25.msn.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.lstrip("0")
    out["byMsn"] = {"%s|%s" % k: int(v) for k, v in n25.assign(m=msn)[msn != ""].groupby(["ligne", "m"]).size().items()}   # 2025 NCs per aircraft: built partly in 2025
    if os.path.exists(config.path("1_livraisons_2025.csv")):
        t = config.frame("1_livraisons_2025.csv")
        months = [c for c in t.columns if c.startswith("2025-")]
        out["prod"] = {EQ_NAMES.get(k, k): [float(v) for v in vals] for k, vals in zip(t.produit_eqmsn, t[months].values)}
        out["months"] = months
        ln = config.frame("1_livraisons_2025_lignes.csv")
        out["msn"] = dict(zip(ln.ligne, ln.msn_entiers_livres_2025.astype(int)))
    s = [r for r in rows if r[1] == "serie" and r[2] == "SERIE"]
    REPORT["y2025"] = dict(info, serie_SERIE={"ncs": sum(r[5] for r in s), "defects": sum(r[6] for r in s), "level3": round(sum(r[8] for r in s), 2)},
                           deliveries=sum(sum(v) for v in (out["prod"] or {}).values()))
    return out




def reference_block(data):
    """What does not come from the two tables: code sheet, MFT actions, cost parameters, production plan, root-cause tree, 2025 (NCs
    summed per month, scope, phase, line and product; deliveries per product), the cable team's requests.
    Written into the page (and into the Slate JS); the examples, quantities and product lines are rebuilt from the tables."""
    cq = {k: v for k, v in data["cnqp"].items() if k != "qty"}
    eq = {k: v for k, v in data["eqmsn"].items() if k != "line"} if data.get("eqmsn") else None
    return {"from": data["meta"]["from"], "codes": data["codes"], "actions": data["actions"], "cnqp": cq, "eqmsn": eq,
            "rca": [dict(o, ex=[]) for o in data["rca"]], "y25": data.get("y25"), "cables": data.get("cables")}




EQ_NAMES, _ = config.mapping("2_produits_noms_plan.csv", "nom_plan", "nom_affiche")   # the production files' product names, as the page shows them


def eqmsn(nc, weekly_csv=None):
    """Production volume for the Production tab: EqMSN per product and month of 2026 (config/1_eqmsn_mois.csv, written from the
    EqMSN Excel file by scripts/eqmsn_depuis_excel.py: the Standard and the Adjusted sheet; "wd": the same counted on working days, see working_day_volume, the page's default), the NC
    product labels it matches (config/2_produits_plan.csv) and each product's line, taken from the NCs. None if the file is
    missing."""
    if not os.path.exists(config.path("1_eqmsn_mois.csv")):
        return None
    t = config.table("1_eqmsn_mois.csv")
    months = sorted(c for c in t.columns if c[:4].isdigit() and c[4] == "-")
    out = {"asof": max(t["export_du"]), "forecastFrom": max(t["prevision_a_partir_de"]), "months": months}
    for version in ("std", "adj"):
        out[version] = {r["produit"]: [float(r[m]) for m in months] for _, r in t[t["version"] == version].iterrows()}
    ref = config.frame("2_produits_plan.csv")
    out["map"] = {str(a).upper(): EQ_NAMES.get(b, b) for a, b in zip(ref.produit_nc, ref.produit_eqmsn)}
    out["toConfirm"] = [EQ_NAMES.get(b, b) for b, c in zip(ref.produit_eqmsn, ref.a_confirmer) if c == "oui"]
    lines = {}
    for lab, line in zip(nc.produit.fillna("").astype(str).str.upper(), nc.ligne.fillna("").astype(str)):
        p = out["map"].get(lab)
        if p and line:
            lines.setdefault(p, {}).setdefault(line, 0)
            lines[p][line] += 1
    out["line"] = {p: (max(lines[p], key=lines[p].get) if p in lines else "") for p in out["std"]}
    out["alias"] = product_alias_rules()
    out["msnAsof"], out["msn"] = production_msn()
    asof, recs = _production_export()
    if asof:
        out["wd"] = working_day_volume(asof, recs)   # the page's default volume (Mohammad, 30 Oct)
        out["wdw"] = working_day_volume(asof, recs, weekly=True)   # the same per week, for the alarms
        rows = [(k, a, "2026-W%02d" % (i + 1), v) for k in ("line", "prod") for a, b in out["wdw"][k].items() for i, v in enumerate(b) if v]
        if weekly_csv:
            pd.DataFrame(rows, columns=["niveau", "nom", "semaine", "msn"]).to_csv(weekly_csv, index=False, encoding="utf-8")
    REPORT["eqmsn"] = {"products": len(out["std"]), "total_std": round(sum(sum(v) for v in out["std"].values()), 2),
                       "total_wd": round(sum(sum(v) for v in out.get("wd", {}).values()), 2),
                       "msn_dates": len(out["msn"] or {}), "msn_asof": out["msnAsof"],
                       "msn_repaired": sorted(set(PRODUCTION_REPAIRED))}   # '#N/A' MSNs filled from an older export
    return out


def product_alias_rules():
    """NC products the production plan does not name, put back on the plan product they belong to (config/2_produits_alias.csv,
    agreed with Mohammad 29 Oct): [line, product regex, station regex or '', plan product]. The first rule that matches wins, and a
    rule applies only to a product that is not itself in the plan. The page applies the same rules to the 2026 NCs (fto2FromTables)."""
    path = config.path("2_produits_alias.csv")
    if not os.path.exists(path):
        return []
    t = config.table("2_produits_alias.csv", ["ligne", "produit_nc", "poste", "produit_cible"])
    return [[r.ligne, r.produit_nc, r.poste, r.produit_cible] for r in t.itertuples()]


def alias_product(rules, plan, line, prod, station):
    """The plan product of an NC product (see product_alias_rules); the product itself when no rule matches."""
    prod = prod or "Other"
    if prod.upper() in plan:
        return prod
    for l, rp, rs, to in rules:
        if l == line and re.search(rp, prod) and (not rs or re.search(rs, station or "", re.I)):
            return to
    return prod


PRODUCTION_REPAIRED = []   # MSNs whose '#N/A' in the Avances / Retards export was filled from an older export
MILESTONES = ["impression", "enclenchement", "se", "meca", "inte", "test", "qualite", "depart_ota"]


def _production_export():
    """The production plan per aircraft (config/1_plan_msn.csv, written from the 'Tableau Avances / Retards' export by
    scripts/plan_depuis_avances_retards.py; rows can be corrected by hand): the export date and one record per MSN and product,
    {line, prod, msn, plan, real} with the 8 milestone dates (Impression, Enclenchement, SE, MECA, INTE, TEST, QUALITE,
    Départ OTA). (None, []) without the table."""
    import datetime as dt
    if not os.path.exists(config.path("1_plan_msn.csv")):
        return None, []
    t = config.table("1_plan_msn.csv")
    day = lambda s: dt.date.fromisoformat(s) if s else None
    dates = [x for x in t["export_du"] if x]
    asof = dt.date.fromisoformat(max(dates)) if dates else None
    recs = [{"line": r["ligne"], "prod": r["produit"], "msn": r["msn"], "plan": [day(r["prevu_" + m]) for m in MILESTONES],
             "real": [day(r["reel_" + m]) for m in MILESTONES]} for _, r in t.iterrows()]
    PRODUCTION_REPAIRED[:] = ["%s %s %s" % (r["ligne"], r["produit"], r["msn"]) for _, r in t.iterrows() if r["note"]]
    return asof, recs


def production_msn():
    """Each aircraft's build dates from the production plan (config/1_plan_msn.csv, from the 'Tableau Avances / Retards' export). Per line|MSN:
    [start, end, products] where start = the first real milestone date (else the planned Impression date) and end = the real OTA
    (else the planned OTA), the earliest start and latest end over the aircraft's products. A real date after the export or more
    than 200 days from its plan is a typo and is ignored. Checked against the export's own 'en cours' flag on 07/10/2026: 130 of
    its 134 MSN in progress are in progress by this rule, and 7 more. The page hatches an aircraft built between start and end
    at the last NC date. Returns (export date, {line|msn: [start, end, products]}), or (None, None) without the file."""
    asof, recs = _production_export()
    if not asof:
        return None, None
    out = {}
    for c in recs:
        real = [x if x and x <= asof and not (p and abs((x - p).days) > 200) else None for x, p in zip(c["real"], c["plan"])]
        s, e = next((x for x in real if x), None) or c["plan"][0], real[7] or c["plan"][7]
        if not s or not e:
            continue
        k = c["line"] + "|" + c["msn"].lstrip("0")
        o = out.get(k)
        out[k] = [min(o[0], s.isoformat()), max(o[1], e.isoformat()), o[2] + [c["prod"]]] if o else [s.isoformat(), e.isoformat(), [c["prod"]]]
    return asof.isoformat(), out


def _french_holidays(year):
    """French public holidays of a year: the fixed ones and Easter Monday, Ascension and Whit Monday."""
    import datetime as dt
    a, (b, c) = year % 19, divmod(year, 100)
    d, e = divmod(b, 4)
    g = (b - (b + 8) // 25 + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    easter = dt.date(year, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)
    return {dt.date(year, mo, da) for mo, da in ((1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25))} | \
           {easter + dt.timedelta(n) for n in (1, 39, 50)}


def working_day_volume(asof, recs, weekly=False):
    """EqMSN per product and month of 2026 counted on the days the plant works. Same MSNs and dates as the EqMSN sheet (each MSN
    = 1.0 from its Impression date to its OTA, the real date else the planned one, the sheet script's date corrections: a real
    date after the export or more than 200 days from its plan is taken with the plan's year when that lands within 30 days of
    the plan, else the plan is used; the span reaches a real milestone entered after the OTA; a second block of the same MSN is
    dropped), but spread over Monday to Friday minus French public holidays, with the closures and quiet weeks of
    04_reference/calendrier_production.csv at their weight (0 or 0.5). July and August 2026 come to about 58 % of a normal month
    for the MIP A350, as its NCs do (Mohammad, 29 Oct); the sheet spreads over every calendar day (83 %). {product: 12 months}.
    weekly=True: the same per ISO week of 2026, by line and by product, for the alarms: {"line": {line: 53 weeks}, "prod": {product:
    53 weeks}}, week 1 first."""
    import datetime as dt
    F = "1_calendrier_production.csv"
    cal = [(dt.date.fromisoformat(config.day(r["debut"], "%s line %d, debut" % (F, i + 2))), dt.date.fromisoformat(config.day(r["fin"], "%s line %d, fin" % (F, i + 2))),
            float(config.number(r["poids"], "%s line %d, poids" % (F, i + 2)))) for i, r in config.table(F, ["debut", "fin", "poids"]).iterrows()]
    hol = set().union(*(_french_holidays(y) for y in range(asof.year - 2, asof.year + 3)))

    def weight(d):
        if d.weekday() >= 5 or d in hol:
            return 0
        return next((w for a, b, w in cal if a <= d <= b), 1)

    def fix(x, p):
        if not x:
            return None
        if x <= asof and (not p or abs((x - p).days) <= 200):
            return x
        try:
            y = x.replace(year=p.year) if p else None
        except ValueError:
            y = None
        return y if y and y <= asof and abs((y - p).days) <= 30 else None
    out, wk, seen = {}, {"line": {}, "prod": {}}, set()
    for c in recs:
        if (c["prod"], c["msn"]) in seen:
            continue
        seen.add((c["prod"], c["msn"]))
        real = [fix(x, p) for x, p in zip(c["real"], c["plan"])]
        known = [x for x in real + c["plan"] if x]
        if not known:
            continue
        s = real[0] or c["plan"][0] or min(known)
        e = max([real[7] or c["plan"][7] or max(known)] + [x for x in real if x])
        if e < s:
            continue
        days = [s + dt.timedelta(n) for n in range((e - s).days + 1)]
        w = [weight(d) for d in days]
        tot = sum(w) or 1
        if not sum(w):
            w[-1] = 1
        m = out.setdefault(c["prod"], [0.0] * 12)
        wl, wp = wk["line"].setdefault(c["line"], [0.0] * 53), wk["prod"].setdefault(c["prod"], [0.0] * 53)
        for d, x in zip(days, w):
            if not x:
                continue
            if d.year == 2026:
                m[d.month - 1] += x / tot
            y, n, _ = d.isocalendar()
            if y == 2026:
                wl[n - 1] += x / tot
                wp[n - 1] += x / tot
    if weekly:
        return {k: {a: [round(v, 3) for v in b] for a, b in g.items()} for k, g in wk.items()}
    return {p: [round(v, 2) for v in m] for p, m in out.items()}


def cable_requests():
    """The cable team's requests for new cables (config/1_demandes_cables.csv, written from the team's tracker by
    scripts/cables_depuis_suivi.py, rows can be corrected by hand). For the Câbles tab, one row per request: [row, week, date, NC,
    programme, MSN, reason, origin, proposed cause, cables, cable type, comment, 1 if it has an action or a status]. None without
    the table."""
    if not os.path.exists(config.path("1_demandes_cables.csv")):
        return None
    t = config.table("1_demandes_cables.csv")
    out = [[int(r["ligne"]), r["semaine"], r["date"], r["nc"], r["programme"], r["msn"], r["motif"], r["origine"], r["cause"], r["cables"],
            r["type"], r["commentaire"], 1 if (r["action"] or r["statut"]) else 0] for _, r in t.iterrows()]
    REPORT["cables"] = {"requests": len(out), "from": min(r[2] for r in out), "to": max(r[2] for r in out)}
    return out

def cnq_explain(d):
    """The CNQ parameters the "explain the calculation" part shows: times and rates, which steps each decision charges,
    minutes and material per defect class, the Airbus standard per decision, and the defect lines counted more than once."""
    from .cost import params as P
    kind = lambda b: "DERIVED" if b.startswith("TEAM RULE") else "RULE" if b.startswith("Rule from AEC") else b.split(" ")[0].upper()
    R = getattr(P, "STEP_RATES", None) or {}
    return {"p": {"rate": P.RATE_STANDARD, "rateEng": P.RATE_ENGINEERING, "rateProd": getattr(P, "RATE_PROD", P.RATE_STANDARD),
                  "rates": {"alert": R.get("alert"), "writing": R.get("writing"), "support": R.get("support"), "setup": R.get("setup"),
                            "hands": R.get("hands_on"), "recheck": R.get("recheck")} if R else None, "alert": P.MIN_ALERT, "write": P.MIN_WRITE_NC, "writeFinal": P.MIN_WRITE_NC_FINAL,
                  "logistics": getattr(P, "MIN_LOGISTICS", 0),
                  "support": P.MIN_SUPPORT, "setup": P.MIN_SETUP, "floor": P.MIN_WORK_FLOOR, "recheck": P.MIN_RECHECK_CLOSE,
                  "noDefect": P.MIN_HANDS_ON_NO_DEFECT, "writeGlobal": P.MIN_WRITE_NC_GLOBAL, "workGlobal": P.MIN_WORK_GLOBAL,
                  "defDefault": P.MIN_DEFAULT_DEFECT, "crExtra": P.CUSTOMER_RETURN_EXTRA, "version": P.MODEL_VERSION,
                  "connNext": P.MIN_CONNECTION_NEXT, "connCls": list(P.CONNECTION_CLASSES), "intTypes": list(P.INTERNAL_TYPES),
                  "intFactor": P.INTERNAL_WORK_FACTOR, "noAlert": list(P.NO_ALERT_TYPES), "orderTime": bool(getattr(P, "USE_ORDER_TIME", False)),
                  "aleaTime": bool(getattr(P, "USE_ALEA_TIME", False)), "aleaHours": list(getattr(P, "ALEA_LINK_HOURS", (-2, 72)))},
            "rules": {k: list(v[:8]) + [kind(v[8])] for k, v in P.RULES.items()},
            "cls": {k: [v[0], v[1], v[2], kind(v[4])] for k, v in P.DEFECT_TIMES.items()},
            "airbus": P.AIRBUS_STANDARD,
            "qty": {"%s|%d" % (r.notification_number, r.seq): int(r.qty) for r in d.itertuples() if pd.notna(r.qty) and int(r.qty) != 1}}


def mft_actions():
    """Actions of the MFT trackers (config/1_actions_mft.csv), each tied to the problem it targets; actions with no problem are
    left out: [line, label fr, label en, level, values, analysis month, action month, status, expected benefit month, defects
    text, root cause, action]."""
    month = lambda d: d[:7] if re.match(r"^\d{4}-\d{2}-\d{2}$", d) else ""
    out = []
    for _, a in config.table("1_actions_mft.csv").iterrows():
        if not a["niveau"]:
            continue
        out.append([a["ligne"], a["titre"], a["titre_en"], a["niveau"], a["valeurs"].split("|"), month(a["debut_analyse"]),
                    month(a["debut_action"]), (a["statut_suivi"] if a["source"] == "auto" else a["statut"])[:400], month(a["benefices_attendus"]),
                    a["defauts"][:400], a["cause_racine"][:400], a["action"][:400]])
    REPORT["mft_actions"] = len(out)
    return out


def rca_reference(d, code_desc):
    """The RCA page: hierarchy official sub-code -> sub-category -> RCA -> category, definitions, real examples."""
    sc = config.frame("3_sous_categories.csv")
    codes = config.frame("3_souscodes.csv")
    codes = codes[~codes.sous_code.astype(str).str.startswith("(")]
    defs = config.frame("2_causes_definitions.csv").set_index("rca_nom")
    pool = d[(d.scope != "") & (d.llm_status == "ok") & (d.llm_confiance == "high") & d.text.fillna("").str.len().between(30, 170)]
    pool = pool.sort_values("date_creation", ascending=False)
    out = []
    for rca_nom, g in sc.groupby("rca_nom", sort=False):
        subs = []
        for s in g.itertuples():
            cc = codes[codes.sous_categorie == s.sous_categorie]
            subs.append({"name": s.sous_categorie, "minor": s.mineur == "oui", "note": S_(s.note),
                         "codes": [[c.sous_code, code_desc.get(c.sous_code, [c.object_desc, c.object_desc])[0], code_desc.get(c.sous_code, [c.object_desc, c.object_desc])[1]] for c in cc.itertuples()]})
        ex = pool[pool.llm_rca_nom == rca_nom].drop_duplicates("notification_number").head(3)
        df_ = defs.loc[rca_nom] if rca_nom in defs.index else None
        out.append({"rca": rca_nom, "cat": g.categorie.iloc[0], "fr": "" if df_ is None else df_.definition_fr, "en": "" if df_ is None else df_.definition_en,
                    "subs": subs, "ex": [[e.notification_number, " ".join(str(e.text).split()).strip(" *:-")] for e in ex.itertuples()]})
    REPORT["rca_without_definition"] = [o["rca"] for o in out if not o["fr"]]
    return out




# ---------------------------------------------------------------- the blocks the pages read
def _tidy(s, n=320):
    if s is None or (isinstance(s, float) and s != s):   # empty cells read as NaN
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()[:n]


def weekly_volume(eq):
    """MSN built per line and ISO week (working days), the alarms' denominator: {line: 53 weeks, week 1 first}."""
    if not eq or not eq.get("wdw"):
        return None
    out = {}
    for line, weeks in eq["wdw"]["line"].items():
        v = [0.0] * 53
        for i, x in enumerate(weeks[:53]):
            v[i] = float(x)
        out[line] = v
    return out


def codes_en():
    """English sub-code descriptions (the official sheet's), as the dashboard."""
    ref = config.frame("3_souscodes.csv")
    out = {str(c): _tidy(d, 90) for c, d in zip(ref.sous_code, ref.object_desc) if not str(c).startswith("(") and _tidy(d, 90)}
    out.update({"Q11 (composant)": "Component (sub-code not specified)", "Non codé": "No code"})
    out.update({str(c)[:3] + " (non précisé)": "Sub-code not specified" for c in ref.sous_code if not str(c).startswith("(")})
    return out


def mft_actions_page():
    """The MFT actions (config/1_actions_mft.csv) in the MFT page's shape, each tied to the problem it targets."""
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


def mft_block(eq):
    """What the MFT page needs besides the two tables."""
    t = config.frame("2_produits_plan.csv")
    fr = config.frame("3_souscodes_fr.csv").set_index("sous_code").description_fr.to_dict()
    asof, pm = production_msn()
    return {"plan": {str(a).upper(): EQ_NAMES.get(b, b) for a, b in zip(t.produit_nc, t.produit_eqmsn)}, "alias": product_alias_rules(),
            "codes": {str(k): _tidy(v, 90) for k, v in fr.items() if _tidy(v, 90)}, "codesEn": codes_en(), "vol": weekly_volume(eq),
            "msnEnd": {k: v[1] for k, v in (pm or {}).items()}, "actions": mft_actions_page(), "settings": page_settings()}


def dashboard_block(d, nc, code_desc, y25):
    """What the dashboard needs besides the NC, defect and aléa tables (the examples, quantities and product lines are rebuilt
    from the tables by the page)."""
    cq = {k: v for k, v in cnq_explain(d).items() if k != "qty"}
    eq = eqmsn(nc)
    return {"from": config.parameter_day("date_debut"), "codes": code_desc, "actions": mft_actions(), "cnqp": cq,
            "eqmsn": {k: v for k, v in eq.items() if k != "line"} if eq else None,
            "rca": [dict(o, ex=[]) for o in rca_reference(d, code_desc)], "y25": y25, "cables": cable_requests(),
            "settings": page_settings()}


CHUNK = 30000   # characters per row of the reference table: long texts are cut into rows that any database keeps


def ref_table(blocks):
    """The reference blocks as a table for Skywise (dataset fto2_dash_ref): one row per piece of text, columns
    partie (dashboard, mft, elizabeth), morceau (0, 1, 2... in order) and texte (JSON). The pages join the pieces back."""
    import json
    rows = []
    for part, block in blocks.items():
        text = json.dumps(block, ensure_ascii=False, separators=(",", ":"))
        for i in range(0, max(len(text), 1), CHUNK):
            rows.append({"partie": part, "morceau": i // CHUNK, "texte": text[i:i + CHUNK]})
    return pd.DataFrame(rows, columns=["partie", "morceau", "texte"])


def _num(v, where):
    try:
        f = float(str(v).replace(",", "."))
    except ValueError:
        raise config.ConfigError("%s: '%s' is not a number" % (where, v))
    return int(f) if f.is_integer() and "." not in str(v) and "," not in str(v) else f


def page_settings():
    """The settings the pages use (config/2_reglages_pages.csv, 2_categories.csv, 2_lignes.csv, 3_alarmes.csv)."""
    F = "2_reglages_pages.csv"
    get = lambda k: config.parameter(k, F)
    weights = {}
    for item in config.parameter_list("poids_mois", F):
        m, w = item.split("=")
        weights[str(int(m))] = _num(w, F + ", poids_mois")
    cats = config.table("2_categories.csv", ["categorie", "ordre", "couleur", "a_part"])
    cats = sorted(cats.to_dict("records"), key=lambda r: _num(r["ordre"], "2_categories.csv, ordre"))
    lines = config.table("2_lignes.csv", ["ligne", "couleur"])
    alarms = config.table("3_alarmes.csv", ["nom", "valeur"])
    windows = {}
    for item in config.parameter_list("mft_fenetres", F):
        a, b = item.split("=")
        windows[str(int(a))] = int(b)
    n = lambda k: _num(get(k), F + ", " + k)
    return {"objectif_baisse": n("objectif_baisse"), "objectif_coef": round(1 - n("objectif_baisse"), 12), "poids_mois": weights,
            "semaine_faible": n("semaine_faible_moins_de"), "mft_fenetres": windows,
            "mft_hausse_min": n("mft_hausse_min_defauts"), "mft_hausse_facteur": n("mft_hausse_facteur"),
            "mft_baisse_min": n("mft_baisse_min_base"), "mft_baisse_facteur": n("mft_baisse_facteur"), "mft_fin_min": n("mft_fin_min_avions"),
            "action_baisse": n("action_objectif_baisse"), "action_coef": round(1 - n("action_objectif_baisse"), 12),
            "action_semaines": n("action_semaines_tenues"), "action_tendance": n("action_seuil_tendance"),
            "semaine_fermeture": _num(get("semaine_fermeture_moins_de"), F), "msn_minimum": _num(get("msn_minimum"), F),
            "placeholder": config.parameter("souscodes_non_precis", F, keep_spaces=True).strip(),
            "defauts": {"phase": get("defaut_phase"), "liab": get("defaut_responsabilite"), "preset": get("defaut_periode")},
            "categories": [{"nom": r["categorie"], "couleur": int(r["couleur"]) if r["couleur"].strip() else None,
                            "a_part": r["a_part"].strip().lower() == "oui"} for r in cats],
            "lignes": {r["ligne"]: int(r["couleur"]) for _, r in lines.iterrows()},
            "alarmes": {r["nom"].strip(): _num(r["valeur"], "3_alarmes.csv, " + r["nom"]) for _, r in alarms.iterrows()}}
