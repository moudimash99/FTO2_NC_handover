"""The settings kept in Fusion: the tables people fill in by hand (the spreadsheet "FTO2 NC Dashboard - Settings", one sheet
per table, each sheet synced to a dataset of its own), and the lists and the production plan pasted there as they are.

    from fto2 import fusion
    fusion.load(Dataset)      # first: some settings are read as soon as the code is loaded
    from fto2 import skywise

For each dataset below that the run can read (in the notebook: added to the Data panel), its rows replace the table of the
settings folder that it stands for; a dataset that cannot be read leaves that table as it is. The settings folder itself is
not changed: the run works on a copy (FTO2_CONFIG points to it), so the files stay the fallback.

A dataset whose columns are not those of its table is not used: the run says which columns are missing and keeps the file.
Column names are matched without regard to case, accents, spaces and signs, as a sync may write them differently.

The pasted sheets (PASTED: the GPS register, the Test list, the cable tracker, the production plan) hold a whole sheet
pasted as it is, from Google Sheets or from the export, title rows included. A sync names a dataset's columns after the
sheet's first row: with a title above the header, the real header arrives as a row of data. So each one is read as the
sheet it comes from (its column names, then its rows, every cell as text), and its header row is the first of its first
rows (HEADER_ROWS) that holds every column the run reads, matched as above. What is above it is dropped, and so are the
other columns and the empty rows; then the run goes on as with a file. For each of these sheets the run says, among its
first lines, on which row it found the header and how many rows it took. A sheet it cannot use is said loudly, with the
reason, at the start and again at the end of the run (ALERTS), and the previous table is kept.
"""
import csv
import datetime as dt
import difflib
import glob
import os
import re
import shutil
import tempfile
import unicodedata

import pandas as pd

from . import config

# dataset -> the settings table it replaces ({year}: the year of its month columns)
TABLES = {
    "fto2_set_targets": "1_reglages_pages.csv",
    "fto2_set_cost": "1_cout_parametres.csv",
    "fto2_set_blackout": "1_calendrier_production.csv",
    "fto2_set_part_prices": "1_prix_pieces.csv",
}
# dataset -> the name / value table whose lines it replaces, line by line (none today)
LINES = {}
# dataset -> the line of 2_sources.csv that names the file it replaces, the lines of 2_sources.csv that give the column
# names in that file, and the line that gives the lines to skip above the header (0 once the sheet is read: see above)
LISTS = {
    "fto2_set_gps": ("liste_gps", ("liste_gps_colonne_numero", "liste_gps_colonne_date"), "liste_gps_lignes_avant_entete"),
    "fto2_set_test": ("liste_test", ("liste_test_colonne_numero", "liste_test_colonne_date"), "liste_test_lignes_avant_entete"),
    "fto2_set_cables": ("suivi_cables", (), None),
}
# the production plan: the export of the Tableau Avances / Retards, read by fto2/downloads.py as one more export
PLAN = "fto2_set_plan"
PLAN_HEADER = ("S/HS", "Prog", "Produit", "MSN")   # the first cells of the export's header row, side by side
# the sheets pasted whole, as they are: dataset -> the sheet's name
PASTED = {"fto2_set_gps": "GPS register", "fto2_set_test": "Test list", "fto2_set_cables": "Cable tracker",
          PLAN: "Production plan"}
HEADER_ROWS = 30   # a pasted sheet's header row is looked for in its first row (the column names) and the 30 rows under it
SOURCES = "2_sources.csv"
MONTH = re.compile(r"(\d{4})\D?(\d{2})")
ISO_DAY = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?(?:Z|[+-]\d{2}:?\d{2})?")
A_DAY = re.compile(r"(?<!\d)(?:(\d{1,2})[/.](\d{1,2})[/.](\d{4})|(\d{4})-(\d{2})-(\d{2}))(?!\d)")

USED, KEPT = {}, {}   # dataset -> what it replaced / why the file was kept
ALERTS = []           # the pasted sheets the run could not use: said at the start, and again at the end (fto2/skywise.py)


def _key(name):
    """A column name without case, accents, spaces or signs: 'N°  NC / AM / AF' and 'n_nc_am_af' give the same key."""
    t = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^0-9a-z]", "", t)


def _text(v, day_first=False):
    """A cell as the text the settings table would hold: empty for nothing, 41 rather than 41.0, a date as 2026-05-15
    (dd/mm/yyyy in the lists, as the lists are written)."""
    if v is None or v is pd.NaT or (isinstance(v, float) and v != v):
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)):
        return v.strftime("%d/%m/%Y" if day_first else "%Y-%m-%d")
    if isinstance(v, bool):
        return "oui" if v else "non"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return str(v)


