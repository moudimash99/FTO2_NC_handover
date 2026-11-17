"""The update as a Code Repository transform (Python, lightweight: polars, no Spark).

fto2.skywise.run reads and writes Skywise through two objects, Dataset and Column, that the notebook gets from
foundry.transforms. A transform has inputs and outputs instead: bind() gives the same two objects over them, so the notebook
and the scheduled transform run exactly the same steps. run() does the whole update inside the transform:

    @transform.using(non_conformity=Input(...), ..., fto2_dash_nc=Output(...), ...)
    def compute(**datasets):
        from fto2 import transform_io
        transform_io.run(datasets)

The names of the inputs and outputs are the ones of fto2/settings/2_sources.csv (inputs), of the settings kept in Fusion
(fto2_set_..., see fto2/fusion.py) and of the tables the run writes. A dataset that is not declared raises KeyError when it
is read or written: the run treats the optional ones that way (a Fusion sheet not declared: its file is used) and says so.

Besides the datasets, the run needs two kinds of files, which the transform puts where the notebook has them (data/):
  - the station list, fto2/files/fto2_station_mapping.csv, kept in the repository;
  - the exports of the production plan (Tableau Avances / Retards), from the input fto2_plan_exports: a dataset holding the
    exports as files, one per download, the date at the end of each name. Without it, the plan stays as it was last read
    (fto2/settings/0_plan_msn.csv).
"""
import glob
import os
import shutil
import tempfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, "files")          # files kept with the code (the station list)
SETTINGS = os.path.join(HERE, "settings")    # the settings tables kept with the code
PLAN_EXPORTS = "fto2_plan_exports"


# ---------------------------------------------------------------- reading: a small filter language over polars
def _pl():
    import polars as pl
    return pl


def _schema(lf):
    try:
        return dict(lf.collect_schema())
    except AttributeError:   # polars before 1.0
        return dict(lf.schema)


def _literal(dtype, value):
    """A value to compare with a column of this type: a text date becomes a date when the column holds dates."""
    pl = _pl()
    if isinstance(value, str) and dtype is not None and dtype.is_temporal():
        t = pd.Timestamp(value)
        if dtype == pl.Date:
            return pl.lit(t.date())
        tz = getattr(dtype, "time_zone", None)
        unit = getattr(dtype, "time_unit", None) or "us"
        if t.tzinfo:   # a date given with its zone: compared in UTC
            t = t.tz_convert("UTC").tz_localize(None)
        lit = pl.lit(t.to_pydatetime()).cast(pl.Datetime(unit))
        return lit.dt.replace_time_zone(tz) if tz else lit
    if isinstance(value, str) and dtype is not None and dtype.is_numeric():
        try:
            return pl.lit(float(value))
        except ValueError:
            return pl.lit(value)
    return pl.lit(value)


class _Condition:
    """A condition on the rows, turned into a polars expression once the table's columns are known."""

    def __init__(self, make):
        self.make = make   # make(schema) -> polars expression

    def __and__(self, other):
        return _Condition(lambda s: self.make(s) & other.make(s))

    def __or__(self, other):
        return _Condition(lambda s: self.make(s) | other.make(s))

    def __invert__(self):
        return _Condition(lambda s: ~self.make(s))


class _Col:
    def __init__(self, name):
        self.name = name

    def _compare(self, op, value):
        def make(schema):
            c = _pl().col(self.name)
            return op(c, _literal(schema.get(self.name), value))
        return _Condition(make)

    def __eq__(self, value):
        return self._compare(lambda c, v: c == v, value)

    def __ne__(self, value):
        return self._compare(lambda c, v: c != v, value)

    def __ge__(self, value):
        return self._compare(lambda c, v: c >= v, value)

    def __gt__(self, value):
        return self._compare(lambda c, v: c > v, value)

    def __le__(self, value):
        return self._compare(lambda c, v: c <= v, value)

    def __lt__(self, value):
        return self._compare(lambda c, v: c < v, value)

    def isin(self, values):
        def make(schema):
            pl, values_ = _pl(), list(values)
            dtype = schema.get(self.name)
            if dtype is not None and dtype.is_numeric():
                values_ = [float(v) for v in values_ if str(v).replace(".", "", 1).isdigit()]
                return pl.col(self.name).cast(pl.Float64).is_in(values_)
            return pl.col(self.name).cast(pl.String).is_in([str(v) for v in values_])
        return _Condition(make)

    __hash__ = object.__hash__


class Column:
    @staticmethod
    def get(name):
        return _Col(name)

    @staticmethod
    def array_contains(name, value):
        """Rows whose column holds the value: a list column that contains it, or a text equal to it or written as a list
        ('[A, B]'). Filtered before the rows are read."""
        def make(schema):
            pl = _pl()
            dtype = schema.get(name)
            if isinstance(dtype, pl.List):
                return pl.col(name).list.contains(value)
            if isinstance(dtype, pl.Array):
                return pl.col(name).arr.contains(value)
            text = pl.col(name).cast(pl.String)
            return (text == value) | text.str.contains(r"(^|[\[,\s])%s($|[\],\s])" % value)
        return _Condition(make)


