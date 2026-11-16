"""The settings spreadsheet for Fusion: the tables filled in by hand, one sheet each, with today's values.

    python3 -I build/fusion_sheet.py

Writes 03_reports/skywise/fusion/FTO2 NC Dashboard - Settings.xlsx, to import into Fusion as the spreadsheet
"FTO2 NC Dashboard - Settings". Each sheet is synced to a dataset of its own (the names are on the sheet "Read me"), which
the pipeline reads. The rules and the other technical tables stay as files in config/.
"""
import csv
import os
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config")
OUT = os.path.join(ROOT, "03_reports", "skywise", "fusion", "FTO2 NC Dashboard - Settings.xlsx")

HOQ, CM = "Head of Quality", "Configuration manager"
# sheet, dataset, who fills it, what it holds, when it changes, where today's values come from
SHEETS = [
    ("Year", "fto2_set_year", HOQ, "The year the dashboard follows, and the year it is compared with (empty: the year before).",
     "Each January.", ("1_parametres.csv", None)),
    ("Target and pages", "fto2_set_targets", HOQ, "The cut of the target (0.25 = 25 % fewer NCs per MSN than the comparison year), the weight of July and "
     "August, what the pages show when they open, the target of an MFT action.", "When the target or the review changes.", ("1_reglages_pages.csv", None)),
    ("Cost rates and times", "fto2_set_cost", HOQ, "The hourly rates of production, quality and methods, and the minutes each step of an NC takes.",
     "When a rate or a process time changes.", ("1_cout_parametres.csv", None)),
    ("Blackout days", "fto2_set_blackout", HOQ, "The days the plant is closed (weight 0) or half closed (weight 0.5). One row per period.",
     "Each year, and when a closure is added.", ("1_calendrier_production.csv", None)),
    ("Deliveries last year", "fto2_set_deliveries", HOQ, "Products delivered each month of the comparison year: the base of this year's targets.",
     "Each January, for the year just ended.", ("0_livraisons_2025.csv", None)),
    ("Deliveries per line", "fto2_set_deliveries_lines", HOQ, "Whole aircraft delivered in the comparison year, per line.",
     "Each January.", ("0_livraisons_2025_lignes.csv", None)),
    ("Planned volume", "fto2_set_eqmsn", HOQ, "The planned volume (EqMSN) of each product, month by month, as in the EqMSN sheet.",
     "When the EqMSN sheet is updated.", ("0_eqmsn_mois.csv", None)),
    ("Plant", "fto2_set_plant", HOQ, "The plant followed, and how its code is written in SAP.", "Rarely.", ("2_parametres.csv", ("usine", "usines_maison"))),
    ("Part prices", "fto2_set_part_prices", CM, "The unit price of each part (material number), so that a scrapped or exchanged part is counted in the "
     "cost. The update lists the parts still to price.", "When a price is known or changes.", ("1_prix_pieces.csv", None)),
    ("Cable tracker", "fto2_set_cables", CM, "The cable team's tracker of cable requests, pasted as it is, from its header row.",
     "At each update of the tracker.", ("../06_input_data/cable_team_tracker_A30_NC_cables.csv", None)),
    ("GPS register", "fto2_set_gps", CM, "The GPS register of the year followed, pasted as it is, from its header row.",
     "At each update of the register.", (None, ["N°  NC / AM / AF", "Date SAP"])),
    ("Test list", "fto2_set_test", CM, "The Test team's NC list, pasted as it is, from its header row.",
     "At each update of the list.", (None, ["N° NC", "Dates"])),
]

HEAD_FONT, HEAD_FILL = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1D6B52")
WRAP = Alignment(wrap_text=True, vertical="top")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    sep = ";" if text.splitlines()[0].count(";") >= text.splitlines()[0].count(",") else ","
    return list(csv.reader(text.splitlines(), delimiter=sep))


def cell(v):
    """Numbers as numbers in the month columns; everything else as written (dates, codes, '7=0.6|8=0.6')."""
    s = v.strip()
    if re.fullmatch(r"-?(0|[1-9]\d*)(\.\d+)?", s):
        return float(s) if "." in s else int(s)
    return v


def sheet(wb, title, rows, numeric=False):
    ws = wb.create_sheet(title)
    for r, row in enumerate(rows, 1):
        for c, v in enumerate(row, 1):
            x = ws.cell(row=r, column=c, value=cell(v) if (numeric and r > 1) else v)
            if r == 1:
                x.font, x.fill = HEAD_FONT, HEAD_FILL
    for c in range(1, (max(len(r) for r in rows) if rows else 1) + 1):
        width = max((len(str(r[c - 1])) for r in rows if len(r) >= c), default=8)
        ws.column_dimensions[get_column_letter(c)].width = min(max(10, width + 2), 60)
    ws.freeze_panes = "A2"
    return ws


def main():
    wb = Workbook()
    rm = wb.active
    rm.title = "Read me"
    rm.append(["FTO2 NC Dashboard - Settings"])
    rm["A1"].font = Font(bold=True, size=14)
    rm.append(["The values of the dashboard that people fill in by hand. One sheet per table; keep the first row (the column "
               "names) exactly as it is. Each sheet is synced to the dataset named below, which the update reads. The change shows "
               "on the dashboard after the next update."])
    rm.append([])
    rm.append(["Sheet", "Filled in by", "What it holds", "When it changes", "Dataset"])
    for c in range(1, 6):
        rm.cell(row=4, column=c).font, rm.cell(row=4, column=c).fill = HEAD_FONT, HEAD_FILL
    for title, dataset, who, what, when, _ in SHEETS:
        rm.append([title, who, what, when, dataset])
    for col, w in zip("ABCDE", (24, 22, 80, 30, 26)):
        rm.column_dimensions[col].width = w
    for row in rm.iter_rows(min_row=2):
        for x in row:
            x.alignment = WRAP
    for title, dataset, who, what, when, (src, keep) in SHEETS:
        if src is None:
            sheet(wb, title, [keep])
            continue
        rows = read(os.path.normpath(os.path.join(CONFIG, src)))
        if keep:
            rows = [rows[0]] + [r for r in rows[1:] if r and r[0] in keep]
        sheet(wb, title, rows, numeric=title in ("Deliveries last year", "Deliveries per line", "Planned volume"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print("written:", os.path.relpath(OUT, ROOT), "-", len(SHEETS), "sheets")


if __name__ == "__main__":
    main()
