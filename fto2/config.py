"""Reads the settings in config/ (on Skywise: data/config/ next to the notebook).

Every setting is a small ';' table that opens in Excel. The file name starts with its level:
  1_  everyday (anyone in the team)
  2_  rules (someone careful)
  3_  expert (technical)
config/lisez_moi.csv lists every table, what it changes and who should edit it.

A table with a mistake stops the run with a plain message naming the file, the line and what to fix.
"""
import os

import pandas as pd

from . import rules

HERE = os.path.dirname(os.path.abspath(__file__))
LAPTOP_DIR = os.path.join(os.path.dirname(HERE), "config")
SKYWISE_DIR = os.path.join("data", "config")


class ConfigError(ValueError):
    """A settings table is missing or wrong. The message says what to fix."""


def folder():
    """The settings folder: config/ on the laptop, data/config/ in the Skywise notebook, or FTO2_CONFIG if set."""
    if os.environ.get("FTO2_CONFIG"):
        return os.environ["FTO2_CONFIG"]
    return LAPTOP_DIR if os.path.isdir(LAPTOP_DIR) else SKYWISE_DIR


def _text(path):
    """The text of a settings table. Excel saves a CSV in the Windows encoding unless 'CSV UTF-8' is chosen: both are read."""
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def _rows(path, name):
    """The lines of a ';' table as lists of cells. Every line must have as many cells as the header: a ';' typed inside a text
    shifts the columns. Blank lines and empty cells after the last column (Excel adds some) are left out."""
    import csv
    import io
    try:
        rows = list(csv.reader(io.StringIO(_text(path), newline=""), delimiter=";"))
    except Exception as e:   # a broken file: say which one
        raise ConfigError("%s cannot be read as a ';' table: %s" % (name, e))
    if not rows or not any(c.strip() for c in rows[0]):
        raise ConfigError("%s is empty: it needs at least its header line" % name)
    header = [c.strip() for c in rows[0]]
    while header and header[-1] == "":
        header.pop()
    n, out = len(header), []
    for i, r in enumerate(rows[1:], start=2):
        while len(r) > n and r[-1].strip() == "":
            r = r[:-1]
        if not any(c.strip() for c in r):
            continue
        if len(r) > n:
            raise ConfigError("%s line %d has %d columns, the header has %d: a ';' inside a text? Put that text in quotes "
                              "or replace the ';'" % (name, i, len(r), n))
        out.append(r + [""] * (n - len(r)))
    return header, out


def table(name, columns=None):
    """A settings table as text (no value is converted). `columns`: the columns it must have."""
    path = os.path.join(folder(), name)
    if not os.path.exists(path):
        raise ConfigError("settings table %s not found in %s" % (name, folder()))
    header, rows = _rows(path, name)
    t = pd.DataFrame(rows, columns=header, dtype=str)
    if columns:
        missing = [c for c in columns if c not in t.columns]
        if missing:
            raise ConfigError("%s: the column(s) %s are missing (expected: %s)" % (name, ", ".join(missing), " ; ".join(columns)))
    return t


def number(text, where):
    """A number typed in a settings table, with a dot or a comma ('0.25', '0,25'). where: the table and line, for the message."""
    t = str(text).strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return int(t) if t.lstrip("-").isdigit() else float(t)
    except ValueError:
        raise ConfigError("%s: '%s' is not a number" % (where, text))


def day(text, where):
    """A date typed in a settings table, as 'AAAA-MM-JJ'. Excel turns such a date into 'JJ/MM/AAAA' when it saves the file:
    both are read."""
    import datetime as dt
    t = str(text).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(t, fmt).date().isoformat()
        except ValueError:
            pass
    raise ConfigError("%s: '%s' is not a date (write it as 2026-01-31 or 31/01/2026)" % (where, text))


def path(name):
    """The full path of a settings table."""
    return os.path.join(folder(), name)


def frame(name, **read_csv_options):
    """A settings table read the usual pandas way (numbers become numbers), for the code that needs typed columns."""
    p = path(name)
    if not os.path.exists(p):
        raise ConfigError("settings table %s not found in %s" % (name, folder()))
    import io
    return pd.read_csv(io.StringIO(_text(p)), sep=";", **read_csv_options)


