"""Views page (Synthèse and Détail) from the current dashboard template, without rerunning the whole pipeline.

The page carries the main page's data (the two tables, rebuilt in the page as on the dashboard, with the production file and 2025), so it
takes that page's data block (03_reports/FTO2_NC_Dashboard.html, written by build_all.py) and writes 03_reports/FTO2_Vues.html and build/artifacts/FTO2_Vues.html
with the build's own page writer. build_all.py writes the same page on a full run.

    python3 -I build/build_vues.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_all   # noqa: E402   _page: the page writer shared by every dashboard page

src = open(os.path.join(ROOT, "03_reports", "FTO2_NC_Dashboard.html"), encoding="utf-8").read()
a = src.index("window.DASH = ") + len("window.DASH = ")
b = src.index(";\nwindow.FTO2_PAGE", a)
data = json.loads(src[a:b].replace("<\\/", "</"))
build_all._page("dashboard.html", data, "FTO2_Vues.html", page="vues", title="FTO2 · Synthèse et détail")
