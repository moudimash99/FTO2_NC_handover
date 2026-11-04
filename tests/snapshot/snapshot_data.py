"""Record the data the build produces, so a change in the code can be checked against it.

    python3 -I tests/snapshot/snapshot_data.py <output folder>

Writes <output folder>/data.json.gz with:
  - every table the build writes to 05_outputs/ (CSV: header and rows as text; JSON as is);
  - the reference data the dashboard page receives (production plan, 2025 figures, codes, causes, cost settings,
    cables, MFT actions), read from the built page;
  - the data the MFT page receives.
Compare two folders with tests/snapshot/compare.py.
"""
import csv
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUTS = os.path.join(ROOT, "05_outputs")
TABLES = [
    "fto2_dash_nc.csv", "fto2_dash_defects.csv", "fto2_dash_disruptions.csv",
    "fto2_nc.csv", "fto2_defects.csv", "fto2_nc_cnq.csv", "fto2_defects_cnq.csv",
    "fto2_msn_semaine.csv", "mft_actions_seed.json",
]


def read_table(path):
    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def json_after(text, marker, end):
    """The JSON value written in a page right after `marker` and before `end`."""
    a = text.index(marker) + len(marker)
    b = text.index(end, a)
    return json.loads(text[a:b].replace("<\\/", "</"))


def page_data():
    out = {}
    with open(os.path.join(ROOT, "03_reports", "FTO2_NC_Dashboard.html"), encoding="utf-8") as f:
        page = f.read()
    dash = json_after(page, "window.DASH = ", ";\nwindow.FTO2_PAGE")
    out["dashboard.ref"] = dash.get("ref")
    with open(os.path.join(ROOT, "03_reports", "FTO2_MFT.html"), encoding="utf-8") as f:
        page = f.read()
    out["mft.data"] = json_after(page, "var D = ", ";\n")
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = sys.argv[1]
    os.makedirs(folder, exist_ok=True)
    data = {name: read_table(os.path.join(OUTPUTS, name)) for name in TABLES}
    data.update(page_data())
    with gzip.open(os.path.join(folder, "data.json.gz"), "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print("data snapshot: %d items -> %s" % (len(data), os.path.join(folder, "data.json.gz")))


if __name__ == "__main__":
    main()
