"""Rehearse the Skywise notebook on the laptop.

    python3 -I tests/notebook_rehearsal.py

Runs fto2/skywise.py (exactly what the notebook runs) against a stand-in for Skywise that serves the local files:
  non_conformity        the NCs of the pipeline exports in 06_input_data (their Skywise columns, liability as a list)
  fto2_ai_labels        04_reference/llm_labels_longtext.csv
  work_order_operation  06_input_data/wo_s03_operations_fto2_*.csv.gz
  mes_disruptions       06_input_data/mes_disruptions_fto2_*.csv.gz
  data/                 a station mapping made from the exports, and a GPS register listing the NCs of the missing-IDs export
Then compares the tables it writes with the laptop build's (05_outputs/fto2_dash_*.csv) on the same NCs.
Prints the differences and exits 1 if there are any.
"""
import glob
import os
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("FTO2_CONFIG", os.path.join(ROOT, "config"))
from fto2 import skywise  # noqa: E402


# ---------------------------------------------------------------- the stand-in for foundry.transforms
class Column:
    def __init__(self, test):
        self.test = test

    @staticmethod
    def get(name):
        return _Col(name)

    def __and__(self, other):
        return Column(lambda df: self.test(df) & other.test(df))


class _Col:
    def __init__(self, name):
        self.name = name

    def __eq__(self, v):
        return Column(lambda df: df[self.name].astype(str) == str(v))

    def __ne__(self, v):
        return Column(lambda df: df[self.name].astype(str) != str(v))

    def __ge__(self, v):
        return Column(lambda df: pd.to_datetime(df[self.name], utc=True, errors="coerce", format="mixed") >= pd.Timestamp(v, tz="UTC")
                      if "time" in self.name else df[self.name] >= v)

    def __lt__(self, v):
        return Column(lambda df: pd.to_datetime(df[self.name], utc=True, errors="coerce", format="mixed") < pd.Timestamp(v, tz="UTC")
                      if "time" in self.name else df[self.name] < v)

    def isin(self, values):
        return Column(lambda df: df[self.name].astype(str).isin([str(v) for v in values]))


class _Query:
    def __init__(self, df):
        self.df = df

    def where(self, cond):
        return _Query(self.df[cond.test(self.df)])

    def select(self, *cols):
        out = self.df.copy()
        for c in cols:
            if c not in out.columns:
                out[c] = np.nan
        return _Query(out[list(cols)])

    def read_table(self, format="pandas"):
        return self.df.reset_index(drop=True).copy()


class Dataset:
    tables = {}
    written = {}

    def __init__(self, name):
        self.name = name

    @classmethod
    def get(cls, name):
        return cls(name)

    def where(self, cond):
        return _Query(self.tables[self.name]).where(cond)

    def read_table(self, format="pandas"):
        return self.tables[self.name].copy()

    def write_table(self, df):
        self.written[self.name] = df.copy()


def _as_list(v):
    """'[FTO2, TO]' -> ['FTO2', 'TO'], as Skywise gives the liability."""
    if not isinstance(v, str) or not v.startswith("["):
        return v
    return [x.strip().strip("'\"") for x in v.strip("[]").split(",") if x.strip()]


