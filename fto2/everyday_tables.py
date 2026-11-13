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


def write(name, new_rows, key, keep=None, keep_if=None):
    """Write config/<name>: the new 'auto' rows plus the existing 'manuel' rows. A new row whose key (list of columns) is
    the key of a 'manuel' row is not written: the person's row wins.
    keep (list of columns): the existing 'auto' rows that the new rows no longer hold, compared on these columns, stay as they
    are; keep_if(row) says which of them (all, without it). The production plan needs it: an aircraft that has left the
    export because it was delivered keeps its last known dates, which give the deliveries of the year before.
    Prints what it kept. Returns the table written."""
    new = new_rows.copy().astype(str).replace({"nan": "", "None": "", "NaT": ""})
    new["source"] = AUTO
    path = config.path(name)
    manual = earlier = pd.DataFrame(columns=new.columns)
    if os.path.exists(path):
        old = config.table(name)
        if "source" in old.columns:
            bad = sorted(set(old["source"].str.strip()) - {AUTO, MANUAL, ""})
            if bad:
                raise config.ConfigError("%s: the column 'source' takes 'auto' or 'manuel', found %s" % (name, ", ".join(bad)))
            manual = old[old["source"].str.strip() == MANUAL]
            if keep:
                earlier = old[old["source"].str.strip() != MANUAL]
    for t in (manual, earlier):
        missing = [c for c in new.columns if len(t) and c not in t.columns]
        if missing:
            raise config.ConfigError("%s: the column(s) %s are missing from the table" % (name, ", ".join(missing)))
    if len(earlier):
        earlier = earlier[list(new.columns)]
        held = set(map(tuple, new[keep].astype(str).values)) | (set(map(tuple, manual[keep].astype(str).values)) if len(manual) else set())
        earlier = earlier[[tuple(r) not in held for r in earlier[keep].astype(str).values]]
        if keep_if is not None and len(earlier):
            wanted = [bool(keep_if(r)) for _, r in earlier.iterrows()]
            print("%s: %d row(s) no longer in the new file left out" % (name, len(wanted) - sum(wanted)))
            earlier = earlier[wanted]
        print("%s: %d row(s) of earlier files kept (no longer in the new one)" % (name, len(earlier)))
    if len(manual):
        manual = manual[list(new.columns)]
        keys = set(map(tuple, manual[key].astype(str).values))
        new = new[[tuple(r) not in keys for r in new[key].astype(str).values]]
        print("%s: %d row(s) corrected by hand kept (source = manuel):" % (name, len(manual)))
        for r in manual[key].astype(str).values[:20]:
            print("   ", " | ".join(r))
    out = pd.concat([new, earlier, manual], ignore_index=True)
    out.to_csv(path, sep=";", index=False, encoding="utf-8")
    print("%s: %d rows written (%d auto, %d manuel)" % (name, len(out), (out.source == AUTO).sum(), (out.source == MANUAL).sum()))
    return out


def read(name, columns=None):
    """An everyday table as text, 'source' included."""
    return config.table(name, columns)