def _cell(v):
    """A cell of a pasted sheet as text (_text), a date as 15/05/2026, as the lists and the export write their dates (a sync
    may give a date as 2026-05-15)."""
    t = _text(v, day_first=True)
    m = ISO_DAY.fullmatch(t.strip())
    return "%s/%s/%s" % (m.group(3), m.group(2), m.group(1)) if m else t


def _read(Dataset, name):
    try:
        df = Dataset.get(name).read_table(format="pandas")
    except Exception as e:   # not in the Data panel (AliasNotDefined), not an input of the transform (KeyError)...
        why = str(e).splitlines()[0][:80] if str(e) else type(e).__name__
        given = not (isinstance(e, KeyError) or "AliasNotDefined" in type(e).__name__ + why)
        KEPT[name] = ("not readable (%s)" if given else "not given to the run (%s)") % why
        return None
    if df is None or not len(df.columns) or not len(df.dropna(how="all")):
        KEPT[name] = "empty (nothing under its first row)"   # a sheet with its header only: the file is kept, not emptied
        return None
    return df


def _grid(df):
    """A dataset as the sheet it was synced from: its column names (the sheet's first row), then its rows; every cell as
    text (_cell)."""
    return [[_cell(c) for c in df.columns]] + [[_cell(v) for v in r] for r in df.itertuples(index=False, name=None)]


def _rows(df):
    rows = [[_text(v) for v in r] for r in df.itertuples(index=False, name=None)]
    return [r for r in rows if any(c.strip() for c in r)]


def _write(path, header, rows, sep=";"):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=sep, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def _positions(cells, wanted):
    """{wanted name: index of its cell in a row of names}: the same key first (_key), else the closest key when it is very
    close (a sync that replaced or dropped a sign or an accented letter: 'Date de cr_ation' for 'Date de création'). Short
    names must be exact (three letters or fewer). A wanted name with no match is left out."""
    keys = [_key(c) for c in cells]
    out, used = {}, set()
    for w in wanted:
        same = [i for i, k in enumerate(keys) if k == _key(w) and i not in used]
        if same:
            out[w] = same[0]
            used.add(same[0])
    for w in wanted:
        k = _key(w)
        if w in out or len(k) < 4:
            continue
        score, best = max(((difflib.SequenceMatcher(None, k, keys[i]).ratio(), i) for i in range(len(keys)) if i not in used),
                          default=(0, None), key=lambda x: x[0])
        if score >= 0.85:
            out[w] = best
            used.add(best)
    return out


def _match(columns, wanted):
    """{wanted name: column of the dataset} (_positions)."""
    return {w: columns[i] for w, i in _positions(list(columns), wanted).items()}


def _header(grid, required, optional=(), side_by_side=False):
    """The header row of a pasted sheet (grid: _grid): (its index, {column: index of its cell}) for the first of its first
    rows (HEADER_ROWS) that holds every required column (side_by_side: next to each other, in that order); (None, the
    reason, with the columns not found) when no row does."""
    best, lacks = 0, list(required)
    for i, cells in enumerate(grid[:HEADER_ROWS + 1]):
        found = _positions(cells, list(required) + list(optional))
        if side_by_side and required[0] in found:
            found = {c: j for c, j in found.items() if c not in required or j == found[required[0]] + required.index(c)}
        missing = [c for c in required if c not in found]
        if not missing:
            return i, found
        if len(missing) < len(lacks):
            best, lacks = i, missing
    names = ", ".join(" ".join(c.split()) for c in lacks)
    n = min(len(grid), HEADER_ROWS + 1)
    if len(lacks) == len(required):
        return None, "its header row was not found: none of its first %d rows holds the columns %s" % (n, names)
    return None, ("its header row was not found in its first %d rows: the closest, row %d, lacks the column(s) %s"
                  % (n, best + 1, names))


def _matched(df, wanted, name):
    """df with its columns renamed to `wanted` and in that order; None, with the reason kept, when one is missing."""
    found = _match(list(df.columns), wanted)
    missing = [c for c in wanted if c not in found]
    if missing:
        KEPT[name] = "column(s) missing: %s" % ", ".join(missing)
        return None
    return df[[found[c] for c in wanted]].set_axis(list(wanted), axis=1)


