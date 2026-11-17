"""Pages to try the Skywise (Slate) set-ups on the laptop, with tests/slate/fake_slate.js standing in for Slate.

    python3 -I tests/slate/make_pages.py <output folder>

Writes into <output folder>/<set-up>/ the Skywise dashboard (03_reports/skywise/level3_datasets) as FTO2_NC_Dashboard.html,
and the Skywise MFT page (03_reports/skywise/mft) as FTO2_MFT.html where the set-up has one:

    sans_fonction       the dashboard computes everything (state.json); the MFT page as installed (mft/state.json)
    3_fonctions         targets, alarms and cost explanation from three Slate functions   fonctions/state_3_fonctions.json
    2_fonctions         targets and alarms from two Slate functions, the cost explanation
                        from the notebook's table fto2_dash_cout                          fonctions/state_2_fonctions.json
    fusion_partage      the two optional keys: "reglages" (a Fusion sheet "Target and pages" with other targets) on both pages,
                        and "store" on the MFT page (the actions kept for everyone, with a few store rows)
    fusion_3_fonctions  3_fonctions with the same Fusion sheet: the functions must compute with the page's cut
    fusion_ouverture    the dashboard with a Fusion sheet that changes the filters at opening
    partage_vide        the MFT page with the key "store" and no store row yet: it starts from the table's actions

Each holds the laptop data (05_outputs/, written by build/build_all.py) as Slate gives a query result. The first three have none
of the optional keys: a snapshot of each (FTO2_PAGES=<output folder>/<set-up> node tests/snapshot/snapshot_pages.js ...) must
show the same as the laptop pages (tests/golden). The others are checked by tests/slate/check_state_keys.js.
"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
L3 = os.path.join(ROOT, "03_reports", "skywise", "level3_datasets")
MFT = os.path.join(ROOT, "03_reports", "skywise", "mft")
FN = os.path.join(L3, "fonctions")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "build"))
from fto2.core import NC_COLUMNS, DEF_COLUMNS, DIS_COLUMNS  # noqa: E402
from fto2.cost.explain import COLUMNS as COUT_COLUMNS  # noqa: E402
import skywise_pack as SP  # noqa: E402

FUSION, STORE = "{{q_fto2_set_targets}}", "{{q_fto2_mft_store}}"
# set-up: (the dashboard's state file, its Slate functions, keys added to its state), and the MFT page's (state file, keys added)
SETUPS = {
    "sans_fonction": ((os.path.join(L3, "state.json"), [], {}), (os.path.join(MFT, "state.json"), {})),
    "3_fonctions": ((os.path.join(FN, "state_3_fonctions.json"), ["f_fto2_objectifs", "f_fto2_alarmes", "f_fto2_cout"], {}), None),
    "2_fonctions": ((os.path.join(FN, "state_2_fonctions.json"), ["f_fto2_objectifs", "f_fto2_alarmes"], {}), None),
    "fusion_partage": ((os.path.join(L3, "state.json"), [], {"reglages": FUSION}),
                       (os.path.join(MFT, "state.json"), {"reglages": FUSION, "store": STORE})),
    "fusion_3_fonctions": ((os.path.join(FN, "state_3_fonctions.json"), ["f_fto2_objectifs", "f_fto2_alarmes", "f_fto2_cout"], {"reglages": FUSION}), None),
    "fusion_ouverture": ((os.path.join(L3, "state.json"), [], {"reglages": FUSION}), None),
    "partage_vide": (None, (os.path.join(MFT, "state.json"), {"store": STORE})),
}

# the Fusion sheet "Target and pages" as a sync might give it (column names in other cases, values written by hand): the target cut
# and the action target change, the filters at opening are the reference ones written differently, and one line is wrong
SHEET = {"Nom": ["objectif_baisse", "defaut_phase", "defaut_responsabilite", "defaut_periode", "action_objectif_baisse", "action_semaines_tenues"],
         "VALEUR": ["30 %", "Série", "F", "3 mois", "0,5", "2"],
         "Description": ["", "", "", "", "", ""]}
# the same sheet, other filters at opening (REC, FTO2 and suppliers, the last 3 months)
SHEET_OPENING = {"nom": ["objectif_baisse", "defaut_phase", "defaut_responsabilite", "defaut_periode"],
                 "valeur": [0.25, "rec", "sf", "M3"], "description": ["", "", "", ""]}


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


def store_rows(empty=False):
    """The store query as Slate gives it (one array per column, the column names as the object type shows them): a row of the
    test box (no page mark: not read), an earlier save with the table's actions, the latest save (two actions: one of the
    table, changed, and one typed on the page), a later save whose text was cut, and an NC of the NC writer."""
    cols = ["Timestamp", "Msn", "Produit", "Detection", "Total Defauts", "Texte Sap"]
    if empty:
        return {c: [] for c in cols}
    with open(os.path.join(ROOT, "05_outputs", "mft_actions_seed.json"), encoding="utf-8") as f:
        seed = json.load(f)
    first = dict(seed[0], title=seed[0]["title"] + " (copie partagée)", log=[{"at": "2026-11-16", "by": "", "name": "Équipe qualité", "text": "Point de la semaine (copie partagée)"}])
    typed = {"id": "a-partage-1", "line": "A350", "title": "Action tapée sur la page (copie partagée)", "category": "", "problem": {"mode": "simple", "codes": ["Q11"]},
             "defects": "", "rootCause": "", "analysisOwner": "", "analysisStart": "2026-09-01", "action": "Vérifier les fixations", "actionOwner": "Chef d'équipe",
             "actionStart": "2026-09-14", "status": "En cours", "expected": "", "note": "", "log": [], "author": "Équipe qualité", "createdBy": "",
             "createdAt": "2026-11-16", "source": "Page MFT"}
    text = lambda at, actions: json.dumps({"page": "MFT", "saved_at": at, "actions": actions}, ensure_ascii=False, separators=(",", ":"))
    latest = text("2026-11-16T09:00:00.000Z", [first, typed])
    rows = [
        ["2026-11-14 10:23:11", "MFT-ACTIONS", "MFT", "store", 1, '{"saved_at":"2026-11-14 10:23:11","actions":[{"id":"a1","title":"Test action","at":"2026-11-14 10:23:05"}]}'],
        ["2026-11-10 09:00:00", "MFT-ACTIONS", "MFT", "store", len(seed), text("2026-11-10T08:00:00.000Z", seed)],
        ["2026-11-16 10:00:00", "MFT-ACTIONS", "MFT", "store", 2, latest],
        ["2026-11-17 08:00:00", "MFT-ACTIONS", "MFT", "store", 2, text("2026-11-17T07:00:00.000Z", [first, typed])[:300]],
        ["2026-11-15 14:02:00", "810", "MIP A350", "Contrôle final", 1, "DEF 1 : câble endommagé"],
    ]
    return {c: [r[i] for r in rows] for i, c in enumerate(cols)}


def fake(setup_js):
    return ("<script>/* LOCAL TEST ONLY: tests/slate/fake_slate.js stands in for Slate */\nwindow.FAKE_SLATE_SETUP = %s;\n</script>\n<script>\n%s</script>\n"
            % (json.dumps(setup_js, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"), read(os.path.join(HERE, "fake_slate.js"))))


def put(one, pre):
    mark = "<!-- ===== HTML START ===== -->"
    assert one.count(mark) == 1
    return one.replace(mark, pre + mark, 1)


def extra_queries(keys, name):
    """The results of the optional queries a set-up's state reads."""
    out = {}
    if FUSION in keys.values():
        out["q_fto2_set_targets"] = SHEET_OPENING if name == "fusion_ouverture" else SHEET
    if STORE in keys.values():
        out["q_fto2_mft_store"] = store_rows(empty=name == "partage_vide")
    return out


