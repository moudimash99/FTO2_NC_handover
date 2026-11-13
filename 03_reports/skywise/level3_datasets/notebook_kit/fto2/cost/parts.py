"""The value of the part on a rejection, a scrap or an exchange.

The NC data names the part concerned in its column `material` (the SAP material number). It is not the article of the NC,
which is the whole assembly. The price of each material comes from the price list config/1_prix_pieces.csv:

    materiel ; designation ; prix_unitaire_eur

One row per material. The value of an NC = unit price x quantity (the NC's defect quantity, 1 when empty). An NC with no
material, or whose material has no price, gets no value: the cost model then counts 0 and marks it "Part value unknown".
The cost model adds the value only for the decisions that count the part (config/2_cout_decisions.csv, valeur_piece).

The price list may be an export pasted as it is: the two columns are found by their names (MATERIAL_NAMES, PRICE_NAMES), in
any order, other columns are ignored; the separator is ';', ',' or a tab; prices take a dot or a comma. Material numbers are
compared without spaces, in upper case and without leading zeros (000000006325018500 = 6325018500).
"""
import csv
import os
import re
import unicodedata

import numpy as np
import pandas as pd

from .. import config

TABLE = "1_prix_pieces.csv"
MATERIAL_NAMES = ("materiel", "material", "numero_materiel", "material_number", "article", "reference", "ref", "part_number", "pn")
PRICE_NAMES = ("prix_unitaire_eur", "prix_unitaire", "prix", "pu", "unit_price", "price", "cout", "cost", "valeur", "montant")


def material_id(v):
    """A material number as compared: no spaces, upper case, no leading zeros; '' when empty."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    t = re.sub(r"\s+", "", str(v)).upper()
    t = re.sub(r"\.0$", "", t)
    return "" if t in ("NAN", "NONE", "<NA>") else t.lstrip("0")


def _header(name):
    t = unicodedata.normalize("NFD", str(name)).encode("ascii", "ignore").decode().strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def _price(v, where):
    t = re.sub(r"[\s  €]|EUR", "", str(v or ""), flags=re.I)
    if not t:
        return None
    if "," in t and "." in t:   # 1.234,56 or 1,234.56: the last sign is the decimal one
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    try:
        return float(t.replace(",", "."))
    except ValueError:
        raise config.ConfigError("%s: '%s' is not a price (%s)" % (TABLE, v, where))


def _read(path):
    """The rows of the price list as lists of text, whatever its separator and encoding (UTF-8 or the Excel default)."""
    with open(path, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    sep = max(";,\t", key=lines[0].count)
    return [r for r in csv.reader(lines, delimiter=sep)]


def price_list():
    """{material: unit price} from config/1_prix_pieces.csv; {} when the table is not there."""
    path = os.path.join(config.folder(), TABLE)
    if not os.path.exists(path):
        return {}
    rows = _read(path)
    if not rows:
        return {}
    names = [_header(c) for c in rows[0]]
    mat = next((names.index(n) for n in MATERIAL_NAMES if n in names), None)
    price = next((names.index(n) for n in PRICE_NAMES if n in names), None)
    if mat is None or price is None:
        raise config.ConfigError("%s: it needs a column for the material number (e.g. 'materiel') and one for the unit price "
                                 "(e.g. 'prix_unitaire_eur'); found: %s" % (TABLE, " ; ".join(rows[0])))
    prices = {}
    for i, r in enumerate(rows[1:], start=2):
        if len(r) <= max(mat, price):
            continue
        m, p = material_id(r[mat]), _price(r[price], "line %d" % i)
        if m and p is not None:
            prices[m] = p
    return prices


def part_values(materials, quantities=None):
    """The part value of each NC: the unit price of its material x its quantity. NaN when the NC has no material or the
    material has no price."""
    prices = price_list()
    mats = pd.Series([material_id(m) for m in materials])
    unit = mats.map(prices) if prices else pd.Series(np.nan, index=mats.index)
    if quantities is None:
        qty = pd.Series(1.0, index=mats.index)
    else:
        qty = pd.to_numeric(pd.Series(list(quantities)), errors="coerce")
        qty = qty.where(qty > 0, 1.0).fillna(1.0)
    return (unit * qty).to_numpy(dtype=float)


def to_price(nc):
    """The materials that still need a price: one row per material of the NCs whose decision counts the part and that FTO2
    is liable for, with no price yet. nc: the NCs after the cost model, with material, material_label, cnq_rule, cnq_on_aec."""
    from . import params
    counts = {k for k, v in params.RULES.items() if v[params.RULE_FIELDS.index("part")]}
    t = nc[nc["cnq_rule"].isin(counts) & (nc["cnq_on_aec"] == 1) & (nc["material"].fillna("") != "") & nc["part_value"].isna()]
    if not len(t):
        return pd.DataFrame(columns=["materiel", "designation", "prix_unitaire_eur", "nc", "derniere_nc"])
    g = t.groupby("material").agg(designation=("material_label", "first"), nc=("notification_number", "size"),
                                  derniere_nc=("date_creation", "max")).reset_index().rename(columns={"material": "materiel"})
    g["prix_unitaire_eur"] = ""
    return g.sort_values(["nc", "materiel"], ascending=[False, True])[["materiel", "designation", "prix_unitaire_eur", "nc", "derniere_nc"]].reset_index(drop=True)
