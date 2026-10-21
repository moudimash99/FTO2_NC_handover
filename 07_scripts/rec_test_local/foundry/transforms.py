"""Local stand-in for foundry.transforms: serves the exported NCs as the non_conformity dataset."""
import pandas as pd

DATA = None          # set by the runner


class _Expr:
    def __init__(self, f): self.f = f
    def __and__(self, o): return _Expr(lambda d: self.f(d) & o.f(d))
    def __or__(self, o): return _Expr(lambda d: self.f(d) | o.f(d))


class _Col:
    def __init__(self, n): self.n = n
    def __eq__(self, v): return _Expr(lambda d: d[self.n] == v)
    def __ne__(self, v): return _Expr(lambda d: d[self.n] != v)
    def __ge__(self, v): return _Expr(lambda d: d[self.n] >= pd.Timestamp(v))
    def isin(self, vs): return _Expr(lambda d: d[self.n].isin(list(vs)))


class Column:
    @staticmethod
    def get(n): return _Col(n)


class _Query:
    def __init__(self, df): self.df = df
    def where(self, e): return _Query(self.df[e.f(self.df).fillna(False).astype(bool)])
    def select(self, *cols):
        missing = [c for c in cols if c not in self.df.columns]
        if missing: raise KeyError(f"columns not in dataset: {missing}")
        return _Query(self.df[list(cols)])
    def read_table(self, format="pandas"):
        Dataset.calls += 1
        return self.df.reset_index(drop=True).copy()


class Dataset:
    calls = 0
    @staticmethod
    def get(name):
        assert name == "non_conformity", name
        return _Query(DATA)
