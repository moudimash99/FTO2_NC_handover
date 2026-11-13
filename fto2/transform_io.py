"""Data access for a Code Repository transform (Python transforms, Spark).

fto2.skywise.run reads and writes Skywise through two objects, Dataset and Column, that the notebook gets from
foundry.transforms. A transform has inputs and outputs instead: bind() gives the same two objects over them, so the notebook
and the scheduled pipeline run exactly the same steps.

    Dataset, Column = transform_io.bind(ctx.spark_session, inputs={"non_conformity": nc_input, ...}, outputs={"fto2_dash_nc": nc_output, ...})
    skywise.run(Dataset, Column)

The names are the ones of data/config/2_sources.csv (inputs) and of the tables the run writes (outputs). A dataset that is not
declared raises KeyError: the run treats its optional outputs that way and says so.
"""
import math

import pandas as pd

# column types of the tables the run writes, as (name, type) with type text, int, num or date; a table that is not listed
# is written with types read from its pandas columns
SCHEMAS = {}


def _schemas():
    if not SCHEMAS:
        from . import core
        from .cost import explain
        short = lambda cols: [(c[0], c[1]) for c in cols]
        SCHEMAS.update({
            "fto2_dash_nc": short(core.NC_COLUMNS), "fto2_dash_defects": short(core.DEF_COLUMNS),
            "fto2_dash_disruptions": short(core.DIS_COLUMNS), "fto2_dash_cout": short(explain.COLUMNS),
            "fto2_dash_ref": [("partie", "text"), ("morceau", "int"), ("texte", "text")],
        })
    return SCHEMAS


def _missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NaT or v is pd.NA


def _cell(v, kind):
    """A pandas value as the Python value Spark takes for a column of this type; None when empty."""
    if _missing(v):
        return None
    if kind == "int":
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None
    if kind == "num":
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        return None if math.isnan(f) else f
    return str(v)


def _kinds(name, df):
    known = dict(_schemas().get(name, []))
    out = []
    for c in df.columns:
        if c in known:
            out.append((c, known[c]))
        elif pd.api.types.is_bool_dtype(df[c]) or pd.api.types.is_integer_dtype(df[c]):
            out.append((c, "int"))
        elif pd.api.types.is_float_dtype(df[c]):
            out.append((c, "num"))
        else:
            out.append((c, "text"))
    return out


def to_spark(spark, name, df):
    """A pandas table as a Spark table with fixed column types (text, whole number, decimal), whatever its values."""
    from pyspark.sql import types as T
    kinds = _kinds(name, df)
    spark_type = {"int": T.LongType(), "num": T.DoubleType()}
    schema = T.StructType([T.StructField(c, spark_type.get(k, T.StringType()), True) for c, k in kinds])
    columns = [[_cell(v, k) for v in df[c].tolist()] for c, k in kinds]
    return spark.createDataFrame(list(zip(*columns)) if columns else [], schema)


class _Query:
    """A dataset being filtered, as foundry.transforms gives it: where(...).select(...).read_table(format="pandas")."""

    def __init__(self, sdf):
        self._sdf = sdf

    def where(self, condition):
        if callable(condition):   # a condition that needs the table's columns (see Column.array_contains)
            condition = condition(self._sdf)
        return _Query(self._sdf.filter(condition))

    def select(self, *columns):
        from pyspark.sql import functions as F
        have = set(self._sdf.columns)   # a column the dataset does not hold comes out empty instead of stopping the run
        return _Query(self._sdf.select(*[F.col(c) if c in have else F.lit(None).cast("string").alias(c) for c in columns]))

    def read_table(self, format="pandas"):
        return self._sdf.toPandas()


def bind(spark, inputs, outputs):
    """(Dataset, Column) for fto2.skywise.run. inputs: {name: transform input}, outputs: {name: transform output}."""
    from pyspark.sql import functions as F

    class _Handle:
        def __init__(self, name):
            self.name = name

        def _input(self):
            if self.name not in inputs:
                raise KeyError("the dataset '%s' is not an input of the transform" % self.name)
            return _Query(inputs[self.name].dataframe())

        def where(self, condition):
            return self._input().where(condition)

        def select(self, *columns):
            return self._input().select(*columns)

        def read_table(self, format="pandas"):
            return self._input().read_table(format)

        def write_table(self, df):
            if self.name not in outputs:
                raise KeyError("the dataset '%s' is not an output of the transform" % self.name)
            outputs[self.name].write_dataframe(to_spark(spark, self.name, df))

    class Dataset:
        @staticmethod
        def get(name):
            return _Handle(name)

    class Column:
        @staticmethod
        def get(name):
            return F.col(name)

        @staticmethod
        def array_contains(name, value):
            """Rows whose column holds the value: a list column that contains it, or a text column equal to it or written
            as a list ('[A, B]'). Spark filters before the rows are read."""
            def condition(sdf):
                kind = dict(sdf.dtypes).get(name, "string")
                if kind.startswith("array"):
                    return F.array_contains(F.col(name), value)
                return (F.col(name) == value) | F.col(name).rlike(r"(^|[\[,\s])%s($|[\],\s])" % value)
            return condition

    return Dataset, Column
