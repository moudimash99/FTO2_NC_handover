"""The everyday tables written from a raw file (fto2/everyday_tables.py): what a new file replaces and what it keeps.

    python3 -m unittest discover -s tests -t .
"""
import contextlib
import io
import os
import shutil
import tempfile
import unittest

import pandas as pd

from fto2 import config, everyday_tables


class Write(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="fto2_everyday_")
        self.before = os.environ.get("FTO2_CONFIG")
        os.environ["FTO2_CONFIG"] = self.folder
        self.quiet = contextlib.redirect_stdout(io.StringIO())   # write() says what it kept
        self.quiet.__enter__()

    def tearDown(self):
        self.quiet.__exit__(None, None, None)
        if self.before is None:
            del os.environ["FTO2_CONFIG"]
        else:
            os.environ["FTO2_CONFIG"] = self.before
        shutil.rmtree(self.folder, ignore_errors=True)

    def rows(self, *rows):
        return pd.DataFrame(list(rows), columns=["ligne", "produit", "msn", "depart"])

    def table(self):
        t = config.table("1_test.csv")
        return sorted(map(tuple, t[["msn", "depart", "source"]].values))

    def test_a_new_file_replaces_the_rows_it_holds(self):
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "801", "2026-01-10"], ["A350", "MIP", "802", ""]), key=["ligne", "produit", "msn"])
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "802", "2026-02-10"]), key=["ligne", "produit", "msn"])
        self.assertEqual(self.table(), [("802", "2026-02-10", "auto")])

    def test_rows_that_left_the_file_can_be_kept(self):
        """The production plan: an aircraft delivered months ago is no longer in the export, and keeps its row."""
        k = ["ligne", "produit", "msn"]
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "801", "2026-01-10"], ["A350", "MIP", "802", ""]), key=k, keep=k)
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "802", "2026-02-10"], ["A350", "MIP", "803", ""]), key=k, keep=k)
        self.assertEqual(self.table(), [("801", "2026-01-10", "auto"), ("802", "2026-02-10", "auto"), ("803", "", "auto")])

    def test_only_the_rows_wanted_are_kept(self):
        """The production plan again: a row that left the export before its delivery has left the plan."""
        k = ["ligne", "produit", "msn"]
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "801", "2026-01-10"], ["A350", "MIP", "802", "2027-03-01"]), key=k, keep=k)
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "803", ""]), key=k, keep=k, keep_if=lambda r: r["depart"] < "2026-11-03")
        self.assertEqual(self.table(), [("801", "2026-01-10", "auto"), ("803", "", "auto")])

    def test_a_row_corrected_by_hand_stays(self):
        k = ["ligne", "produit", "msn"]
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "801", "2026-01-10"]), key=k, keep=k)
        t = config.table("1_test.csv")
        t.loc[0, ["depart", "source"]] = ["2026-01-12", "manuel"]
        t.to_csv(config.path("1_test.csv"), sep=";", index=False, encoding="utf-8")
        everyday_tables.write("1_test.csv", self.rows(["A350", "MIP", "801", "2026-01-10"], ["A350", "MIP", "802", ""]), key=k, keep=k)
        self.assertEqual(self.table(), [("801", "2026-01-12", "manuel"), ("802", "", "auto")])


if __name__ == "__main__":
    unittest.main()
