"""Pages to try the dashboard's Slate set-ups on the laptop, with tests/slate/fake_slate.js standing in for Slate.

    python3 -I tests/slate/make_pages.py <output folder>

Writes <output folder>/<set-up>/FTO2_NC_Dashboard.html, the Skywise page (03_reports/skywise/level3_datasets) in three set-ups:

    sans_fonction   the page computes everything                                    state.json
    3_fonctions     targets, alarms and cost explanation from three Slate functions  fonctions/state_3_fonctions.json
    2_fonctions     targets and alarms from two Slate functions, the cost explanation
                    from the notebook's table fto2_dash_cout                         fonctions/state_2_fonctions.json

Each holds the laptop data (05_outputs/, written by build/build_all.py) as Slate gives a query result. Take a snapshot of each
page (FTO2_PAGES=<output folder>/<set-up> node tests/snapshot/snapshot_pages.js ...) and compare it with tests/golden: the
figures must be the same as the laptop page's.
"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
L3 = os.path.join(ROOT, "03_reports", "skywise", "level3_datasets")
FN = os.path.join(L3, "fonctions")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "build"))
from fto2.core import NC_COLUMNS, DEF_COLUMNS, DIS_COLUMNS  # noqa: E402
from fto2.cost.explain import COLUMNS as COUT_COLUMNS  # noqa: E402
import skywise_pack as SP  # noqa: E402

SETUPS = {
    "sans_fonction": (os.path.join(L3, "state.json"), []),
    "3_fonctions": (os.path.join(FN, "state_3_fonctions.json"), ["f_fto2_objectifs", "f_fto2_alarmes", "f_fto2_cout"]),
    "2_fonctions": (os.path.join(FN, "state_2_fonctions.json"), ["f_fto2_objectifs", "f_fto2_alarmes"]),
}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def query(name, columns):
    """A table of 05_outputs as Slate gives a query result: one array per column, typed as the dataset."""
    t = pd.read_csv(os.path.join(ROOT, "05_outputs", name), dtype=str, keep_default_na=False)
    return SP._colmajor(SP._typed(t, columns))


def queries():
    return {"q_fto2_nc": query("fto2_dash_nc.csv", NC_COLUMNS), "q_fto2_def": query("fto2_dash_defects.csv", DEF_COLUMNS),
            "q_fto2_dis": query("fto2_dash_disruptions.csv", DIS_COLUMNS), "q_fto2_cout": query("fto2_dash_cout.csv", COUT_COLUMNS),
            "q_fto2_ref": SP.ref_columns(ROOT)}


def page(setup, Q):
    state_path, functions = SETUPS[setup]
    setup_js = {"state": json.loads(read(state_path)), "queries": Q, "functions": {f: read(os.path.join(FN, f + ".js")) for f in functions},
                "events": {"fto2Filtres": {"text": read(os.path.join(FN, "event_fto2Filtres.js")), "variable": "v_fto2_filtres"}},
                "variables": {"v_fto2_filtres": {}}, "delay": 80}
    pre = ("<script>/* LOCAL TEST ONLY: tests/slate/fake_slate.js stands in for Slate */\nwindow.FAKE_SLATE_SETUP = %s;\n</script>\n<script>\n%s</script>\n"
           % (json.dumps(setup_js, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"), read(os.path.join(HERE, "fake_slate.js"))))
    one = read(os.path.join(L3, "FTO2_Level23_Slate.html"))
    mark = "<!-- ===== HTML START ===== -->"
    assert one.count(mark) == 1
    return one.replace(mark, pre + mark, 1)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    Q = queries()
    for setup in SETUPS:
        out = os.path.join(sys.argv[1], setup)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "FTO2_NC_Dashboard.html"), "w", encoding="utf-8") as f:
            f.write(page(setup, Q))
        print("page:", os.path.join(out, "FTO2_NC_Dashboard.html"))


if __name__ == "__main__":
    main()
