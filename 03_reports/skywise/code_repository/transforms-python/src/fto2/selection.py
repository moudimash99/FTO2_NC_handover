"""Which NCs count, and the columns the notebook adds to each NC: phase (SERIE / REC / FTI), decision label, origin,
NC type and product. Every rule comes from a table in config/:

  2_regle_exclusion.csv   NCs left out (ERMA, NCs deleted in another plant)
  2_regle_phase.csv       SERIE / REC / FTI
  2_decisions.csv         decision code -> label
  2_regle_origine.csv     Test / Qualite (who opened the NC)
  2_regle_type_nc.csv     NC type, in priority order
  2_regle_produit.csv     product, from the article and station texts

The Skywise notebook and the laptop build both call apply_rules(), so the two cannot differ.
"""
from . import config, rules

TEXT_COLUMNS = ("decision_status", "workflow_list", "article_version_description", "user_department")


def exclusions(df):
    """True for the NCs the exclusion rules leave out."""
    t = config.rule_table("2_regle_exclusion.csv", set(df.columns))
    return rules.apply(df, t, "2_regle_exclusion.csv") == "exclure"


def add_columns(df):
    """The *_auto columns, in the order the rules need them (the NC type uses the origin)."""
    df = df.copy()
    for c in TEXT_COLUMNS:
        df[c] = df[c].fillna("")
    df["Programme_auto"] = rules.apply(df, config.rule_table("2_regle_phase.csv", set(df.columns)), "2_regle_phase.csv")
    labels, other = config.mapping("2_decisions.csv", "code", "libelle")
    df["Statut_decision_auto"] = df["decision_status"].map(labels).fillna(other)
    df["Origin_auto"] = rules.apply(df, config.rule_table("2_regle_origine.csv", set(df.columns)), "2_regle_origine.csv")
    df["Type_NC_auto"] = rules.apply(df, config.rule_table("2_regle_type_nc.csv", set(df.columns)), "2_regle_type_nc.csv")
    df["Produit_auto"] = rules.apply(df, config.rule_table("2_regle_produit.csv", set(df.columns)), "2_regle_produit.csv")
    return df


def apply_rules(raw, station_desc=None, exclude=True):
    """The notebook's selection and *_auto columns on a raw NC extract.
    station_desc: {station: description}, used when the extract has no station_description column."""
    df = raw.copy()
    for c in TEXT_COLUMNS:
        df[c] = df[c].fillna("")
    if exclude:
        df = df[~exclusions(df)].copy()
    if station_desc is not None:
        df["station_description"] = df["station"].map(station_desc)
    return add_columns(df).reset_index(drop=True)
