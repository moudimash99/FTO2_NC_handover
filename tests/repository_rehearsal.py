"""Rehearse the Code Repository transform on the laptop.

    python3 -I tests/repository_rehearsal.py [folder]

Runs build/repository/fto2_update.py (the transform, with a stand-in for transforms.api and polars inputs) on the same
data as tests/notebook_rehearsal.py, with the settings given as Fusion datasets would give them (the settings
spreadsheet), and the GPS register, the Test list, the cable tracker and the newest export of the Tableau Avances /
Retards pasted whole into their sheets, as they are, title rows included, as a sync gives such a sheet (its first row as
the column names, the real header a row of data). The plan's sheet has a title row with the export's date, as the notebook
dates the export by its file name. Then compares the tables it writes with the notebook's run: they must be the same.
Exits 1 if they are not.
"""
import csv
import importlib.util
import inspect
import io
import os
import shutil
import sys
import tempfile
import types

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("FTO2_CONFIG", os.path.join(ROOT, "config"))
import tests.notebook_rehearsal as R  # noqa: E402
from fto2 import downloads, fusion as F, manual_lists, transform_io  # noqa: E402

SHEET = os.path.join(ROOT, "03_reports", "skywise", "fusion", "FTO2 NC Dashboard - Settings.xlsx")


class FakeInput:
    """A lightweight transform input over a pandas table."""

    def __init__(self, df):
        self.df = df

    def polars(self, lazy=False):
        import polars as pl
        lf = pl.from_pandas(self.df).lazy()
        return lf if lazy else lf.collect()

    def pandas(self):
        return self.df.copy()


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


SHIPPED = ["non_conformity", "fto2_ai_labels", "work_order_operation", "mes_disruptions", "fto2_set_cost", "fto2_set_blackout",
           "fto2_set_part_prices", "fto2_set_cables", "fto2_set_gps", "fto2_set_test", "fto2_set_plan", "fto2_dash_nc",
           "fto2_dash_defects", "fto2_dash_disruptions", "fto2_dash_ref", "fto2_lines_to_label", "fto2_parts_to_price"]


def load_transform(folder):
    """build/repository/fto2_update.py as shipped, its inputs and outputs checked (named, no **kwargs, the same on both
    sides)."""
    path = os.path.join(folder, "fto2_update_shipped.py")
    shutil.copyfile(os.path.join(ROOT, "build", "repository", "fto2_update.py"), path)
    spec = importlib.util.spec_from_file_location("fto2_update_shipped", path)
    shipped = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shipped)
    names = list(inspect.signature(shipped.compute).parameters)
    assert names == SHIPPED and sorted(shipped.compute.io) == sorted(SHIPPED), "fto2_update.py declares %s" % names
    return shipped


def pasted(path, title=()):
    """A file pasted whole into a Fusion sheet, as it is (title rows above it), as the sheet's sync gives it: its first row
    as the column names (a blank cell gets a name of its own), the other rows as data, every cell as text."""
    rows = ([list(title)] if title else []) + list(csv.reader(io.StringIO(downloads._text(path), newline="")))
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    return pd.DataFrame(rows[1:], columns=[c if c.strip() else "Column %d" % (i + 1) for i, c in enumerate(rows[0])])


def main():
    nc_n, def_n, dis_n = R.run()
    notebook = dict(R.Dataset.written)
    tables, exports = R.stand_in()
    work = tempfile.mkdtemp(prefix="fto2_repo_rehearsal_")
    try:
        R.data_files(work, tables["non_conformity"], exports, downloads=True)
        data, files = os.path.join(work, "data"), os.path.join(work, "files")
        os.makedirs(files)
        shutil.copy(os.path.join(data, "fto2_station_mapping.csv"), files)
        transform_io.FILES, transform_io.SETTINGS = files, os.path.join(ROOT, "config")
        # the Fusion datasets: the settings tables of the spreadsheet; the lists and the plan pasted whole, as they are
        readme = pd.read_excel(SHEET, sheet_name="Read me", header=3)
        fusion = {d: pd.read_excel(SHEET, sheet_name=s) for d, s in zip(readme["Dataset"], readme["Sheet"]) if d not in F.PASTED}
        fusion["fto2_set_gps"] = pasted(os.path.join(work, manual_lists._src("liste_gps")))     # 3 title rows, then the header
        fusion["fto2_set_test"] = pasted(os.path.join(work, manual_lists._src("liste_test")))   # 2 title rows
        cables = [f for f in os.listdir(data) if "cables" in f.lower() and f.endswith(".csv")]
        fusion["fto2_set_cables"] = pasted(os.path.join(data, cables[0]), ["Suivi des demandes de câbles A30"])
        newest = sorted(f for f in os.listdir(data) if f.startswith("Avances_Retards"))[-1]   # 5 rows of legend above its header
        fusion["fto2_set_plan"] = pasted(os.path.join(data, newest),
                                         ["", "Tableau Avances / Retards au %s" % downloads._dmy(downloads.file_day(newest))])
        nc = tables["non_conformity"].copy()
        # the liability is a list in Skywise: a list for every NC (the comparison year's rows are still text here)
        nc["liability"] = nc["liability"].map(R._as_list).map(lambda v: v if isinstance(v, list) else [v] if isinstance(v, str) else None)
        inputs = {"non_conformity": FakeInput(nc), **{k: FakeInput(v) for k, v in tables.items() if k != "non_conformity"},
                  **{k: FakeInput(v) for k, v in fusion.items()}}
        outputs = {k: FakeOutput() for k in ("fto2_dash_nc", "fto2_dash_defects", "fto2_dash_disruptions", "fto2_dash_ref",
                                             "fto2_lines_to_label", "fto2_parts_to_price")}
        fake_transforms_api()
        fto2_update = load_transform(work)
        params = inspect.signature(fto2_update.compute).parameters
        fto2_update.compute(**{k: v for k, v in inputs.items() if k in params}, **outputs)
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
