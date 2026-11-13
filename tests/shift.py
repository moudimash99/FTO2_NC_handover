"""Move the dates of a table, to rehearse another year (tests/next_year_rehearsal.py). No backend code is loaded here."""
import datetime as dt
import re

DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def shift_dates(table, days, columns=None):
    """A copy of a table with its dates moved by `days`: the 'AAAA-MM-JJ' at the start of a value (the time of day after it
    stays). columns: the columns holding dates; by default those whose name holds 'time' or 'date'."""
    if not days:
        return table

    def move(v):
        m = DAY.match(v) if isinstance(v, str) else None
        if not m:
            return v
        try:
            return (dt.date(int(m[1]), int(m[2]), int(m[3])) + dt.timedelta(days)).isoformat() + v[10:]
        except ValueError:   # a mistyped date
            return v
    out = table.copy()
    for c in (columns if columns is not None else [c for c in out.columns if "time" in c.lower() or "date" in c.lower()]):
        out[c] = out[c].map(move)
    return out
