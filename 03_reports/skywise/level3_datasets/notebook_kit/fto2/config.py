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


def table(name, columns=None):
    """A settings table as text (no value is converted). `columns`: the columns it must have."""
    path = os.path.join(folder(), name)
    if not os.path.exists(path):
        raise ConfigError("settings table %s not found in %s" % (name, folder()))
    try:
        t = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except Exception as e:   # a broken file: say which one
        raise ConfigError("%s cannot be read as a ';' table: %s" % (name, e))
    t.columns = [c.strip() for c in t.columns]
    t = t[~(t.apply(lambda r: "".join(r).strip(), axis=1) == "")].reset_index(drop=True)   # blank lines from Excel
    if columns:
        missing = [c for c in columns if c not in t.columns]
        if missing:
            raise ConfigError("%s: the column(s) %s are missing (expected: %s)" % (name, ", ".join(missing), " ; ".join(columns)))
    return t


def path(name):
    """The full path of a settings table."""
    return os.path.join(folder(), name)


def frame(name, **read_csv_options):
    """A settings table read the usual pandas way (numbers become numbers), for the code that needs typed columns."""
    p = path(name)
    if not os.path.exists(p):
        raise ConfigError("settings table %s not found in %s" % (name, folder()))
    return pd.read_csv(p, sep=";", encoding="utf-8-sig", **read_csv_options)


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


def parameter(name, table_name="2_parametres.csv", keep_spaces=False):
    """One value of a 'nom ; valeur' settings table (2_parametres.csv by default), as text.
    keep_spaces: keep spaces at the start and end (column names copied from a file, e.g. ' Date SAP')."""
    if table_name not in _PARAMS:
        t = table(table_name, ["nom", "valeur"])
        _PARAMS[table_name] = dict(zip(t["nom"].str.strip(), t["valeur"]))
    values = _PARAMS[table_name]
    if name not in values:
        raise ConfigError("%s: the line '%s' is missing" % (table_name, name))
    return values[name] if keep_spaces else values[name].strip()


def parameter_list(name, table_name="2_parametres.csv"):
    """A setting holding several values separated by '|', as a list."""
    return [v.strip() for v in parameter(name, table_name).split("|") if v.strip()]


def parameter_yes(name, table_name="2_parametres.csv"):
    """A 'oui' / 'non' setting, as True / False."""
    v = parameter(name, table_name).lower()
    if v not in ("oui", "non"):
        raise ConfigError("%s, %s: write 'oui' or 'non', found '%s'" % (table_name, name, v))
    return v == "oui"
