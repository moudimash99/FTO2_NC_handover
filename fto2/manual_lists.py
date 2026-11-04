"""The two manual lists: the GPS register (NC INT SERIE ELEC) and the Test list.

They do two things:
  1. NCs on a list that the standard selection does not catch are fetched by number (list_ids);
  2. each NC gets the lists' columns (Ext_Source, Ext_Produit, Ext_Nb_Defauts, GPS_Type_NC...), see add_external.

The file names, header rows and column names are in config/2_sources.csv. Same logic as the pipeline notebook's.
"""
import warnings

import pandas as pd

from . import config

SOURCES = "2_sources.csv"
EXTERNAL_TEXT_COLUMNS = ["Ext_Produit", "Ext_Nb_Defauts", "Ext_Defaut_Constate", "Ext_Source",
                         "GPS_Type_NC", "GPS_Statut_decision", "GPS_Imputation", "GPS_Retouches_majeures", "GPS_Retouches_mineures"]


def _src(name):
    return config.parameter(name, SOURCES, keep_spaces=name.endswith(("_numero", "_date")))   # column names: exactly as in the file


def _load(filepath, skiprows, id_col):
    """A list as a table, one row per NC number (numbers only, no duplicates). An empty table if the file cannot be read."""
    try:
        df = pd.read_csv(filepath, skiprows=skiprows, low_memory=False)
        df = df.dropna(subset=[id_col]).copy()
        df["notification_number"] = df[id_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        df = df[df["notification_number"].str.isnumeric()]
        return df.drop_duplicates(subset=["notification_number"])
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return pd.DataFrame()


def _coalesce(df, base):
    """One column from its Test and GPS versions, the Test value first."""
    t, g = base + "_test", base + "_gps"
    if t in df.columns and g in df.columns:
        df[base] = df[t].combine_first(df[g])
        df.drop(columns=[t, g], inplace=True)
    elif t in df.columns:
        df.rename(columns={t: base}, inplace=True)
    elif g in df.columns:
        df.rename(columns={g: base}, inplace=True)


def _source(row):
    a, b = row.get("Ext_Source_test"), row.get("Ext_Source_gps")
    if pd.notna(a) and pd.notna(b):
        warnings.warn(f"DATA ERROR: NC {row['notification_number']} found in BOTH Test and GPS files.")
        return "Both (Error)"
    if pd.notna(a):
        return a
    if pd.notna(b):
        return b
    return "Unknown External"


def external_table():
    """The two lists merged: one row per NC number with the Ext_ and GPS_ columns."""
    test = _load(_src("liste_test"), int(_src("liste_test_lignes_avant_entete")), _src("liste_test_colonne_numero"))
    if not test.empty:
        test["Ext_Produit"] = (test["Produit"].fillna("") + " " + test["VU\nuniquement PTVU"].fillna("")).str.strip()
        test = test.rename(columns={"Nb défaut": "Ext_Nb_Defauts", "Défaut majeur": "Ext_Defaut_Constate"})
        test["Ext_Source"] = "Test"
        test = test[["notification_number", "Ext_Produit", "Ext_Nb_Defauts", "Ext_Defaut_Constate", "Ext_Source"]].copy()
    else:
        test = pd.DataFrame(columns=["notification_number", "Ext_Produit", "Ext_Nb_Defauts", "Ext_Defaut_Constate", "Ext_Source"])
    gps = _load(_src("liste_gps"), int(_src("liste_gps_lignes_avant_entete")), _src("liste_gps_colonne_numero"))
    if not gps.empty:
        gps = gps.rename(columns={"Produit": "Ext_Produit", "Nombre total retouches": "Ext_Nb_Defauts",
                                  "Non conformité constatée": "Ext_Defaut_Constate", "Type NC": "GPS_Type_NC",
                                  "Statut décision": "GPS_Statut_decision", "IMPUTATION \n(après analyse)": "GPS_Imputation",
                                  "Nombre de retouches majeures": "GPS_Retouches_majeures",
                                  "Nombre de retouches mineures": "GPS_Retouches_mineures"})
        gps["Ext_Source"] = "GPS"
        gps = gps[["notification_number", "Ext_Produit", "Ext_Nb_Defauts", "Ext_Defaut_Constate", "Ext_Source",
                   "GPS_Type_NC", "GPS_Statut_decision", "GPS_Imputation", "GPS_Retouches_majeures", "GPS_Retouches_mineures"]].copy()
    else:
        gps = pd.DataFrame()
    both = pd.merge(test, gps, on="notification_number", how="outer", suffixes=("_test", "_gps"))
    for c in ("Ext_Produit", "Ext_Nb_Defauts", "Ext_Defaut_Constate"):
        _coalesce(both, c)
    both["Ext_Source"] = both.apply(_source, axis=1)
    if "Ext_Source_test" in both.columns:
        both = both.drop(columns=["Ext_Source_test", "Ext_Source_gps"])
    return both


def add_external(final_df, external):
    """The NCs with the lists' columns ('Not in external lists' when an NC is on neither list)."""
    external = external.copy()
    external["notification_number"] = external["notification_number"].astype(str)
    final_df = final_df.copy()
    final_df["notification_number"] = final_df["notification_number"].astype("Int64").astype(str)
    final_df = final_df.merge(external, on="notification_number", how="left")
    final_df["Ext_Source"] = final_df["Ext_Source"].fillna("Not in external lists")
    for col in EXTERNAL_TEXT_COLUMNS:   # text, so that Foundry keeps one schema
        if col in final_df.columns:
            final_df[col] = final_df[col].fillna("").astype(str)
    if "is_orgunit" in final_df.columns:
        final_df["is_orgunit"] = final_df["is_orgunit"].astype(str)
    if "defect_quantity" in final_df.columns:
        final_df["defect_quantity"] = final_df["defect_quantity"].astype(float)
    return final_df


def _ids(file_name, id_column, date_column, skiprows, from_year):
    """NC numbers of a list whose date (dd/mm/yyyy) is in from_year or later."""
    try:
        df = pd.read_csv(file_name, skiprows=skiprows)
        if id_column not in df.columns or date_column not in df.columns:
            print(f"❌ Error: Missing columns in {file_name}.")
            return set()
        dates = pd.to_datetime(df[date_column], format="%d/%m/%Y", errors="coerce")
        ids = df.loc[dates.dt.year >= from_year, id_column].dropna().astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        return set(ids[ids.str.isdigit()])
    except Exception as e:
        print(f"❌ Error processing {file_name}: {e}")
        return set()


def list_ids():
    """The NC numbers of both lists dated from config 'annee_listes_manuelles' on."""
    year = int(config.parameter("annee_listes_manuelles"))
    return (_ids(_src("liste_gps"), _src("liste_gps_colonne_numero"), _src("liste_gps_colonne_date"), int(_src("liste_gps_lignes_avant_entete")), year)
            | _ids(_src("liste_test"), _src("liste_test_colonne_numero"), _src("liste_test_colonne_date"), int(_src("liste_test_lignes_avant_entete")), year))
