"""Suivi des câbles (the cable team's tracker, CSV export) -> config/1_demandes_cables.csv

    python3 -I scripts/cables_depuis_suivi.py "06_input_data/cable_team_tracker_A30_NC_cables.csv"

One row per request of the tracker (lines without an NC number are skipped), with:
  - the creation date (a mistyped date, empty or not in the tracker's year, is replaced by the work-order date), month, quarter;
  - the origin, from the imputation (config/2_cables_origines.csv);
  - a proposed cause read in the analysis comment (config/2_regle_cause_cable.csv), else "Inconnu – à analyser";
  - the cable numbers and the first cable type found in the comment.
The TSFS initials (people) are left out. Rows marked 'manuel' in the table are kept (see fto2/everyday_tables.py).
"""
import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from fto2 import config, everyday_tables, rules  # noqa: E402

TABLE = "1_demandes_cables.csv"
CABLE_NUMBER = r"\b\d{4}\s?[-–]\s?\d{4}\b"                                              # e.g. 4411-0298
CABLE_TYPE = r"\b(ADB|AD|DRB|DRC|DR|MLB|KL|VNA|VNB|VNC|WX|MMG|DK)\s?(\d\d)\b"           # e.g. WX26


def convert(path):
    t = pd.read_csv(path, dtype=str, keep_default_na=False)
    t.columns = [c.replace("\n", " ") for c in t.columns]
    t["ligne"] = range(1, len(t) + 1)
    t = t[t.NC.str.strip() != ""].copy()
    d = pd.to_datetime(t["Date de création de la NC"], dayfirst=True, errors="coerce")
    of = pd.to_datetime(t["Date de réalisation OF"], dayfirst=True, errors="coerce")
    bad = d.isna() | (d.dt.year != config.year())   # a creation date outside the year followed is a typing mistake
    d = d.where(~bad, of)
    print("dates replaced by the work-order date:", int(bad.sum()))
    origins, other = config.mapping("2_cables_origines.csv", "imputation", "origine")
    comment = t["Commentaires analyses"].str.replace(r"\s+", " ", regex=True).str.strip()
    out = pd.DataFrame({
        "ligne": t["ligne"], "semaine": t["Semaine"].str.upper(), "date": d.dt.strftime("%Y-%m-%d"), "mois": d.dt.strftime("%Y-%m"),
        "trimestre": "T" + ((d.dt.month - 1) // 3 + 1).astype(str), "nc": t["NC"], "programme": t["Programme"].replace("", "—"),
        "msn": t["MSN"], "entite": t["Entité en charge du rattrapage "], "motif": t["Motifs"].replace("", "—"),
        "imputation": t["Imputation"], "origine": t["Imputation"].map(origins).fillna(other), "commentaire": comment,
        "action": t["Action"].str.strip(), "statut": t["Statut"].str.strip()})
    out["cause"] = rules.apply(out, config.rule_table("2_regle_cause_cable.csv", set(out.columns)), "2_regle_cause_cable.csv")
    out["cables"] = comment.str.findall(CABLE_NUMBER).map(lambda l: " ".join(sorted({re.sub(r"\s|–", "", x) for x in l})))
    out["type"] = comment.str.upper().str.findall(CABLE_TYPE).map(lambda l: l[0][0] + l[0][1] if l else "")
    cols = ["ligne", "semaine", "date", "mois", "trimestre", "nc", "programme", "msn", "entite", "motif", "imputation", "origine",
            "cause", "cables", "type", "commentaire", "action", "statut"]
    return out[cols]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    rows = convert(sys.argv[1])
    everyday_tables.write(TABLE, rows, key=["ligne", "nc"])
    print((rows.cause != "Inconnu – à analyser").sum(), "requests with a proposed cause")


if __name__ == "__main__":
    main()
