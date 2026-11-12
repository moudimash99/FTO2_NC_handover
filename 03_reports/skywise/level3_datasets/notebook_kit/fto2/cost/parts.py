"""The value of the part on a rejection, a scrap or an exchange, from the price list config/1_prix_pieces.csv.

The NC data does not hold the number of the part that was rejected (its SAP article is the whole assembly). So a part is tied
to an NC in two ways:

  - by its reference written in the NC: a row with a reference and a unit price, and no NC number, prices every NC whose
    title or long text contains that reference (spaces and case ignored; references shorter than 5 characters are not
    searched, to avoid false matches);
  - by hand: a row with an NC number says that NC used that part (quantity `quantite`, 1 when empty). Its price is the row's
    own, or else the price of the row with the same reference and no NC. An NC listed by hand is not searched in the text.

The value is the sum of price x quantity of the parts found. An NC with no part found keeps no value (the cost model then
counts 0 and marks it "Part value unknown"). The cost model adds the value only for the decisions that count the part
(config/2_cout_decisions.csv, column valeur_piece).
"""
import re

import numpy as np
import pandas as pd

from .. import config

TABLE = "1_prix_pieces.csv"
COLUMNS = ["reference", "prix_unitaire_eur", "nc", "quantite", "note"]
MIN_LENGTH = 5


def _norm(s):
    return re.sub(r"\s+", "", str(s or "")).upper()


def _num(v, where):
    t = str(v or "").strip().replace(",", ".").replace("€", "").replace(" ", "")
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        raise config.ConfigError("%s: '%s' is not a number (%s)" % (TABLE, v, where))


def _id(v):
    return re.sub(r"\.0$", "", str(v or "").strip()).lstrip("0")


def price_list():
    """(prices by reference, rows tied to an NC): {REFERENCE: unit price}, {nc: [(reference, price or None, quantity)]}."""
    try:
        t = config.table(TABLE, COLUMNS)
    except config.ConfigError as e:
        if "not found" in str(e):   # no price list: no part value, as before
            return {}, {}
        raise
    prices, by_nc = {}, {}
    for i, r in t.iterrows():
        where = "line %d" % (i + 2)
        ref, price, nc = _norm(r["reference"]), _num(r["prix_unitaire_eur"], where), _id(r["nc"])
        if nc:
            q = _num(r["quantite"], where)
            by_nc.setdefault(nc, []).append((ref, price, q if q is not None else 1.0))
        elif ref and price is not None:
            prices[ref] = price
    return prices, by_nc


def part_values(numbers, titles, texts):
    """The part value of each NC (NaN when no priced part is found), in the order of `numbers`."""
    prices, by_nc = price_list()
    ids = pd.Series([_id(n) for n in numbers])
    out = pd.Series(np.nan, index=ids.index)
    if not prices and not by_nc:
        return out.to_numpy()
    text = (pd.Series(list(titles)).fillna("").astype(str) + " " + pd.Series(list(texts)).fillna("").astype(str)).map(_norm)
    found = pd.Series(0.0, index=ids.index)
    hit = pd.Series(False, index=ids.index)
    for ref, price in prices.items():   # a reference written in the NC
        if len(ref) < MIN_LENGTH:
            continue
        m = text.str.contains(ref, regex=False)
        found += np.where(m, price, 0.0)
        hit |= m
    manual = ids.isin(by_nc.keys())
    for i in ids.index[manual]:   # parts tied by hand replace the text search for that NC
        v = [(p if p is not None else prices.get(ref)) for ref, p, _ in by_nc[ids[i]]]
        q = [qty for _, _, qty in by_nc[ids[i]]]
        known = [(p, n) for p, n in zip(v, q) if p is not None]
        found[i], hit[i] = sum(p * n for p, n in known), bool(known)
    out[hit] = found[hit]
    return out.to_numpy()
