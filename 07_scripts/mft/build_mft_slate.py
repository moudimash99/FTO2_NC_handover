"""The MFT page for a Slate code sandbox, fed by the dashboard's level-3 queries. Writes 03_reports/skywise/mft/.

Same page as 03_reports/FTO2_MFT.html (07_scripts/mft/mft_template.html), with two changes for Slate:
- its data come from the queries q_fto2_nc and q_fto2_def (the datasets fto2_dash_nc and fto2_dash_defects the Skywise notebook
  writes), turned into the page's data in the browser by mftFromTables (07_scripts/mft/mft_slate.js), as build_mft.data() does
  from the CSV files;
- the fixed references (sub-code names, production plan products, MSN per week, end of build per MSN, the MFT trackers' actions)
  come from the query q_fto2_ref (part "mft" of the dataset fto2_dash_ref), as the dashboard's do.
Both pages keep the actions and the alarm marks in the browser, through the store of mft_slate.js (Slate gives a code sandbox no
shared store): the trackers' actions, from the table, and the ones typed on the page.
Two options of the Slate page only, each through a key of the sandbox's state (without the key, the page is as before):
- "reglages": the query q_fto2_set_targets (the Fusion sheet "Target and pages"), whose lines replace the reference settings;
- "store": the query q_fto2_mft_store (q_fto2_mft_store.sql, written here), the actions kept for everyone in one object of the
  NC writer's object type, written through a Slate event, a variable and the object type's Action widget
  (03_reports/skywise/README.md, step 4).

    python3 -I 07_scripts/mft/build_mft_slate.py        (also run by build_mft.py)
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "03_reports", "skywise", "mft")
L3 = os.path.join(ROOT, "03_reports", "skywise", "level3_datasets")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "build"))
sys.path.insert(0, ROOT)
from fto2 import config     # noqa: E402   the settings in config/
import build_mft as M      # noqa: E402   the references and the alarm parts, as the page built from the CSV files
import build_all as B      # noqa: E402   _scope_css, the product alias rules and plan names
import skywise_pack as SP  # noqa: E402   the one-file layout, the error box styles, the local stand-in for Slate


# the actions kept for everyone: the store rows of the NC writer's object type, synced to Postgres as fto2_mft_store
STORE_SQL = """-- FTO2 MFT page: the MFT actions kept for everyone, in the NC writer's object type ("a30 Nc Writer Dataset"): the objects
-- whose Msn is MFT-ACTIONS, their Texte Sap holding every action as JSON. Each save adds one; the page takes the one saved
-- last. Slate query q_fto2_mft_store, optional (03_reports/skywise/README.md, step 4): the state key "store".
-- The table: the dataset the object type's action writes to, synced to Postgres as fto2_mft_store (schema foundry_sync).
-- If Slate says a column does not exist, write its name as Postgres has it, between double quotes (for example "Msn", "Texte Sap").
-- Only the 20 saved last are read (their save time is in the text, after "saved_at").
SELECT
    *
FROM "foundry_sync"."fto2_mft_store"
WHERE msn = 'MFT-ACTIONS'
ORDER BY substring(texte_sap from '"saved_at":"([^"]*)"') DESC NULLS LAST
LIMIT 20
"""


def refs():
    import pandas as pd
    t = config.frame("2_produits_plan.csv")
    fr = config.frame("3_souscodes_fr.csv").set_index("sous_code").description_fr.to_dict()
    return {"plan": {str(a).upper(): B.EQ_NAMES.get(b, b) for a, b in zip(t.produit_nc, t.produit_eqmsn)}, "alias": B.product_alias_rules(),
            "codes": {str(k): M.tidy(v, 90) for k, v in fr.items() if M.tidy(v, 90)}, "codesEn": M.codes_en(), "vol": M.weekly_volume(), "msnEnd": M.msn_end(),
            "actions": M.seed_actions()}


def dashboard_tables():
    """The dashboard page's tables, from its data block (03_reports/FTO2_NC_Dashboard.html, written by build_all.py)."""
    src = open(os.path.join(ROOT, "03_reports", "FTO2_NC_Dashboard.html"), encoding="utf-8").read()
    mark = '<script type="application/json" id="fto2-data">'
    a = src.index(mark) + len(mark)
    return json.loads(src[a:src.index("</script>", a)].replace("<\\/", "</"))["tables"]