def _table(Dataset, name, target, folder):
    df = _read(Dataset, name)
    if df is None:
        return
    if "{year}" in target:   # the deliveries: the month columns give the year, and the file's name
        months = {c: "%s-%s" % MONTH.fullmatch(str(c).strip()).groups() for c in df.columns if MONTH.fullmatch(str(c).strip())}
        years = {m[:4] for m in months.values()}
        if len(months) != 12 or len(years) != 1:
            KEPT[name] = "it needs the 12 month columns of one year (for example the twelve months of the year before)"
            return
        target = target.format(year=years.pop())
        model = sorted(f for f in os.listdir(folder) if re.fullmatch(r"0_livraisons_\d{4}\.csv", f))
        if not model:
            KEPT[name] = "no 0_livraisons_<year>.csv in the settings to take the other columns from"
            return
        wanted = []
        for c in config._rows(os.path.join(folder, model[-1]), model[-1])[0]:   # the model's columns, its months replaced
            if not MONTH.fullmatch(c):
                wanted.append(c)
            elif not any(MONTH.fullmatch(w) for w in wanted):
                wanted += sorted(months.values())
        df = df.rename(columns=months)
    else:
        p = os.path.join(folder, target)
        if not os.path.exists(p):
            KEPT[name] = "%s is not in the settings folder" % target
            return
        wanted = config._rows(p, target)[0]
    df = _matched(df, wanted, name)
    if df is None:
        return
    rows = _rows(df)
    _write(os.path.join(folder, target), wanted, rows)
    USED[name] = "%s (%d rows)" % (target, len(rows))


def _set_lines(folder, table, values):
    """Replace the value of some lines of a name / value table (nom;valeur;description)."""
    p = os.path.join(folder, table)
    header, rows = config._rows(p, table)
    i, j = header.index("nom"), header.index("valeur")
    for r in rows:
        if r[i].strip() in values:
            r[j] = values[r[i].strip()]
    _write(p, header, rows)


def _lines(Dataset, name, table, folder):
    df = _read(Dataset, name)
    if df is None:
        return
    df = _matched(df, ["nom", "valeur"], name)
    if df is None:
        return
    values = {n.strip(): v for n, v in _rows(df) if n.strip()}
    _, rows = config._rows(os.path.join(folder, table), table)
    unknown = sorted(set(values) - {r[0].strip() for r in rows})
    if unknown:
        KEPT[name] = "line(s) not in %s: %s" % (table, ", ".join(unknown))
        return
    _set_lines(folder, table, values)
    USED[name] = "%s: %s" % (table, ", ".join(sorted(values)))


def _list_columns(name, sources):
    """The columns of a list that the run reads (all required), and others it reads when they are there."""
    from . import downloads, manual_lists
    if name == "fto2_set_cables":
        return list(downloads.TRACKER_COLUMNS), ["Année", "Entité en charge du rattrapage"]
    src, columns, _ = LISTS[name]
    named = [sources[c] for c in columns]   # the NC number and the date, as 2_sources.csv names them
    more = manual_lists.GPS_LIST_COLUMNS if name == "fto2_set_gps" else manual_lists.TEST_LIST_COLUMNS
    return named + list(more), []


def _list(Dataset, name, source, skip, folder, sources):
    """A list pasted as it is: its header row found (_header), the columns the run reads under it, spelt as the run spells
    them, written to a file of the settings folder that 2_sources.csv then names (with no line to skip)."""
    df = _read(Dataset, name)
    if df is None:
        return
    required, optional = _list_columns(name, sources)
    grid = _grid(df)
    head, found = _header(grid, required, optional)
    if head is None:
        KEPT[name] = found
        return
    columns = [c for c in required + optional if c in found]
    rows = [[r[found[c]] for c in columns] for r in grid[head + 1:] if any(x.strip() for x in r)]
    path = os.path.join(folder, "fusion_%s.csv" % name)
    _write(path, columns, rows, sep=",")
    change = {source: path}
    if skip:
        change[skip] = "0"
    _set_lines(folder, SOURCES, change)
    USED[name] = "header on row %d, %d rows" % (head + 1, len(rows))


