"""Rehearse the Code Repository transform on the laptop.

    python3 -I tests/repository_rehearsal.py [folder]

Runs build/repository/fto2_update.py (the transform, with a stand-in for transforms.api and polars inputs) on the same
data as tests/notebook_rehearsal.py, with the settings and the lists given as Fusion datasets would give them (the settings
spreadsheet; the GPS register, the Test list and the cable tracker with their column names written as a sync may write
them) and the production plan exports as a dataset of files. Then compares the tables it writes with the notebook's run:
they must be the same. Exits 1 if they are not.
"""
import os
import re
import shutil
import sys
import tempfile
import types

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("FTO2_CONFIG", os.path.join(ROOT, "config"))
import tests.notebook_rehearsal as R  # noqa: E402
from fto2 import config, manual_lists, transform_io  # noqa: E402

SHEET = os.path.join(ROOT, "03_reports", "skywise", "fusion", "FTO2 NC Dashboard - Settings.xlsx")


class FakeInput:
    """A lightweight transform input over a pandas table."""

    def __init__(self, df=None, folder=None):
        self.df, self.folder = df, folder

    def polars(self, lazy=False):
        import polars as pl
        lf = pl.from_pandas(self.df).lazy()
        return lf if lazy else lf.collect()

    def pandas(self):
        return self.df.copy()

    def path(self):
        return self.folder


class FakeOutput:
    def __init__(self):
        self.df = None

    def write_table(self, df):
        self.df = df.copy()


def fake_transforms_api():
    """transforms.api as the transform imports it: Input, Output, transform.using."""
    api = types.ModuleType("transforms.api")
    api.Input = api.Output = lambda where: where
    api.LightweightInput = api.LightweightOutput = object

    class transform:
        @staticmethod
        def using(**io):
            def wrap(f):
                f.io = io
                return f
            return wrap
    api.transform = transform
    sys.modules["transforms"] = types.ModuleType("transforms")
    sys.modules["transforms.api"] = api


def synced(df):
    """Column names as a sync may write them: signs and accented letters replaced."""
    return df.set_axis([re.sub(r"[^0-9A-Za-z]", "_", str(c)) for c in df.columns], axis=1)


def main():
    nc_n, def_n, dis_n = R.run()
    notebook = dict(R.Dataset.written)
    tables, exports = R.stand_in()
    work = tempfile.mkdtemp(prefix="fto2_repo_rehearsal_")
    try:
        R.data_files(work, tables["non_conformity"], exports, downloads=True)
        data = os.path.join(work, "data")
        files, plan = os.path.join(work, "files"), os.path.join(work, "plan")
        os.makedirs(files)
        os.makedirs(plan)
        shutil.copy(os.path.join(data, "fto2_station_mapping.csv"), files)
        for f in os.listdir(data):
            if f.startswith("Avances_Retards"):
                shutil.copy(os.path.join(data, f), plan)
        transform_io.FILES, transform_io.SETTINGS = files, os.path.join(ROOT, "config")
        # the Fusion datasets
        readme = pd.read_excel(SHEET, sheet_name="Read me", header=3)
        fusion = {d: pd.read_excel(SHEET, sheet_name=s) for d, s in zip(readme["Dataset"], readme["Sheet"])
                  if d not in ("fto2_set_gps", "fto2_set_test", "fto2_set_cables")}
        gps = pd.read_csv(os.path.join(work, manual_lists._src("liste_gps")), skiprows=3, dtype=str)
        gps[" Date SAP"] = pd.to_datetime(gps[" Date SAP"], format="%d/%m/%Y")
        test = pd.read_csv(os.path.join(work, manual_lists._src("liste_test")), skiprows=2, dtype=str)
        cables = [f for f in os.listdir(data) if "cables" in f.lower() and f.endswith(".csv")]
        fusion["fto2_set_gps"], fusion["fto2_set_test"] = synced(gps), synced(test)
        fusion["fto2_set_cables"] = synced(pd.read_csv(os.path.join(data, cables[0]), dtype=str, keep_default_na=False))
        nc = tables["non_conformity"].copy()
        # the liability is a list in Skywise: a list for every NC (the comparison year's rows are still text here)
        nc["liability"] = nc["liability"].map(R._as_list).map(lambda v: v if isinstance(v, list) else [v] if isinstance(v, str) else None)
        inputs = {"non_conformity": FakeInput(nc), **{k: FakeInput(v) for k, v in tables.items() if k != "non_conformity"},
                  **{k: FakeInput(v) for k, v in fusion.items()}, "fto2_plan_exports": FakeInput(folder=plan)}
        outputs = {k: FakeOutput() for k in ("fto2_dash_nc", "fto2_dash_defects", "fto2_dash_disruptions", "fto2_dash_ref",
                                             "fto2_lines_to_label", "fto2_parts_to_price")}
        fake_transforms_api()
        sys.path.insert(0, os.path.join(ROOT, "build", "repository"))
        import fto2_update
        fto2_update.compute(**inputs, **outputs)
    finally:
        shutil.rmtree(work, ignore_errors=True)
        os.environ["FTO2_CONFIG"] = os.path.join(ROOT, "config")
        os.environ.pop("FTO2_FUSION_FROM", None)
    if len(sys.argv) > 1:   # a folder: both versions of each table, to look at the differences
        os.makedirs(sys.argv[1], exist_ok=True)
        for name in ("fto2_dash_nc", "fto2_dash_defects", "fto2_dash_ref"):
            notebook[name].to_pickle(os.path.join(sys.argv[1], name + "_notebook.pkl"))
            outputs[name].df.to_pickle(os.path.join(sys.argv[1], name + "_transform.pkl"))
    bad = 0
    print()
    for name in ("fto2_dash_nc", "fto2_dash_defects", "fto2_dash_disruptions", "fto2_dash_ref"):
        a = notebook[name].astype(str).fillna("").reset_index(drop=True)   # two empty cells are the same
        b = outputs[name].df.astype(str).fillna("").reset_index(drop=True)
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            bad += 1
            print("%s: shape differs: notebook %s, transform %s" % (name, a.shape, b.shape))
            continue
        kinds = [(c, str(notebook[name][c].dtype), str(outputs[name].df[c].dtype)) for c in a.columns
                 if str(notebook[name][c].dtype) != str(outputs[name].df[c].dtype)]
        if kinds:   # the column types decide the dataset's schema, which the Slate queries read
            bad += 1
            print("%s: column types differ: %s" % (name, kinds))
        diff = [(c, int((a[c] != b[c]).sum())) for c in a.columns if (a[c] != b[c]).any()]
        print("%s: %d rows, %s" % (name, len(a), "identical" if not diff else "differences in %s" % diff))
        bad += bool(diff)
    for name in ("fto2_lines_to_label", "fto2_parts_to_price"):
        print("%s: %s rows" % (name, None if outputs[name].df is None else len(outputs[name].df)))
    print("OK: the transform gives the notebook's tables" if not bad else "DIFFERENCES above")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