def dashboard_page(setup, Q):
    state_path, functions, keys = SETUPS[setup][0]
    setup_js = {"state": dict(json.loads(read(state_path)), **keys), "queries": dict(Q, **extra_queries(keys, setup)),
                "functions": {f: read(os.path.join(FN, f + ".js")) for f in functions},
                "events": {"fto2Filtres": {"text": read(os.path.join(FN, "event_fto2Filtres.js")), "variable": "v_fto2_filtres"}},
                "variables": {"v_fto2_filtres": {}}, "delay": 80}
    return put(read(os.path.join(L3, "FTO2_Level23_Slate.html")), fake(setup_js))


def mft_page(setup, Q):
    state_path, keys = SETUPS[setup][1]
    state = dict(json.loads(read(state_path)), **keys)
    setup_js = {"state": state, "queries": dict({k: Q[k] for k in ("q_fto2_nc", "q_fto2_def", "q_fto2_ref")}, **extra_queries(keys, setup)),
                "functions": {}, "events": {"save": {"text": "return {{slEventValue}};", "variable": "v_mft_store"}},   # the event of the README, step 4
                "variables": {"v_mft_store": {}}, "delay": 80}
    return put(read(os.path.join(MFT, "FTO2_MFT_Slate.html")), fake(setup_js))


def page(setup, Q):
    """The dashboard of a set-up (kept for tests/test_slate_functions.py and older callers)."""
    return dashboard_page(setup, Q)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    Q = queries()
    for setup, (dash, mft) in SETUPS.items():
        out = os.path.join(sys.argv[1], setup)
        os.makedirs(out, exist_ok=True)
        for name, make, wanted in (("FTO2_NC_Dashboard.html", dashboard_page, dash), ("FTO2_MFT.html", mft_page, mft)):
            if wanted is None:
                continue
            with open(os.path.join(out, name), "w", encoding="utf-8") as f:
                f.write(make(setup, Q))
            print("page:", os.path.join(out, name))


if __name__ == "__main__":
    main()