def _plan(Dataset, folder):
    """The export of the Tableau Avances / Retards pasted as it is: written to the settings folder as one more export, which
    fto2/downloads.py reads after the others (its rows from the header row 'S/HS, Prog, Produit, MSN...'). Its day: a date
    written above the header when there is one, else the day of the run."""
    from . import downloads
    df = _read(Dataset, PLAN)
    if df is None:
        return
    grid = _grid(df)
    head, found = _header(grid, PLAN_HEADER, side_by_side=True)
    if head is None:
        KEPT[PLAN] = found
        return
    s = found[PLAN_HEADER[0]]   # the column of S/HS: the export's columns start there
    rows = [r[s:] for r in grid[head + 1:] if any(x.strip() for x in r[s:])]
    aircraft = sum(1 for r in rows if len(r) > 14 and r[14].strip() == "date prévue du début" and r[3].strip())
    if not aircraft:
        KEPT[PLAN] = ("no aircraft under its header row (row %d): no row 'date prévue du début' in the 15th column of the "
                      "export. Is it the export of the Tableau Avances / Retards?" % (head + 1))
        return
    days = [m for r in grid[:head] for c in r for m in A_DAY.finditer(c)]
    day = None
    for m in days:
        d, mo, y = m.group(1, 2, 3) if m.group(1) else (m.group(6), m.group(5), m.group(4))
        try:
            day = dt.date(int(y), int(mo), int(d)).isoformat()
            break
        except ValueError:
            continue
    said = "the date written above its header" if day else "no date in the sheet: the day of the run"
    day = day or dt.date.today().isoformat()
    _write(os.path.join(folder, downloads.PLAN_SHEET.format(day=day)), list(PLAN_HEADER[:3]) + grid[head][s + 3:], rows, sep=",")
    USED[PLAN] = "header on row %d, %d aircraft and products, export of %s (%s)" % (head + 1, aircraft, downloads._dmy(day), said)


def _instead(name, sources):
    """What the run uses when a pasted sheet is not used: the previous table."""
    pattern = (sources.get("exports_plan" if name == PLAN else LISTS[name][0]) or "").strip()
    if "{annee}" in pattern:
        try:
            pattern = pattern.replace("{annee}", str(config.year()))
        except Exception:   # a year badly written: the run stops on it later, with its message
            pass
    there = sorted(glob.glob(pattern)) if pattern else []
    if name == PLAN:
        return "the plan stays as last read: the table 0_plan_msn.csv" + (
            " and the %d export(s) saved in data/" % len(there) if there else "")
    if name == "fto2_set_cables":
        return "the previous cable requests are kept: " + (
            "the export " + os.path.basename(there[-1]) if there else "the table 0_demandes_cables.csv")
    if there:
        return "the previous list is kept: " + there[-1]
    return "there is no previous list to keep: this run goes without the %s" % PASTED[name]


def load(Dataset, say=print):
    """Take the settings kept in Fusion: copy the settings folder, replace in the copy each table whose dataset can be read,
    and point the run at the copy. Call it before the rest of the code is loaded. Says one line per pasted sheet (PASTED).
    Returns USED."""
    source = os.environ.get("FTO2_FUSION_FROM") or config.folder()   # the folder of files, also on a second run
    os.environ["FTO2_FUSION_FROM"] = source
    work = tempfile.mkdtemp(prefix="fto2_settings_")
    shutil.copytree(source, work, dirs_exist_ok=True)
    USED.clear()
    KEPT.clear()
    del ALERTS[:]
    for name, target in TABLES.items():
        _table(Dataset, name, target, work)
    for name, table in LINES.items():
        _lines(Dataset, name, table, work)
    header, rows = config._rows(os.path.join(work, SOURCES), SOURCES)
    sources = {r[header.index("nom")].strip(): r[header.index("valeur")] for r in rows}
    for name, (src, _, skip) in LISTS.items():
        _list(Dataset, name, src, skip, work, sources)
    _plan(Dataset, work)
    os.environ["FTO2_CONFIG"] = work
    config._PARAMS.clear()
    tables = {k: v for k, v in USED.items() if k not in PASTED}
    if tables:
        say("Settings from Fusion: " + "; ".join("%s -> %s" % kv for kv in tables.items()))
    bad = {k: v for k, v in KEPT.items() if k not in PASTED and not v.startswith(("not given", "not readable", "empty"))}
    for k, v in bad.items():
        say("⚠️ %s not used, %s: the file of the settings folder is used instead" % (k, v))
    for name, sheet in PASTED.items():
        if name in USED:
            say("Fusion sheet %s: %s" % (sheet, USED[name]))
        elif KEPT[name].startswith("not given"):
            if name != PLAN:   # the plan: its exports are files kept with the code, a sheet is optional
                say("Fusion sheet %s: %s; %s" % (sheet, KEPT[name], _instead(name, sources)))
        else:
            instead = _instead(name, sources)
            ALERTS.append("⚠️ Fusion sheet %s NOT USED: %s. %s." % (sheet, KEPT[name], instead[0].upper() + instead[1:]))
            say(ALERTS[-1])
    if not USED and not bad and not ALERTS:
        say("Settings: no Fusion dataset in the Data panel, the files of the settings folder are used")
    return dict(USED)
