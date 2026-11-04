"""Writing an everyday table (config/1_*.csv) from a raw file, without losing hand edits.

Each row of an everyday table has a 'source' column:
  auto    written by a script from a raw file; the next run of the script replaces it
  manuel  typed or corrected by a person; scripts leave it alone

A person who corrects an 'auto' row sets its source to 'manuel' and it stays. To give a row back to the script, set its source
back to 'auto' (or delete the row) and run the script again.
"""
import os

import pandas as pd

from . import config

AUTO, MANUAL = "auto", "manuel"


def write(name, new_rows, key):
    """Write config/<name>: the new 'auto' rows plus the existing 'manuel' rows. A new row whose key (list of columns) is
    the key of a 'manuel' row is not written: the person's row wins. Prints what it kept. Returns the table written."""
    new = new_rows.copy().astype(str).replace({"nan": "", "None": "", "NaT": ""})
    new["source"] = AUTO
    path = config.path(name)
    manual = pd.DataFrame(columns=new.columns)
    if os.path.exists(path):
        old = config.table(name)
        if "source" in old.columns:
            bad = sorted(set(old["source"].str.strip()) - {AUTO, MANUAL, ""})
            if bad:
                raise config.ConfigError("%s: the column 'source' takes 'auto' or 'manuel', found %s" % (name, ", ".join(bad)))
            manual = old[old["source"].str.strip() == MANUAL]
    if len(manual):
        missing = [c for c in new.columns if c not in manual.columns]
        if missing:
            raise config.ConfigError("%s: the column(s) %s are missing from the table" % (name, ", ".join(missing)))
        manual = manual[list(new.columns)]
        keys = set(map(tuple, manual[key].astype(str).values))
        new = new[[tuple(r) not in keys for r in new[key].astype(str).values]]
        print("%s: %d row(s) corrected by hand kept (source = manuel):" % (name, len(manual)))
        for r in manual[key].astype(str).values[:20]:
            print("   ", " | ".join(r))
    out = pd.concat([new, manual], ignore_index=True)
    out.to_csv(path, sep=";", index=False, encoding="utf-8")
    print("%s: %d rows written (%d auto, %d manuel)" % (name, len(out), (out.source == AUTO).sum(), (out.source == MANUAL).sum()))
    return out


def read(name, columns=None):
    """An everyday table as text, 'source' included."""
    return config.table(name, columns)
