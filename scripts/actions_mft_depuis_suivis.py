"""MFT action trackers (CSV exports, one per line) -> config/1_actions_mft.csv

    python3 -I scripts/actions_mft_depuis_suivis.py A330=06_input_data/MFT_actions_A330.csv A350=06_input_data/MFT_actions_A350.csv

One row per action. Each action is tied to the problem it targets with config/2_actions_mft_problemes.csv (line, the tracker's
NC category, the start of its defects text -> level and values: a cause, a category...). An action that matches no row of that
table gets no problem (niveau and valeurs empty): the dashboard leaves it out, the MFT page shows it.

Dates are written AAAA-MM-JJ ('juin 2026' -> 2026-06-01). After this first import, actions are added and updated by hand in the
table (source = manuel): the trackers' CSV files are only the starting point.
"""
import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from fto2 import config, everyday_tables  # noqa: E402

TABLE = "1_actions_mft.csv"
FR_MONTHS = {"janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
             "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12}
COLUMNS = ["id", "ligne", "categorie", "titre", "titre_en", "niveau", "valeurs", "defauts", "cause_racine", "porteur_analyse",
           "debut_analyse", "statut_analyse", "action", "porteur_action", "debut_action", "statut", "statut_suivi",
           "benefices_attendus", "note", "suivi"]


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
    return s[:1].upper() + s[1:]


def convert(trackers):
    mp = config.table("2_actions_mft_problemes.csv", ["programme", "nc_category", "defauts_debut", "niveau", "valeur", "libelle_fr", "libelle_en"])
    out = []
    for line, path in trackers:
        t = pd.read_csv(path, skiprows=2, dtype=str).dropna(how="all")
        two = "Statut.1" in t.columns   # A350: analysis status, then action status; A330: one status, the action's
        for k, a in enumerate(t.itertuples(index=False)):
            a = dict(zip(t.columns, a))
            cat, dft = tidy(a.get("NC Category (Type)")), tidy(a.get("Défauts"), 1200)
            m = mp[(mp.programme == line) & (mp.nc_category.str.strip() == cat) & mp.defauts_debut.map(lambda p: dft.startswith(p))]
            st_raw = a.get("Statut.1") if two else a.get("Statut")
            out.append({"id": "trk-%s-%d" % (line.lower(), k + 1), "ligne": line, "categorie": cat,
                        "titre": m.iloc[0].libelle_fr if not m.empty else cat, "titre_en": m.iloc[0].libelle_en if not m.empty else "",
                        "niveau": m.iloc[0].niveau if not m.empty else "", "valeurs": m.iloc[0].valeur if not m.empty else "",
                        "defauts": dft, "cause_racine": tidy(a.get("Analyse de cause racine"), 2000),
                        "porteur_analyse": tidy(a.get("Porteur de l'analyse")), "debut_analyse": month_day(a.get("Début de l'analyse")),
                        "statut_analyse": status(a.get("Statut")) if two else "", "action": tidy(a.get("Action"), 2000),
                        "porteur_action": tidy(a.get("Porteur de l'action")), "debut_action": month_day(a.get("Début de l'action")),
                        "statut": status(st_raw) or status(a.get("Statut")) or "En cours", "statut_suivi": tidy(st_raw, 400),
                        "benefices_attendus": month_day(a.get("Quand (bénéfices estimés)")) or tidy(a.get("Quand (bénéfices estimés)")),
                        "note": tidy(a.get("Informations complémentaires"), 600), "suivi": "Tracker MFT %s" % line})
            if m.empty:
                print("no problem found for: %s | %s | %s" % (line, cat, dft[:50]))
    return pd.DataFrame(out, columns=COLUMNS)


def main():
    pairs = [a.split("=", 1) for a in sys.argv[1:]]
    if not pairs or any(len(p) != 2 for p in pairs):
        sys.exit(__doc__)
    everyday_tables.write(TABLE, convert(pairs), key=["id"])


if __name__ == "__main__":
    main()
