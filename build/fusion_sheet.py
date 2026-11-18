"""The settings spreadsheet for Fusion: the tables filled in by hand, one sheet each, with today's values, and the sheets
where the lists and the production plan are pasted whole, as they are (empty but for a note in A1 that says how).

    python3 -I build/fusion_sheet.py

Writes 03_reports/skywise/fusion/FTO2 NC Dashboard - Settings.xlsx, to import into Fusion as the spreadsheet
"FTO2 NC Dashboard - Settings". Each sheet is synced to a dataset of its own (the names are on the sheet "Read me"), which
the pipeline reads. The rules and the other technical tables stay as files in config/.
"""
import csv
import io
import os
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config")
OUT = os.path.join(ROOT, "03_reports", "skywise", "fusion", "FTO2 NC Dashboard - Settings.xlsx")

HOQ, CM = "Head of Quality", "Configuration manager"
# the note in A1 of a sheet pasted whole (the update's header search passes over it: it holds no column name)
NNBSP = " "   # the narrow no-break space of French typography, before : and ;
PASTE = ("Collez ici la feuille entière, telle quelle, à partir de la cellule A1" + NNBSP + ": dans Google Sheets, Ctrl+A puis "
         "Ctrl+C" + NNBSP + "; ici, cliquez sur A1 puis Ctrl+V. Pour une mise à jour, videz d'abord cette feuille (Ctrl+A puis "
         "Suppr). Ne retouchez rien" + NNBSP + ": les lignes de titre et les colonnes en plus sont ignorées.")
PASTE_PLAN = ("Collez ici l'export du Tableau Avances / Retards en entier, tel quel, à partir de la cellule A1" + NNBSP + ": dans "
              "l'export, Ctrl+A puis Ctrl+C" + NNBSP + "; ici, cliquez sur A1 puis Ctrl+V. À chaque nouvel export, videz "
              "d'abord cette feuille (Ctrl+A puis Suppr). Ne retouchez rien" + NNBSP + ": les lignes au-dessus de l'en-tête "
              "sont ignorées.")
# sheet, dataset, who fills it, what it holds, when it changes, where today's values come from (a sheet pasted whole: its note)
SHEETS = [
    ("Target and pages", "fto2_set_targets", HOQ, "The cut of the target (0.25 = 25 % fewer NCs per MSN than the comparison year), what the pages "
     "show when they open, the target of an MFT action.", "When the target or the review changes.", "1_reglages_pages.csv"),
    ("Cost rates and times", "fto2_set_cost", HOQ, "The hourly rates of production, quality and methods, and the minutes each step of an NC takes.",
     "When a rate or a process time changes.", "1_cout_parametres.csv"),
    ("Blackout days", "fto2_set_blackout", HOQ, "The days the plant is closed (weight 0) or half closed (weight 0.5). One row per period.",
     "Each year, and when a closure is added.", "1_calendrier_production.csv"),
    ("Part prices", "fto2_set_part_prices", CM, "The unit price of each part (material number), so that a scrapped or exchanged part is counted in the "
     "cost. The update lists the parts still to price.", "When a price is known or changes.", "1_prix_pieces.csv"),
    ("Cable tracker", "fto2_set_cables", CM, "The cable team's tracker of cable requests: the whole Google sheet, pasted as it is.",
     "At each update of the tracker.", PASTE),
    ("GPS register", "fto2_set_gps", CM, "The GPS register of the year followed: the whole Google sheet, pasted as it is.",
     "At each update of the register.", PASTE),
    ("Test list", "fto2_set_test", CM, "The Test team's NC list: the whole Google sheet, pasted as it is.",
     "At each update of the list.", PASTE),
]

HEAD_FONT, HEAD_FILL = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1D6B52")
WRAP = Alignment(wrap_text=True, vertical="top")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    sep = ";" if text.splitlines()[0].count(";") >= text.splitlines()[0].count(",") else ","
    return list(csv.reader(io.StringIO(text, newline=""), delimiter=sep))   # a text in quotes may hold line breaks


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
    rm.append(["The values of the dashboard that people fill in by hand, one sheet per table. In the first four sheets, keep the "
               "first row (the column names) exactly as it is. The last four are pasted whole, as they are, from cell A1 (in "
               "Google Sheets or in the export: Ctrl+A, Ctrl+C; here: Ctrl+V in A1), after emptying the sheet: the update finds "
               "the header row itself and leaves out the title rows and the columns it does not need. Each sheet is synced to "
               "the dataset named below, which the update reads. The change shows on the dashboard after the next update."])
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
    for title, dataset, who, what, when, src in SHEETS:
        if src in (PASTE, PASTE_PLAN):   # pasted whole: only the note, which the paste covers
            ws = wb.create_sheet(title)
            ws["A1"] = src
            ws["A1"].font = Font(italic=True, color="555555")
            continue
        sheet(wb, title, read(os.path.join(CONFIG, src)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print("written:", os.path.relpath(OUT, ROOT), "-", len(SHEETS), "sheets")


if __name__ == "__main__":
    main()
