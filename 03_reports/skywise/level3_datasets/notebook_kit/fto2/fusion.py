"""The settings kept in Fusion: the tables people fill in by hand (the spreadsheet "FTO2 NC Dashboard - Settings", one sheet
per table, each sheet synced to a dataset of its own).

    from fto2 import fusion
    fusion.load(Dataset)      # first: some settings are read as soon as the code is loaded
    from fto2 import skywise

For each dataset below that the run can read (in the notebook: added to the Data panel), its rows replace the table of the
settings folder that it stands for; a dataset that cannot be read leaves that table as it is. The settings folder itself is
not changed: the run works on a copy (FTO2_CONFIG points to it), so the files stay the fallback.

A dataset whose columns are not those of its table is not used: the run says which columns are missing and keeps the file.
Column names are matched without regard to case, accents, spaces and signs, as a sync may write them differently.
"""
import csv
import datetime as dt
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
    "fto2_set_deliveries": "0_livraisons_{year}.csv",
    "fto2_set_eqmsn": "0_eqmsn_mois.csv",
    "fto2_set_part_prices": "1_prix_pieces.csv",
}
# dataset -> the name / value table whose lines it replaces, line by line
LINES = {"fto2_set_plant": "2_parametres.csv"}
# dataset -> the line of 2_sources.csv that names the file it replaces, and the lines of 2_sources.csv that give the
# column names in that file (a list is pasted from its header row: no line to skip)
LISTS = {
    "fto2_set_gps": ("liste_gps", ("liste_gps_colonne_numero", "liste_gps_colonne_date"), "liste_gps_lignes_avant_entete"),
    "fto2_set_test": ("liste_test", ("liste_test_colonne_numero", "liste_test_colonne_date"), "liste_test_lignes_avant_entete"),
    "fto2_set_cables": ("suivi_cables", (), None),
}
SOURCES = "2_sources.csv"
MONTH = re.compile(r"(\d{4})\D?(\d{2})")

USED, KEPT = {}, {}   # dataset -> what it replaced / why the file was kept


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


def _read(Dataset, name):
    try:
        df = Dataset.get(name).read_table(format="pandas")
    except Exception as e:   # not in the Data panel (AliasNotDefined), not an input of the transform (KeyError)...
        KEPT[name] = "not readable (%s)" % (str(e).splitlines()[0][:80] if str(e) else type(e).__name__)
        return None
    if df is None or not len(df.columns) or not len(df.dropna(how="all")):
        KEPT[name] = "empty"   # a sheet with its header only: the file is kept rather than emptied
        return None
    return df


def _rows(df, day_first=False):
    rows = [[_text(v, day_first) for v in r] for r in df.itertuples(index=False, name=None)]
    return [r for r in rows if any(c.strip() for c in r)]


def _write(path, header, rows, sep=";"):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=sep, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def _matched(df, wanted, name):
    """df with its columns renamed to `wanted` (matched by _key) and in that order; None, with the reason kept, when one is
    missing."""
    have = {_key(c): c for c in df.columns}
    missing = [c for c in wanted if _key(c) not in have]
    if missing:
        KEPT[name] = "column(s) missing: %s" % ", ".join(missing)
        return None
    return df[[have[_key(c)] for c in wanted]].set_axis(list(wanted), axis=1)


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


def _list(Dataset, name, source, columns, skip, folder, sources):
    df = _read(Dataset, name)
    if df is None:
        return
    exact = [sources[c] for c in columns]
    if name == "fto2_set_cables":
        from .downloads import TRACKER_COLUMNS
        exact = list(TRACKER_COLUMNS)
    have = {_key(c) for c in df.columns}
    missing = [c for c in exact if _key(c) not in have]
    if missing:
        KEPT[name] = "column(s) missing: %s" % ", ".join(missing)
        return
    names = {_key(c): c for c in exact}
    df = df.set_axis([names.get(_key(c), str(c)) for c in df.columns], axis=1)   # the columns the run looks for, spelt as it does
    path = os.path.join(folder, "fusion_%s.csv" % name)
    rows = _rows(df, day_first=True)
    _write(path, list(df.columns), rows, sep=",")
    change = {source: path}
    if skip:
        change[skip] = "0"
    _set_lines(folder, SOURCES, change)
    USED[name] = "%s (%d rows)" % (source, len(rows))


def load(Dataset, say=print):
    """Take the settings kept in Fusion: copy the settings folder, replace in the copy each table whose dataset can be read,
    and point the run at the copy. Call it before the rest of the code is loaded. Returns USED."""
    source = os.environ.get("FTO2_FUSION_FROM") or config.folder()   # the folder of files, also on a second run
    os.environ["FTO2_FUSION_FROM"] = source
    work = tempfile.mkdtemp(prefix="fto2_settings_")
    shutil.copytree(source, work, dirs_exist_ok=True)
    USED.clear()
    KEPT.clear()
    for name, target in TABLES.items():
        _table(Dataset, name, target, work)
    for name, table in LINES.items():
        _lines(Dataset, name, table, work)
    header, rows = config._rows(os.path.join(work, SOURCES), SOURCES)
    sources = {r[header.index("nom")].strip(): r[header.index("valeur")] for r in rows}
    for name, (src, columns, skip) in LISTS.items():
        _list(Dataset, name, src, columns, skip, work, sources)
    os.environ["FTO2_CONFIG"] = work
    config._PARAMS.clear()
    if USED:
        say("Settings from Fusion: " + "; ".join("%s -> %s" % kv for kv in USED.items()))
    bad = {k: v for k, v in KEPT.items() if not v.startswith(("not readable", "empty"))}
    for k, v in bad.items():
        say("⚠️ %s not used, %s: the file of the settings folder is used instead" % (k, v))
    if not USED and not bad:
        say("Settings: no Fusion dataset in the Data panel, the files of the settings folder are used")
    return dict(USED)
