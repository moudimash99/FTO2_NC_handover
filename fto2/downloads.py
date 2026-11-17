"""The files the team downloads and saves beside the notebook as they are (data/), read at each run.

    production plan   every export of the Tableau Avances / Retards (CSV)      2_sources.csv, line exports_plan
    cable requests    the export of the cable team's tracker (CSV)             2_sources.csv, line suivi_cables

Nobody fills a table by hand for these: a new download is saved in data/ beside the earlier ones, and the next run reads it.
Each line of 2_sources.csv gives where the files are, with * for any text (data/Avances_Retards*.csv); an empty or missing
line means no file is read, and the table of config/ is used alone.

The production plan is made of every export, oldest first. An aircraft takes its row from the newest export that lists it.
An aircraft the newest export no longer lists keeps its last row if it was delivered by then (its Départ OTA, the real date
or else the planned one, is before that export): the plan remembers the aircraft of the year before, whose deliveries the
targets start from. A row that left the export before its delivery has left the plan. The table config/0_plan_msn.csv is
the plan as it stood when the exports started to be saved in data/: it is read as one more export, at its own date.

The cable requests are those of the newest export of the tracker; without one, the table config/0_demandes_cables.csv.
"""
import csv
import datetime as dt
import glob
import os
import re

import pandas as pd

from . import config, rules

SOURCES = "2_sources.csv"
PLAN_TABLE, CABLE_TABLE = "0_plan_msn.csv", "0_demandes_cables.csv"
MILESTONES = ["impression", "enclenchement", "se", "meca", "inte", "test", "qualite", "depart_ota"]
PLAN_COLUMNS = (["ligne", "produit", "msn", "rang"] + ["prevu_" + m for m in MILESTONES] + ["reel_" + m for m in MILESTONES]
                + ["export_du", "note"])
CABLE_COLUMNS = ["ligne", "semaine", "date", "mois", "trimestre", "nc", "programme", "msn", "entite", "motif", "imputation", "origine",
                 "cause", "cables", "type", "commentaire", "action", "statut"]
CABLE_NUMBER = r"\b\d{4}\s?[-–]\s?\d{4}\b"                                              # e.g. 4411-0298
CABLE_TYPE = r"\b(ADB|AD|DRB|DRC|DR|MLB|KL|VNA|VNB|VNC|WX|MMG|DK)\s?(\d\d)\b"           # e.g. WX26
READ = {}   # what the last call read, for the run's report: {"plan": [...files], "cables": file}


