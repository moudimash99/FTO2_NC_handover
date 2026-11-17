"""The Code Repository's reading of Skywise (fto2/transform_io.py): the filters the run uses, on polars tables typed as
Skywise types them (dates with a time zone, liability as a list)."""
import datetime as dt
import unittest

try:
    import polars as pl
except ImportError:   # polars is only needed in the Code Repository
    pl = None

from fto2 import transform_io as T


class Source:
    def __init__(self, df):
        self.df = df

    def polars(self, lazy=False):
        return self.df.lazy() if lazy else self.df


@unittest.skipIf(pl is None, "polars is not installed")
class TestReading(unittest.TestCase):
    def setUp(self):
        utc = dt.timezone.utc
        self.nc = pl.DataFrame({
            "plant": ["FTO2", "FTO2", "TO", "TO"],
            "creation_time": [dt.datetime(2025, 12, 31, 23, tzinfo=utc), dt.datetime(2026, 1, 2, tzinfo=utc),
                              dt.datetime(2026, 3, 1, tzinfo=utc), dt.datetime(2026, 3, 2, tzinfo=utc)],
            "liability": [["FTO2"], ["FTO2"], ["FTO2", "TO"], ["TO"]],
            "number": ["1", "2", "3", "4"],
        })
        self.Dataset, self.Column = T.bind({"nc": Source(self.nc), "out": None})

    def numbers(self, query):
        return list(query.select("number").read_table().number)

    def test_a_date_given_as_text(self):
        C = self.Column
        q = self.Dataset.get("nc").where((C.get("plant") == "FTO2") & (C.get("creation_time") >= "2026-01-01 00:00:00"))
        self.assertEqual(self.numbers(q), ["2"])

    def test_the_liability_list(self):
        C = self.Column
        q = self.Dataset.get("nc").where(C.get("plant") != "FTO2").where(C.array_contains("liability", "FTO2"))
        self.assertEqual(self.numbers(q), ["3"])

    def test_a_list_of_numbers(self):
        self.assertEqual(self.numbers(self.Dataset.get("nc").where(self.Column.get("number").isin(["2", "4"]))), ["2", "4"])

    def test_a_column_the_dataset_does_not_hold(self):
        t = self.Dataset.get("nc").select("number", "material").read_table()
        self.assertTrue(t.material.isna().all())

    def test_a_dataset_that_is_not_declared(self):
        with self.assertRaises(KeyError):
            self.Dataset.get("fto2_set_cost").read_table(format="pandas")
        with self.assertRaises(KeyError):
            self.Dataset.get("fto2_dash_cout").write_table(None)


if __name__ == "__main__":
    unittest.main()