class _Query:
    """A dataset being read, as foundry.transforms gives it: where(...).select(...).read_table(format="pandas")."""

    def __init__(self, lf):
        self._lf = lf

    def where(self, condition):
        return _Query(self._lf.filter(condition.make(_schema(self._lf))))

    def select(self, *columns):
        pl = _pl()
        have = _schema(self._lf)   # a column the dataset does not hold comes out empty instead of stopping the run
        return _Query(self._lf.select([pl.col(c) if c in have else pl.lit(None, dtype=pl.String).alias(c) for c in columns]))

    def read_table(self, format="pandas"):
        return self._lf.collect().to_pandas()


def _lazy(source):
    """A transform input as a polars LazyFrame, whatever this version of the API offers."""
    pl = _pl()
    if hasattr(source, "polars"):
        try:
            return source.polars(lazy=True)
        except TypeError:
            return source.polars().lazy()
    return pl.from_pandas(source.pandas()).lazy()


def bind(datasets):
    """(Dataset, Column) for fto2.skywise.run, over the transform's inputs and outputs ({name: input or output})."""

    class _Handle:
        def __init__(self, name):
            self.name = name

        def _input(self):
            source = datasets.get(self.name)
            if source is None or not (hasattr(source, "polars") or hasattr(source, "pandas")):
                raise KeyError("the dataset '%s' is not an input of the transform" % self.name)
            return _Query(_lazy(source))

        def where(self, condition):
            return self._input().where(condition)

        def select(self, *columns):
            return self._input().select(*columns)

        def read_table(self, format="pandas"):
            return self._input().read_table(format)

        def write_table(self, df):
            out = datasets.get(self.name)
            if out is None or not hasattr(out, "write_table"):
                raise KeyError("the dataset '%s' is not an output of the transform" % self.name)
            try:
                out.write_table(df)
            except (TypeError, ValueError):   # a version that takes polars tables only
                out.write_table(_pl().from_pandas(df))

    class Dataset:
        @staticmethod
        def get(name):
            return _Handle(name)

        @staticmethod
        def has(name):
            """True when the transform declares this dataset (input or output)."""
            return datasets.get(name) is not None

    return Dataset, Column


# ---------------------------------------------------------------- files
def copy_files(source, folder, suffix=".csv"):
    """Copy the files of a dataset of files (input) into a folder. Returns their names."""
    names = []
    try:
        root = source.path()   # the dataset's files on the local disk
    except Exception:
        root = None
    if root and os.path.isdir(root):
        for d, _, files in os.walk(root):
            for f in files:
                if f.lower().endswith(suffix):
                    shutil.copyfile(os.path.join(d, f), os.path.join(folder, f))
                    names.append(f)
        return names
    fs = source.filesystem()
    for status in fs.ls():
        if status.path.lower().endswith(suffix):
            name = os.path.basename(status.path)
            with fs.open(status.path, "rb") as r, open(os.path.join(folder, name), "wb") as w:
                shutil.copyfileobj(r, w)
            names.append(name)
    return names


# ---------------------------------------------------------------- the whole update
def run(datasets, say=None):
    """The update inside a transform: the notebook's layout rebuilt in a working folder (data/ with the station list and
    the plan exports), the settings kept in Fusion read over those of the repository, then the same run as the notebook.
    Returns the three dashboard tables."""
    import time
    t0 = time.time()
    say = say or (lambda msg: print("[%6.1f s] %s" % (time.time() - t0, msg), flush=True))
    work = tempfile.mkdtemp(prefix="fto2_update_")
    data = os.path.join(work, "data")
    os.makedirs(data)
    for f in glob.glob(os.path.join(FILES, "*")):
        shutil.copyfile(f, os.path.join(data, os.path.basename(f)))
    if not os.path.exists(os.path.join(data, "fto2_station_mapping.csv")):
        raise FileNotFoundError("the station list is missing: put fto2_station_mapping.csv (the notebook's data/ file) "
                                "in fto2/files/ of the repository")
    if PLAN_EXPORTS in datasets:
        names = copy_files(datasets[PLAN_EXPORTS], data)
        say("Production plan: %d export(s) read from %s" % (len(names), PLAN_EXPORTS))
    else:
        say("Production plan: no input %s, the plan stays as last read (0_plan_msn.csv)" % PLAN_EXPORTS)
    os.environ.pop("FTO2_FUSION_FROM", None)
    os.environ["FTO2_CONFIG"] = SETTINGS
    Dataset, Column_ = bind(datasets)
    here = os.getcwd()
    os.chdir(work)
    try:
        from . import fusion
        fusion.load(Dataset, say)   # first: some settings are read as soon as the rest of the code is loaded
        from . import skywise
        return skywise.run(Dataset, Column_, say=say, old_outputs=False)
    finally:
        os.chdir(here)
        shutil.rmtree(work, ignore_errors=True)