def file_day(path):
    """The day a file was downloaded, 'AAAA-MM-JJ': the date at the end of its name (..._2026-11-03.csv) when it has one,
    else the day the file was saved."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})\.[A-Za-z]+$", os.path.basename(path))
    if m:
        return config.day(m.group(1), os.path.basename(path))
    return dt.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def files(setting):
    """The files a line of 2_sources.csv names, oldest first (file_day, then name)."""
    pattern = config.optional(setting, SOURCES)
    return sorted(glob.glob(pattern), key=lambda p: (file_day(p), os.path.basename(p))) if pattern else []


def _text(path):
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:   # saved from Excel
        return raw.decode("cp1252")


# ---------------------------------------------------------------- the production plan
def _export_rows(path):
    """The rows of an Avances / Retards export under its header line (S/HS, Prog, Produit...)."""
    import io
    text = _text(path)
    sep = ";" if text.count(";") > text.count(",") else ","
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=sep))
    h = next((i for i, r in enumerate(rows) if [c.strip() for c in r[:3]] == ["S/HS", "Prog", "Produit"]), None)
    if h is None:
        raise config.ConfigError("%s: the header line 'S/HS, Prog, Produit' was not found: is it an export of the Tableau "
                                 "Avances / Retards?" % os.path.basename(path))
    return rows[h + 1:]


def _day(s):
    try:
        return dt.datetime.strptime(s.strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return ""


def plan_of_export(path, older=()):
    """One export as plan rows (PLAN_COLUMNS): one row per aircraft (MSN) and product, with the planned and the real date of
    its 8 milestones. An MSN that reads "#N/A" in the export (an Excel error) takes its MSN, and its planned dates that read
    "#N/A", from the older exports, the newest of them first, matched on line, product and rank."""
    names, _ = config.mapping("2_produits_noms_plan.csv", "nom_plan", "nom_affiche")
    bad = lambda v: v.strip() in ("", "#N/A")
    known = {}   # (line, product, rank) -> the planned row of an older export that has its MSN
    for f in sorted(older, key=file_day):
        for r in _export_rows(f):
            if len(r) >= 15 and r[14] == "date prévue du début" and not bad(r[3]):
                known[(r[1].strip(), r[2].strip(), r[4].strip())] = (r, file_day(f))
    asof, out, cur = file_day(path), [], None
    for r in _export_rows(path):
        if len(r) < 15:
            continue
        note = ""
        if r[14] == "date prévue du début" and bad(r[3]):
            o = known.get((r[1].strip(), r[2].strip(), r[4].strip()))
            if o:
                o, when = o
                r = r[:3] + [o[3]] + r[4:5] + [x if not bad(x) else y for x, y in zip(r[5:13], o[5:13])] + r[13:]
                note = "MSN et dates #N/A repris de l'export du %s" % when
        if r[14] == "date prévue du début" and r[3].strip():
            cur = {"ligne": r[1].strip(), "produit": names.get(r[2].strip(), r[2].strip()), "msn": r[3].strip(), "rang": r[4].strip(),
                   "export_du": asof, "note": note}
            cur.update({"prevu_" + m: _day(x) for m, x in zip(MILESTONES, r[5:13])})
            cur.update({"reel_" + m: "" for m in MILESTONES})
            out.append(cur)
        elif r[14] == "date réelle" and cur:
            cur.update({"reel_" + m: _day(x) for m, x in zip(MILESTONES, r[5:13])})
    return pd.DataFrame(out, columns=PLAN_COLUMNS).astype(str)


def merge_plan(layers):
    """The plan from its exports. layers: [(day of the export, its rows)]; applied oldest first (see the top of the file)."""
    table = None
    for asof, rows in sorted(layers, key=lambda x: x[0]):
        if table is None or not len(table):
            table = rows
            continue
        listed = set(zip(rows["ligne"], rows["produit"], rows["msn"]))
        end = table["reel_depart_ota"].where(table["reel_depart_ota"] != "", table["prevu_depart_ota"])
        gone = pd.Series([k not in listed for k in zip(table["ligne"], table["produit"], table["msn"])], index=table.index)
        table = pd.concat([rows, table[gone & (end != "") & (end < asof)]], ignore_index=True)
    return table if table is not None else pd.DataFrame(columns=PLAN_COLUMNS)


_PLAN = {}


def plan():
    """The production plan, one row per aircraft and product (PLAN_COLUMNS, as text): the table of config/ and every export
    saved in data/."""
    exports = files("exports_plan")
    base = config.path(PLAN_TABLE)
    stamp = (config.folder(),) + tuple((p, os.path.getmtime(p), os.path.getsize(p)) for p in ([base] if os.path.exists(base) else []) + exports)
    if _PLAN.get("stamp") != stamp:
        layers = []
        if os.path.exists(base):
            t = config.table(PLAN_TABLE, ["ligne", "produit", "msn", "export_du"])
            for c in PLAN_COLUMNS:
                if c not in t.columns:
                    t[c] = ""
            days = [d for d in t["export_du"] if d]
            layers.append((max(days) if days else "", t[PLAN_COLUMNS]))
        for i, f in enumerate(exports):
            layers.append((file_day(f), plan_of_export(f, exports[:i])))
        _PLAN.update(stamp=stamp, table=merge_plan(layers))
        READ["plan"] = [os.path.basename(f) for f in exports]
    return _PLAN["table"]


# ---------------------------------------------------------------- the cable requests
# any run of spaces, the non-breaking ones included (pandas may search with an engine whose \s does not cover them)
SPACES = "[\\s\u00a0\u2007\u202f]+"

# the columns of the cable team's tracker that the run reads
TRACKER_COLUMNS = ("NC", "Date de création de la NC", "Date de réalisation OF", "Semaine", "Programme", "MSN", "Motifs", "Imputation",
                   "Commentaires analyses", "Action", "Statut")


def cables_of_export(path):
    """The cable team's tracker (CSV export) as request rows (CABLE_COLUMNS): one row per request of the tracker (lines
    without an NC number are skipped), with
      - the creation date (a mistyped date: empty, or not in the year the row is filed under, is replaced by the work-order
        date), month, quarter;
      - the origin, from the imputation (config/2_cables_origines.csv);
      - a proposed cause read in the analysis comment (config/2_regle_cause_cable.csv), else "Inconnu – à analyser";
      - the cable numbers and the first cable type found in the comment.
    The initials of people are left out."""
    import io
    need = TRACKER_COLUMNS
    text = _text(path)
    for sep in (",", ";"):   # a CSV export, or the same saved from a French Excel
        t = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, sep=sep)
        t.columns = [c.replace("\n", " ") for c in t.columns]
        missing = [c for c in need if c not in t.columns]
        if not missing:
            break
    if missing:
        raise config.ConfigError("%s: the column(s) %s are missing: is it an export of the cable team's tracker?"
                                 % (os.path.basename(path), ", ".join(missing)))
    t["ligne"] = range(1, len(t) + 1)
    t = t[t.NC.str.strip() != ""].copy()
    d = pd.to_datetime(t["Date de création de la NC"], dayfirst=True, errors="coerce")
    of = pd.to_datetime(t["Date de réalisation OF"], dayfirst=True, errors="coerce")
    filed = pd.to_numeric(t["Année"], errors="coerce") if "Année" in t.columns else pd.Series(float("nan"), index=t.index)
    bad = d.isna() | (filed.notna() & (d.dt.year != filed))
    d = d.where(~bad, of)
    origins, other = config.mapping("2_cables_origines.csv", "imputation", "origine")
    comment = t["Commentaires analyses"].str.replace(SPACES, " ", regex=True).str.strip()
    entity = next((c for c in t.columns if c.strip() == "Entité en charge du rattrapage"), None)
    out = pd.DataFrame({
        "ligne": t["ligne"], "semaine": t["Semaine"].str.upper(), "date": d.dt.strftime("%Y-%m-%d"), "mois": d.dt.strftime("%Y-%m"),
        "trimestre": "T" + ((d.dt.month - 1) // 3 + 1).astype(str), "nc": t["NC"], "programme": t["Programme"].replace("", "—"),
        "msn": t["MSN"], "entite": t[entity] if entity else "", "motif": t["Motifs"].replace("", "—"),
        "imputation": t["Imputation"], "origine": t["Imputation"].map(origins).fillna(other), "commentaire": comment,
        "action": t["Action"].str.strip(), "statut": t["Statut"].str.strip()})
    out["cause"] = rules.apply(out, config.rule_table("2_regle_cause_cable.csv", set(out.columns)), "2_regle_cause_cable.csv")
    out["cables"] = comment.str.findall(CABLE_NUMBER).map(lambda l: " ".join(sorted({re.sub(r"\s|–", "", x) for x in l})))
    out["type"] = comment.str.upper().str.findall(CABLE_TYPE).map(lambda l: l[0][0] + l[0][1] if l else "")
    return out[CABLE_COLUMNS].astype(str).replace({"nan": "", "None": "", "NaT": ""})


def cables():
    """The cable requests (CABLE_COLUMNS, as text): the newest export of the tracker saved in data/, else the table of
    config/. None without either."""
    exports = files("suivi_cables")
    if exports:
        READ["cables"] = os.path.basename(exports[-1])
        return cables_of_export(exports[-1])
    READ["cables"] = None
    return config.table(CABLE_TABLE) if os.path.exists(config.path(CABLE_TABLE)) else None


def report():
    """What the run read from data/, in two lines for its log."""
    p, c = READ.get("plan"), READ.get("cables")
    table = plan()
    days = [d for d in table["export_du"] if d] if len(table) else []
    return ["production plan: %d aircraft and products, as of %s (%s)" % (
                len(table), max(days) if days else "?",
                "exports read: " + ", ".join(p) if p else "no export in data/: the table config/%s alone" % PLAN_TABLE),
            "cable requests: " + ("from the export %s" % c if c else "no export in data/: the table config/%s" % CABLE_TABLE)]