def main():
    exports = [pd.read_csv(f, low_memory=False, dtype=str) for f in sorted(glob.glob(os.path.join(ROOT, "06_input_data", "fto2_dashboard_data*.csv")))]
    nc = pd.concat(exports, ignore_index=True).drop_duplicates("notification_number")
    nc["liability"] = nc["liability"].map(_as_list)
    nc["notification_number"] = nc["notification_number"].astype(str).str.replace(r"\.0$", "", regex=True)
    # the material of each NC (the Skywise dataset holds it; the exports were made before it was read): from the raw extracts
    for f in sorted(glob.glob(os.path.join(ROOT, "06_input_data", "nc_2026_skywise_*.csv*"))):
        raw = pd.read_csv(f, dtype=str, low_memory=False)
        raw["notification_number"] = raw["notification_number"].astype(str).str.replace(r"\.0$", "", regex=True).str.lstrip("0")
        for c in ("material", "material_description_fr", "material_description_en"):
            known = nc["notification_number"].map(raw.dropna(subset=[c]).set_index("notification_number")[c])
            nc[c] = nc[c].where(nc[c].notna(), known) if c in nc.columns else known
    y25 = pd.read_csv(os.path.join(ROOT, "06_input_data", "nc_2025_skywise_fto2.csv.gz"), dtype=str, keep_default_na=False, na_values=[""])
    nc = pd.concat([nc, y25[~y25.notification_number.isin(nc.notification_number)]], ignore_index=True)   # the 2025 NCs, for the comparison year
    Dataset.tables = {
        "non_conformity": nc,
        "fto2_ai_labels": pd.read_csv(os.path.join(ROOT, "04_reference", "llm_labels_longtext.csv"), dtype={"notification_number": str}, encoding="utf-8-sig"),
        "work_order_operation": pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False, na_values=[""])
                                           for f in sorted(glob.glob(os.path.join(ROOT, "06_input_data", "wo_s03_operations_fto2_*.csv.gz")))]),
        "mes_disruptions": pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False, na_values=[""])
                                      for f in sorted(glob.glob(os.path.join(ROOT, "06_input_data", "mes_disruptions_fto2_*.csv.gz")))]),
    }
    work = tempfile.mkdtemp(prefix="fto2_rehearsal_")
    here = os.getcwd()
    try:
        os.makedirs(os.path.join(work, "data"))
        # station mapping in the notebook's wide form, from the exports' station / description pairs
        pairs = nc[["station", "station_description", "programme"]].dropna(subset=["station"]).drop_duplicates("station")
        wide = {}
        for line, pat in (("A320", "32"), ("A330", "330"), ("A350", "350"), ("A400M", "400|MT")):
            p = pairs[pairs.programme.fillna("").str.contains(pat)]
            wide["STATION " + line] = list(p.station)
            wide["Désignations " + line] = list(p.station_description)
        n = max(len(v) for v in wide.values())
        pd.DataFrame({k: v + [None] * (n - len(v)) for k, v in wide.items()}).to_csv(os.path.join(work, "data", "fto2_station_mapping.csv"), index=False)
        # the GPS register and the Test list rebuilt from the exports' list columns (the real files stay in Skywise), with the
        # header lines the real files have; every listed NC dated in 2026 so that the run fetches the ones the selection misses
        allx = pd.concat(exports, ignore_index=True).drop_duplicates("notification_number")
        allx["num"] = allx["notification_number"].astype(str).str.replace(r"\.0$", "", regex=True)
        g = allx[allx.Ext_Source == "GPS"]
        with open(os.path.join(work, "data", "GPS NC INT_SERIE ELEC 2026 - NC REGISTRE.csv"), "w", encoding="utf-8") as f:
            f.write("x\nx\nx\n")
            pd.DataFrame({"N°  NC / AM / AF": g.num, " Date SAP": "15/03/2026", "Produit": g.Ext_Produit,
                          "Nombre total retouches": g.Ext_Nb_Defauts, "Non conformité constatée": g.Ext_Defaut_Constate,
                          "Type NC": g.GPS_Type_NC, "Statut décision": g.GPS_Statut_decision, "IMPUTATION \n(après analyse)": g.GPS_Imputation,
                          "Nombre de retouches majeures": g.GPS_Retouches_majeures, "Nombre de retouches mineures": g.GPS_Retouches_mineures}).to_csv(f, index=False)
        t = allx[allx.Ext_Source == "Test"]
        with open(os.path.join(work, "data", "NC TEST - NC.csv"), "w", encoding="utf-8") as f:
            f.write("x\nx\n")
            pd.DataFrame({"N° NC": t.num, "Dates": "15/03/2026", "Produit": t.Ext_Produit, "VU\nuniquement PTVU": "",
                          "Nb défaut": t.Ext_Nb_Defauts, "Défaut majeur": t.Ext_Defaut_Constate}).to_csv(f, index=False)
        os.chdir(work)
        nc_t, def_t, dis_t = skywise.run(Dataset, Column)
    finally:
        os.chdir(here)
        shutil.rmtree(work, ignore_errors=True)

    # compare with the laptop build on the NCs both hold
    lap_nc = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_nc.csv"), dtype=str, keep_default_na=False)
    lap_def = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_defects.csv"), dtype=str, keep_default_na=False)
    got = nc_t.astype(str).replace({"nan": "", "None": ""}).set_index("nc")
    lap = lap_nc.set_index("nc")
    both = sorted(set(got.index) & set(lap.index))
    print("\nrehearsal: %d NCs written; laptop: %d; in both: %d (the laptop also reads the raw extracts)" % (len(got), len(lap), len(both)))
    bad = 0
    # 'origin' (normal / missing_ids) is left out: the exports were made while the selection still kept only 1,000 NCs, so some
    # NCs came in as missing IDs that today's selection catches directly
    for c in ["line", "plant", "scope", "phase", "product", "type_nc", "liability", "on_aec", "defect_lines", "cost_total", "cost_work", "source"]:
        a, b = got.loc[both, c], lap.loc[both, c]
        num = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        diff = ~((a == b) | ((num[0] - num[1]).abs() < 0.01))
        if diff.sum():
            bad += 1
            print("  %s: %d NCs differ, e.g. %s" % (c, diff.sum(), list(zip(a[diff].index[:3], a[diff][:3], b[diff][:3]))))
    nd = def_t[def_t.nc.astype(str).isin(both)]
    ld = lap_def[lap_def.nc.isin(both)]
    print("defect lines on those NCs: rehearsal %d, laptop %d" % (len(nd), len(ld)))
    if len(nd) != len(ld):
        bad += 1
    # the reference data: the same blocks as the laptop build's 05_outputs/fto2_dash_ref.csv
    import json
    def blocks(t):
        t = t.astype({"morceau": int})
        return {p: json.loads("".join(g.sort_values("morceau").texte)) for p, g in t.groupby("partie")}
    lap_ref = blocks(pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_ref.csv"), dtype={"texte": str}, keep_default_na=False))
    got_ref = blocks(Dataset.written["fto2_dash_ref"])
    for part in lap_ref:
        for k in lap_ref[part]:
            same = lap_ref[part][k] == got_ref.get(part, {}).get(k)
            if not same:
                bad += 1
                print("  reference %s > %s differs" % (part, k))
    print("reference data: %d blocks compared" % sum(len(v) for v in lap_ref.values()))
    print("written datasets:", sorted(Dataset.written))
    print("OK: the notebook gives the laptop's figures" if not bad else "DIFFERENCES above")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