def rule_table(name, data_columns=None):
    """A rule table (see fto2/rules.py), checked."""
    t = table(name, ["ordre", "resultat", "colonne", "test", "valeur"])
    problems = rules.check(t, name, data_columns)
    if problems:
        raise ConfigError("\n".join(problems))
    return t


def mapping(name, key, value, default_key="(autre)"):
    """A two-column table as {key: value} plus the value of the '(autre)' row (None if there is none)."""
    t = table(name, [key, value])
    d = dict(zip(t[key].str.strip(), t[value]))
    return {k: v for k, v in d.items() if k != default_key}, d.get(default_key)


_PARAMS = {}


def _values(table_name):
    """A 'nom ; valeur' settings table as {name: value}, read once."""
    if table_name not in _PARAMS:
        t = table(table_name, ["nom", "valeur"])
        _PARAMS[table_name] = dict(zip(t["nom"].str.strip(), t["valeur"]))
    return _PARAMS[table_name]


def parameter(name, table_name="2_parametres.csv", keep_spaces=False):
    """One value of a 'nom ; valeur' settings table (2_parametres.csv by default), as text.
    keep_spaces: keep spaces at the start and end (column names copied from a file, e.g. ' Date SAP')."""
    values = _values(table_name)
    if name not in values:
        raise ConfigError("%s: the line '%s' is missing" % (table_name, name))
    return values[name] if keep_spaces else values[name].strip()


def optional(name, table_name="2_parametres.csv"):
    """A setting that may be left empty (or left out): '' then."""
    return _values(table_name).get(name, "").strip()


def parameter_day(name, table_name="2_parametres.csv"):
    """A date setting, as 'AAAA-MM-JJ' (see day())."""
    return day(parameter(name, table_name), "%s, %s" % (table_name, name))


def parameter_list(name, table_name="2_parametres.csv"):
    """A setting holding several values separated by '|', as a list."""
    return [v.strip() for v in parameter(name, table_name).split("|") if v.strip()]


def parameter_yes(name, table_name="2_parametres.csv"):
    """A 'oui' / 'non' setting, as True / False."""
    v = parameter(name, table_name).lower()
    if v not in ("oui", "non"):
        raise ConfigError("%s, %s: write 'oui' or 'non', found '%s'" % (table_name, name, v))
    return v == "oui"


# ---------------------------------------------------------------- the year
# The pages follow one calendar year: the NCs created in that year, its production plan, its targets. The year is one line
# of 2_parametres.csv ('annee'); the dates tied to it are worked out here, so that a new year is a one-line change.
def _year(text, where):
    t = str(text).strip()
    if not (t.isdigit() and len(t) == 4):
        raise ConfigError("%s: '%s' is not a year (write it with four digits, e.g. 2026)" % (where, text))
    return int(t)


def year():
    """The year the pages follow ('annee'). An empty line means the current year. Settings written before the line
    existed gave a start date instead ('date_debut'): its year is used then."""
    import datetime as dt
    v = optional("annee")
    if v:
        return _year(v, "2_parametres.csv, annee")
    d = optional("date_debut")
    return int(day(d, "2_parametres.csv, date_debut")[:4]) if d else dt.date.today().year


def comparison_year():
    """The year the targets and the year comparisons start from: 'annee_comparaison', else the year before the one followed."""
    v = optional("annee_comparaison")
    y = _year(v, "2_parametres.csv, annee_comparaison") if v else year() - 1
    if y >= year():
        raise ConfigError("2_parametres.csv: annee_comparaison (%d) must be before the year followed (%d); "
                          "leave it empty for the year before" % (y, year()))
    return y


def first_day():
    """The first creation date counted: 1 January of the year followed, as 'AAAA-MM-JJ'."""
    return "%d-01-01" % year()


def year_end():
    """The day after the year followed, as 'AAAA-MM-JJ': an NC created from that day on belongs to the next year."""
    return "%d-01-01" % (year() + 1)


def aleas_since():
    """The aléas are read from 1 December of the year before: an NC of early January can follow an aléa of late December."""
    return "%d-12-01" % (year() - 1)
