"""EqMSN Excel file (sheets Standard and Adjusted) -> config/1_eqmsn_mois.csv

    python3 -I scripts/eqmsn_depuis_excel.py 06_input_data/EqMSN_2026.xlsx 2026-10-07 2026-10

Arguments: the file, the date of the export (AAAA-MM-JJ) and the first month that is a forecast (AAAA-MM, see the Notes sheet).
One row per product and version (std = Standard sheet, adj = Adjusted sheet) with its EqMSN for each month of the year.
Rows marked 'manuel' in the table are kept (see fto2/everyday_tables.py).
"""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from fto2 import config, everyday_tables  # noqa: E402

TABLE = "1_eqmsn_mois.csv"


def convert(path, export_du, forecast_from):
    import openpyxl
    names, _ = config.mapping("2_produits_noms_plan.csv", "nom_plan", "nom_affiche")
    year = export_du[:4]
    months = ["%s-%02d" % (year, m) for m in range(1, 13)]
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    for sheet, version in (("Standard", "std"), ("Adjusted", "adj")):
        start = False
        for r in wb[sheet].iter_rows(values_only=True):
            if r[0] == "Produit":
                start = True
                continue
            if not start or r[0] in (None, "Total"):
                if start and r[0] == "Total":
                    break
                continue
            row = {"produit": names.get(str(r[0]), str(r[0])), "version": version}
            row.update({m: round(float(v or 0), 2) for m, v in zip(months, r[1:13])})
            row.update({"export_du": export_du, "prevision_a_partir_de": forecast_from})
            out.append(row)
    return pd.DataFrame(out, columns=["produit", "version"] + months + ["export_du", "prevision_a_partir_de"])


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    rows = convert(*sys.argv[1:])
    everyday_tables.write(TABLE, rows, key=["produit", "version"])


if __name__ == "__main__":
    main()
