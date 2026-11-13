"""Tableau Avances / Retards (CSV export) -> config/1_plan_msn.csv

    python3 -I scripts/plan_depuis_avances_retards.py 06_input_data/Avances_Retards_2026-11-03.csv [older exports...]

One row per aircraft (MSN) and product: line, product, MSN, rank, the planned and the real date of the 8 milestones (Impression,
Enclenchement, SE, MECA, INTE, TEST, QUALITE, Départ OTA), and the export date (taken from the file name _AAAA-MM-JJ.csv).
The backend works out the MSN built per product and month (on working days) from this table.

An MSN that reads "#N/A" in the export (an Excel error) takes its MSN, and its planned dates that read "#N/A", from the older
exports given after the first one (the newest older export wins), matched on line, product and rank.

An aircraft that the export no longer lists because it was delivered (its Départ OTA, real or else planned, is before the new
export) keeps its row, with its last known dates: the table holds more than the export does, and so gives the deliveries of
the year before, which the targets start from. A row that left the export before its Départ OTA has left the plan: it goes.

Rows marked 'manuel' in the table are kept (see fto2/everyday_tables.py): to correct an aircraft by hand, change its dates and
set its source to manuel.
"""
import csv
import datetime as dt
import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from fto2 import config, everyday_tables  # noqa: E402

TABLE = "1_plan_msn.csv"
MILESTONES = ["impression", "enclenchement", "se", "meca", "inte", "test", "qualite", "depart_ota"]
COLUMNS = (["ligne", "produit", "msn", "rang"] + ["prevu_" + m for m in MILESTONES] + ["reel_" + m for m in MILESTONES]
           + ["export_du", "note"])


def export_date(path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})\.csv$", os.path.basename(path))
    if not m:
        sys.exit("%s: the file name must end with its date, e.g. Avances_Retards_2026-11-03.csv" % path)
    return m.group(1)


def plan_rows(path):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    h = next((i for i, r in enumerate(rows) if r[:3] == ["S/HS", "Prog", "Produit"]), None)
    if h is None:
        sys.exit("%s: header 'S/HS, Prog, Produit' not found: is it the Avances / Retards export?" % path)
    return rows[h + 1:]


def day(s):
    try:
        return dt.datetime.strptime(s.strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return ""


def convert(newest, older_files):
    names, _ = config.mapping("2_produits_noms_plan.csv", "nom_plan", "nom_affiche")
    bad = lambda v: v.strip() in ("", "#N/A")
    older = {}   # (line, product, rank) -> planned row of an older export with a real MSN; the newest older export wins
    for f in sorted(older_files, key=export_date):
        for r in plan_rows(f):
            if len(r) >= 15 and r[14] == "date prévue du début" and not bad(r[3]):
                older[(r[1].strip(), r[2].strip(), r[4].strip())] = (r, export_date(f))
    asof = export_date(newest)
    out, cur = [], None
    for r in plan_rows(newest):
        if len(r) < 15:
            continue
        note = ""
        if r[14] == "date prévue du début" and bad(r[3]):
            o = older.get((r[1].strip(), r[2].strip(), r[4].strip()))
            if o:
                o, when = o
                r = r[:3] + [o[3]] + r[4:5] + [x if not bad(x) else y for x, y in zip(r[5:13], o[5:13])] + r[13:]
                note = "MSN et dates #N/A repris de l'export du %s" % when
                print("repaired from the export of %s: %s %s MSN %s" % (when, r[1].strip(), r[2].strip(), o[3].strip()))
        if r[14] == "date prévue du début" and r[3].strip():
            cur = {"ligne": r[1].strip(), "produit": names.get(r[2].strip(), r[2].strip()), "msn": r[3].strip(), "rang": r[4].strip(),
                   "export_du": asof, "note": note}
            cur.update({"prevu_" + m: day(x) for m, x in zip(MILESTONES, r[5:13])})
            cur.update({"reel_" + m: "" for m in MILESTONES})
            out.append(cur)
        elif r[14] == "date réelle" and cur:
            cur.update({"reel_" + m: day(x) for m, x in zip(MILESTONES, r[5:13])})
    return pd.DataFrame(out, columns=COLUMNS)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rows = convert(sys.argv[1], sys.argv[2:])
    asof = export_date(sys.argv[1])
    delivered = lambda r: "" < (r["reel_depart_ota"] or r["prevu_depart_ota"]) < asof   # its build ended before this export
    everyday_tables.write(TABLE, rows, key=["ligne", "produit", "msn", "rang"], keep=["ligne", "produit", "msn"], keep_if=delivered)


if __name__ == "__main__":
    main()
