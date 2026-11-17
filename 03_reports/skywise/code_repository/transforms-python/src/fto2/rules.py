"""The rule engine: applies a rule table from config/ to a table of NCs.

A rule table has the columns   ordre ; resultat ; colonne ; test ; valeur ; commentaire

- Rows with the same `ordre` form one rule: all their conditions must be true (AND).
- Rules are tried from the smallest `ordre` to the largest. The first rule whose conditions are all true gives the
  NC its `resultat`. An NC that no rule matches gets the result of the rule whose test is `toujours` (the default).
- `colonne` names a column of the NC data. Several columns joined by " + " are searched as one text
  (e.g. "description_short + article_version_description").
- `valeur` holds one value or several separated by "|" (any of them is enough).
- `resultat` may be "{extrait}": the text found by an `extraire` test.

Tests (upper and lower case are treated the same):
  contient            the text contains one of the values
  ne_contient_pas     the text contains none of the values
  mot                 the text contains one of the values as a whole word ("REC" matches "REW-REC" but not "RECEPTION")
  commence_par        the text starts with one of the values
  ne_commence_pas_par the text starts with none of the values
  egal                the text (spaces trimmed) is one of the values
  different           the text (spaces trimmed) is none of the values
  vide / non_vide     the cell is empty / not empty
  regex / pas_regex   expert: a Python regular expression is found / not found
  extraire            expert: a regular expression with one group in (...); the text it finds can be the result
  toujours            always true (the default rule, put it last)
"""
import re

import numpy as np
import pandas as pd

TESTS = ("contient", "ne_contient_pas", "mot", "commence_par", "ne_commence_pas_par", "egal", "different",
         "vide", "non_vide", "regex", "pas_regex", "extraire", "toujours")
NEEDS_VALUE = {"contient", "ne_contient_pas", "mot", "commence_par", "ne_commence_pas_par", "egal", "different",
               "regex", "pas_regex", "extraire"}
EXTRACT = "{extrait}"


class RuleError(ValueError):
    """A rule table that cannot be applied. The message says which file, which line and what to fix."""


def _values(v):
    return [x for x in str(v).split("|") if x != ""]


def _text(df, colonne):
    """The text a condition looks at: one column, or several joined by ' | '."""
    cols = [c.strip() for c in str(colonne).split("+")]
    parts = [df[c].fillna("").astype(str) for c in cols]
    out = parts[0]
    for p in parts[1:]:
        out = out + " | " + p
    return out


def _any_of(values):
    return "|".join(re.escape(v) for v in values)


def _condition(df, row):
    """True/False per NC for one condition row."""
    test = row["test"]
    if test == "toujours":
        return pd.Series(True, index=df.index), None
    s = _text(df, row["colonne"])
    vals = _values(row["valeur"])
    if test == "contient":
        return s.str.contains(_any_of(vals), case=False, regex=True), None
    if test == "ne_contient_pas":
        return ~s.str.contains(_any_of(vals), case=False, regex=True), None
    if test == "mot":
        return s.str.contains(r"\b(?:%s)\b" % _any_of(vals), case=False, regex=True), None
    if test == "commence_par":
        return s.str.contains(r"^(?:%s)" % _any_of(vals), case=False, regex=True), None
    if test == "ne_commence_pas_par":
        return ~s.str.contains(r"^(?:%s)" % _any_of(vals), case=False, regex=True), None
    if test in ("egal", "different"):
        hit = s.str.strip().str.upper().isin([v.strip().upper() for v in vals])
        return (hit if test == "egal" else ~hit), None
    if test == "vide":
        return s.str.strip() == "", None
    if test == "non_vide":
        return s.str.strip() != "", None
    if test == "regex":
        return s.str.contains(row["valeur"], case=False, regex=True), None
    if test == "pas_regex":
        return ~s.str.contains(row["valeur"], case=False, regex=True), None
    if test == "extraire":
        found = s.str.extract(row["valeur"], expand=False, flags=re.IGNORECASE)
        return found.notna(), found
    raise RuleError("unknown test '%s'" % test)


def check(table, name, columns=None):
    """Plain-language problems in a rule table (an empty list when it is fine). `columns`: the NC columns available."""
    problems = []
    need = ["ordre", "resultat", "colonne", "test", "valeur"]
    missing = [c for c in need if c not in table.columns]
    if missing:
        return ["%s: the column(s) %s are missing (expected: %s)" % (name, ", ".join(missing), " ; ".join(need + ["commentaire"]))]
    for i, r in table.iterrows():
        line = "%s line %d" % (name, i + 2)   # +2: the header is line 1
        if str(r["ordre"]).strip() == "" or not str(r["ordre"]).strip().replace(".", "", 1).isdigit():
            problems.append("%s: 'ordre' must be a number, found '%s'" % (line, r["ordre"]))
        if r["test"] not in TESTS:
            problems.append("%s: test '%s' is not one of: %s" % (line, r["test"], ", ".join(TESTS)))
            continue
        if r["test"] in NEEDS_VALUE and str(r["valeur"]).strip() == "":
            problems.append("%s: test '%s' needs a value in 'valeur'" % (line, r["test"]))
        if r["test"] in ("regex", "pas_regex", "extraire"):
            try:
                rx = re.compile(r["valeur"])
            except re.error as e:
                problems.append("%s: the regular expression '%s' is not valid (%s)" % (line, r["valeur"], e))
                continue
            if r["test"] == "extraire" and rx.groups != 1:
                problems.append("%s: 'extraire' needs exactly one group in (...), found %d" % (line, rx.groups))
        if r["test"] != "toujours" and columns is not None:
            for c in str(r["colonne"]).split("+"):
                if c.strip() not in columns:
                    problems.append("%s: column '%s' is not in the NC data" % (line, c.strip()))
        if str(r["resultat"]).strip() == "":
            problems.append("%s: 'resultat' is empty" % line)
    if not (table["test"] == "toujours").any():
        problems.append("%s: no default rule (a last line with test 'toujours')" % name)
    return problems


def apply(df, table, name="rules"):
    """The result of the rule table for each row of df (a Series of text)."""
    problems = check(table, name, set(df.columns))
    if problems:
        raise RuleError("\n".join(problems))
    result = pd.Series(np.nan, index=df.index, dtype=object)
    todo = pd.Series(True, index=df.index)
    for _, rule in table.groupby(table["ordre"].astype(float), sort=True):
        hit = todo.copy()
        found = None
        for _, row in rule.iterrows():
            ok, extracted = _condition(df, row)
            hit &= ok.fillna(False).astype(bool)
            if extracted is not None:
                found = extracted
        res = str(rule["resultat"].iloc[0])
        if res == EXTRACT:
            if found is None:
                raise RuleError("%s: rule %s gives '{extrait}' but has no 'extraire' test" % (name, rule["ordre"].iloc[0]))
            result[hit] = found[hit]
        else:
            result[hit] = res
        todo &= ~hit
    return result