def parts():
    t = open(os.path.join(HERE, "mft_template.html"), encoding="utf-8").read()
    js_al, css_al = M.alarm_parts()
    css = t.split("<style>", 1)[1].split("</style>", 1)[0].replace("/*@@ALARMCSS@@*/", css_al, 1)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    fonts = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">', t)
    css = (('/* Fonts: if Slate blocks this address, the page falls back to the system fonts. */\n@import url("%s");\n' % fonts.group(1)) if fonts else "") + \
        B._scope_css(css) + SP.EXTRA_CSS
    body = t[t.index('<header class="top">'):t.index('<script type="application/json" id="mft-data">')].strip()   # the page, without its data
    html = '<div class="fto2">\n<div id="fto2-err" class="fto2-err" hidden></div>\n<div id="fto2-wait" class="fto2-wait" hidden></div>\n%s\n</div>\n' % body
    main = t[t.index("<script>") + len("<script>"):t.rindex("</script>")].strip()
    head = "var D = JSON.parse(document.getElementById('mft-data').textContent);   // the data, written by the build beside the code"
    assert main.count(head) == 1 and "/*@@ALARMS@@*/" in main
    main = main.replace(head, "var D = window.FTO2_MFT_D;", 1).replace("/*@@ALARMS@@*/", js_al, 1)
    return css, html, main


def build(say=print):
    os.makedirs(OUT, exist_ok=True)
    stamp = ("FTO2 MFT for Slate: data from the queries q_fto2_nc, q_fto2_def and q_fto2_ref through the code sandbox's state; actions kept in "
             "this browser, or for everyone with the state key store (q_fto2_mft_store). Generated by 07_scripts/mft/build_mft_slate.py; do not edit by hand.")
    css, html, main = parts()
    js = open(os.path.join(HERE, "mft_slate.js"), encoding="utf-8").read()
    js = (js.replace("@@STAMP@@", stamp, 1).replace("@@REF_READER@@", SP.JS_REF_READER, 1).replace("@@REGLAGES@@", SP.JS_REGLAGES, 1)
          .replace("@@MAIN@@", main, 1))
    assert "{{" not in js, "a double brace in the MFT page's JS: Slate would read it as a binding"
    one = SP.write_level(OUT, "fto2_mft", stamp, "MFT Qualité FTO2 - Slate", css, html, js)
    open(os.path.join(OUT, "FTO2_MFT_Slate.html"), "w", encoding="utf-8").write(one)
    json.dump({"nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}", "ref": "{{q_fto2_ref}}"}, open(os.path.join(OUT, "state.json"), "w"), indent=2)
    for q in ("q_fto2_nc", "q_fto2_def", "q_fto2_ref", "q_fto2_set_targets"):   # the dashboard's level-3 queries, unchanged (the last optional)
        shutil.copyfile(os.path.join(L3, q + ".sql"), os.path.join(OUT, q + ".sql"))
    with open(os.path.join(OUT, "q_fto2_mft_store.sql"), "w", encoding="utf-8") as f:   # optional: the actions kept for everyone
        f.write(STORE_SQL)
    # local preview: the dashboard's real tables handed over as Slate would (never paste this file into Slate)
    t = dashboard_tables()
    pre = SP.fake_slate(SP._blob(t["nc"]), "null", SP._blob(t["def"]), SP._blob(SP.ref_columns(ROOT)))
    open(os.path.join(OUT, "preview_local_only.html"), "w", encoding="utf-8").write(
        one.replace("<!-- ===== HTML START ===== -->", pre + "<!-- ===== HTML START ===== -->", 1))
    say("MFT for Slate:", {f: os.path.getsize(os.path.join(OUT, f)) // 1024 for f in sorted(os.listdir(OUT)) if not f.endswith(".md")}, "KB")


if __name__ == "__main__":
    build()
