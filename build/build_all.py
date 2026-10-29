# -*- coding: utf-8 -*-
"""
Rebuild every FTO2 NC output from the raw Skywise exports, in one run.

    python3 build/build_all.py

Input (the only data read):
    06_input_data/fto2_dashboard_data*.csv     Skywise NC exports (standard + missing-IDs). All files are merged;
                                               when an NC is in several, the most recently changed row wins.
    04_reference/llm_labels_longtext.csv       Root-cause labels per defect line (Sonnet, full long text, 12 Oct 2026).

Steps:
    1. parser v4.8 (02_dashboard_pack/.../fto2_logic.py)  -> one row per defect, one row per NC; where raised (scope) from the pipeline's plant and Type_NC_auto
    2. join the long-text labels on (NC, defect #); a line whose text changed or that is new is marked "to label"
    3. CNQ model cnq-2026.10 (cnq_handoever/) for both classifications
    4. write the tables, refresh the CNQ package sample outputs, build the HTML pages and the Excel files

Outputs:
    05_outputs/fto2_defects.csv, fto2_nc.csv                     the reference datasets
    05_outputs/fto2_defects_cnq.csv, fto2_nc_cnq.csv             CNQ step output (parser classification, as in Skywise)
    05_outputs/FTO2_defects_detail.xlsx                          one row per defect, all columns, live summary
    05_outputs/FTO2_llm_longtext_review.xlsx                     disagreements parser vs long-text labels, to review
    03_reports/FTO2_NC_Dashboard.html                            Pareto · weekly Pareto · CNQ · customer returns · root causes
    cnq_handoever/sample_output, tests/expected_totals.json, params/*.csv, dashboard/cnq_dashboard.html
    build/build_report.json                                      counts and checks of this run
"""
import glob, json, os, re, subprocess, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "02_dashboard_pack", "skywise_nc_dashboard_v48", "1_pipeline")
CNQ = os.path.join(ROOT, "cnq_handoever")
OUT = os.path.join(ROOT, "05_outputs")
REP = os.path.join(ROOT, "03_reports")
sys.path.insert(0, PACK)
sys.path.insert(0, CNQ)
import fto2_logic as L                                   # noqa: E402
import nc_defect_parser as PARSER                        # noqa: E402
from cnq.cnq_core import compute_cnq, parameters_as_tables  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "build"))
import fto2_core as core                                # noqa: E402   the data steps, shared with the Skywise notebook

REPORT = {}
CODE_DESC = {}   # official sub-code -> [en, fr], filled by the data steps


def say(*a):
    print(*a, flush=True)


# ============================================================ 1. raw exports -> parser
def load_exports():
    files = sorted(glob.glob(os.path.join(ROOT, "06_input_data", "fto2_dashboard_data*.csv")))
    frames = []
    for f in files:
        x = pd.read_csv(f, low_memory=False, dtype={"notification_number": str})
        x["_source"] = os.path.basename(f)
        frames.append(x)
    x, info = core.merge_exports(frames)
    REPORT["inputs"] = {os.path.basename(f): int((x["_source"] == os.path.basename(f)).sum()) for f in files}
    REPORT.update(info)
    return x


clean_long_text, week_of = core.clean_long_text, core.week_of


def load_orders():
    """Operations of the rework orders (SAP S03, plant FTO2): 06_input_data/wo_s03_operations_fto2_*.csv.gz. Today one month of
    operations (confirmed Sept 2026), extracted from main's work-order upload. None when there is no file."""
    files = sorted(glob.glob(os.path.join(ROOT, "06_input_data", "wo_s03_operations_fto2_*.csv.gz")))
    if not files:
        return None
    frames = [pd.read_csv(f, dtype=str, keep_default_na=False, na_values=[""]) for f in files]
    REPORT["order_inputs"] = {os.path.basename(f): len(t) for f, t in zip(files, frames)}
    return pd.concat(frames, ignore_index=True)


def load_disruptions():
    """MES disruptions (aléas) at plant FTO2: 06_input_data/mes_disruptions_fto2_*.csv.gz. Today Jan-Sep 2026, extracted from main's
    upload (2,500 rows: possibly cut at an export limit, check H7). None when there is no file."""
    files = sorted(glob.glob(os.path.join(ROOT, "06_input_data", "mes_disruptions_fto2_*.csv.gz")))
    if not files:
        return None
    frames = [pd.read_csv(f, dtype=str, keep_default_na=False, na_values=[""]) for f in files]
    REPORT["disruption_inputs"] = {os.path.basename(f): len(t) for f, t in zip(files, frames)}
    return pd.concat(frames, ignore_index=True).drop_duplicates("disruption_id")


def year_2025(x):
    """2025 for the year comparisons: the raw Skywise NC extract of 2025 (06_input_data/nc_2025_skywise_fto2.csv.gz) through the
    pipeline's rules, the parser and the CNQ model, summed per month, scope, phase, line and product; and the 2025 deliveries per
    product (06_input_data/Livraisons_MSN_2025.csv, the Livraisons 2025 sheet). None when the extract is missing."""
    path = os.path.join(ROOT, "06_input_data", "nc_2025_skywise_fto2.csv.gz")
    if not os.path.exists(path):
        return None
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    rules, plan = product_alias_rules(), {str(k).upper() for k in pd.read_csv(os.path.join(ROOT, "04_reference", "eqmsn_produits.csv"), encoding="utf-8").produit_nc}
    alias = lambda line, prod, station: alias_product(rules, plan, line, prod, station)   # products off the plan put back on their plan product
    rows, info, p = core.year_baseline(raw, core.station_pairs([x]), os.path.join(ROOT, "04_reference"), 2025, alias)
    out = {"cols": ["month", "scope", "phase", "line", "product", "nc", "def", "defMajor", "cost", "cost2", "cost1"], "rows": rows,
           "from": info["created_from"], "to": info["created_to"], "prod": None, "msn": None}
    out["rcaCols"], out["rca"] = core.year_causes(p, 2025)   # 2025 defects by cause (parser labels), for the 2025 / 2026 cause charts
    n25 = p["nc"][p["nc"].date_creation.astype(str).str.startswith("2025") & (p["nc"].scope == "serie")]
    msn = n25.msn.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.lstrip("0")
    out["byMsn"] = {"%s|%s" % k: int(v) for k, v in n25.assign(m=msn)[msn != ""].groupby(["ligne", "m"]).size().items()}   # 2025 NCs per aircraft: built partly in 2025
    lv = os.path.join(ROOT, "06_input_data", "Livraisons_MSN_2025.csv")
    if os.path.exists(lv):
        t = pd.read_csv(lv, encoding="utf-8")
        months = [c for c in t.columns if c.startswith("2025-")]
        out["prod"] = {EQ_NAMES.get(k, k): [float(v) for v in vals] for k, vals in zip(t.produit_eqmsn, t[months].values)}
        out["months"] = months
        ln = pd.read_csv(os.path.join(ROOT, "06_input_data", "Livraisons_MSN_2025_lignes.csv"), encoding="utf-8")
        out["msn"] = dict(zip(ln.ligne, ln.msn_entiers_livres_2025.astype(int)))
    s = [r for r in rows if r[1] == "serie" and r[2] == "SERIE"]
    REPORT["y2025"] = dict(info, serie_SERIE={"ncs": sum(r[5] for r in s), "defects": sum(r[6] for r in s), "level3": round(sum(r[8] for r in s), 2)},
                           deliveries=sum(sum(v) for v in (out["prod"] or {}).values()))
    return out


# ============================================================ main
def main():
    x = load_exports()
    say("exports:", REPORT["inputs"], "->", len(x), "NCs")
    ops, dis = load_orders(), load_disruptions()
    lab = pd.read_csv(os.path.join(ROOT, "04_reference", "llm_labels_longtext.csv"), dtype={"notification_number": str}, encoding="utf-8-sig")
    y25 = year_2025(x.copy())
    say("2025:", REPORT.get("y2025"))
    p = core.prepare(x, lab, os.path.join(ROOT, "04_reference"), ops, dis)   # parser, labels, CNQ, rework orders, aléas, scope: build/fto2_core.py
    d, nc_ref, lt, nc_in = p["d"], p["nc"], p["lt"], p["nc_in"]
    nl_, dl_ = p["nc_llm"], p["def_llm"]
    CODE_DESC.update(p["codes"])
    REPORT.update({k: p["report"][k] for k in ("labels", "subcodes", "unknown_cnq_classes", "rework_orders", "aleas") if k in p["report"]})
    say("parser v4.8:", p["report"]["parser"]["defect_lines"], "defect lines in", p["report"]["parser"]["ncs"], "NCs")
    say("labels:", REPORT["labels"])
    d.to_csv(os.path.join(OUT, "fto2_defects.csv"), index=False, encoding="utf-8-sig")
    nc_ref.to_csv(os.path.join(OUT, "fto2_nc.csv"), index=False, encoding="utf-8-sig")
    nl_.to_csv(os.path.join(OUT, "fto2_nc_cnq.csv"), index=False)
    dl_.rename(columns={"sous_groupe": "llm_sous_categorie"}).merge(
        d[["notification_number", "seq", "text", "llm_categorie", "llm_rca_nom", "llm_mineur", "groupe", "sous_groupe"]],
        on=["notification_number", "seq"]).to_csv(os.path.join(OUT, "fto2_defects_cnq.csv"), index=False)
    say("written 05_outputs/fto2_defects.csv, fto2_nc.csv, fto2_*_cnq.csv")

    # figures for the report
    aec = nc_ref[nc_ref.cnq_on_aec == 1]
    t3 = float(aec.cnq_cost_total.sum())
    cab_alloc = float(d.loc[d.llm_defaut_cable, "cnq_cost_allocated_llm"].sum())
    cab_p = float(d.loc[d.defaut_cable, "cnq_cost_allocated"].sum()); t3p = float(aec.cnq_cost_total_parser.sum())
    REPORT["cnq"] = {"classification": "root cause (long text)", "nc_on_aec": int(len(aec)), "level1": round(float(aec.cnq_cost_airbus.sum()), 2),
                     "level2": round(float(aec.cnq_cost_global.sum()), 2), "level3": round(t3, 2), "cable_allocated": round(cab_alloc, 2),
                     "cable_share": round(cab_alloc / t3, 4), "level3_parser": round(t3p, 2), "cable_share_parser": round(cab_p / t3p, 4)}
    REPORT["scope"] = nc_ref.scope.value_counts().to_dict()
    REPORT["report_scope"] = {k: {"ncs": int((nc_ref.scope == k).sum()), "ncs_without_defect_line": int(((nc_ref.scope == k) & (nc_ref.cnq_defect_lines == 0)).sum()),
                                  "defects": int((d.scope == k).sum()), "cnq": round(float(nc_ref.loc[nc_ref.scope == k, "cnq_cost_total"].sum()), 2)}
                              for k in ("serie", "client", "autre")}
    REPORT["defects_by_scope"] = d.scope.value_counts().to_dict()

    # ======================================================== 4a. CNQ package: same data, same totals
    refresh_cnq_package(nc_in, d)
    # ======================================================== 4b. pages and workbooks
    build_dashboard(d, nc_ref, lt, y25, core.dis_table(p["dis"]))
    build_review(d, lt)
    build_detail(d, nc_ref, x)
    json.dump(REPORT, open(os.path.join(ROOT, "build", "build_report.json"), "w"), indent=2, ensure_ascii=False, default=str)
    say(json.dumps(REPORT, indent=1, ensure_ascii=False, default=str))


# ============================================================ CNQ package
def refresh_cnq_package(nc_in, d):
    # the package's defect dataset, classified by root cause; the parser columns are kept under parser_*
    dd = d[["notification_number", "seq", "qty", "code", "fin", "text", "provenance", "etat_cable",
            "llm_sous_categorie", "llm_categorie", "llm_rca_type", "llm_rca_nom", "llm_mineur", "llm_defaut_cable",
            "sous_groupe", "groupe", "rca_type", "mineur", "defaut_cable"]].rename(columns={
        "sous_groupe": "parser_sous_groupe", "groupe": "parser_groupe", "rca_type": "parser_rca_type", "mineur": "parser_mineur", "defaut_cable": "parser_defaut_cable"})
    dd = dd.rename(columns={"llm_sous_categorie": "sous_groupe", "llm_categorie": "groupe", "llm_rca_type": "rca_type", "llm_rca_nom": "rca_nom",
                            "llm_mineur": "mineur", "llm_defaut_cable": "defaut_cable"})
    dd["categorie"] = dd["groupe"]
    n_out, d_out = compute_cnq(nc_in, dd)
    n_out.to_csv(os.path.join(CNQ, "sample_output", "fto2_nc_cnq.csv"), index=False)
    d_out.to_csv(os.path.join(CNQ, "sample_output", "fto2_defects_cnq.csv"), index=False)
    for name, t in zip(("cnq_steps", "cnq_rules", "cnq_defect_times"), parameters_as_tables()):
        t.to_csv(os.path.join(CNQ, "params", name + ".csv"), index=False)
    sys.path.insert(0, os.path.join(CNQ, "tests"))
    from run_local import totals
    t = totals(n_out, d_out)
    json.dump(t, open(os.path.join(CNQ, "tests", "expected_totals.json"), "w"), indent=2, ensure_ascii=False)
    for cmd in ([sys.executable, os.path.join(CNQ, "dashboard", "build_dashboard.py")],
                [sys.executable, os.path.join(CNQ, "tests", "test_queries.py")],
                ["node", os.path.join(CNQ, "tests", "test_dashboard.js")]):
        r = subprocess.run(cmd, cwd=CNQ, capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or [""])[-1]
        REPORT.setdefault("cnq_package_checks", {})[os.path.basename(cmd[-1])] = "OK" if r.returncode == 0 else "FAILED: " + (r.stderr or r.stdout)[-400:]
        say("cnq package:", os.path.basename(cmd[-1]), "OK" if r.returncode == 0 else "FAILED", "|", last[:100])
    REPORT["cnq_package_totals"] = {k: t[k] for k in ("nc_rows", "nc_on_aec", "nc_no_master_data", "level1_airbus_aec", "level2_global_aec", "level3_detailed_aec")}


# ============================================================ pages
def _page(template, data, name, page="main", title=None):
    t = open(os.path.join(ROOT, "build", "templates", template), encoding="utf-8").read().replace("__PAGE__", page)
    if title:
        t = t.replace("<title>FTO2 NC Dashboard</title>", "<title>" + title + "</title>", 1)
    page = t.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    # the published artifact gets its own skeleton; the offline copy needs one
    os.makedirs(os.path.join(ROOT, "build", "artifacts"), exist_ok=True)
    open(os.path.join(ROOT, "build", "artifacts", name), "w", encoding="utf-8").write(page)
    full = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + page.replace('<div class="wrap">', '</head>\n<body>\n<div class="wrap">', 1) + '\n</body>\n</html>\n')
    open(os.path.join(REP, name), "w", encoding="utf-8").write(full)
    say("page:", name, len(full) // 1024, "KB")


S_ = lambda v: "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def _scope_css(css, scope=".fto2"):
    """Prefix every selector with the dashboard's own class, so the styles stay inside the dashboard when it is pasted
    into a page it shares with other content (Slate). Dark-mode blocks are dropped: Slate pages are light."""
    out, i = [], 0
    while True:
        j = css.find("{", i)
        if j < 0:
            break
        sel, depth, k = css[i:j].strip(), 1, j + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        body, i = css[j + 1:k - 1], k
        if sel.startswith("@media"):
            if "prefers-color-scheme: dark" not in sel:
                out.append(sel + " {\n" + _scope_css(body, scope) + "}")
        elif sel.startswith("@"):
            out.append(sel + " {" + body + "}")
        elif 'data-theme="dark"' not in sel:
            def one(s):
                if s in (":root", "body", "html"):
                    return scope
                return scope + " " + s
            out.append(", ".join(one(s.strip()) for s in sel.split(",")) + " {" + body + "}")
    return "\n".join(out) + "\n"


def slate_pack(data, template="dashboard.html", page="main"):
    """The dashboard as three pieces for a Slate code box (HTML, CSS, JavaScript), in 03_reports/slate/.
    No outside resources (fonts, libraries), styles scoped to .fto2, page title and address left alone, errors shown on the page."""
    t = open(os.path.join(ROOT, "build", "templates", template), encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", t.split("<style>", 1)[1].split("</style>", 1)[0], flags=re.S)
    fonts = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">', t)
    html = t[t.index('<div class="wrap">'):t.index("<script>")].strip()
    main = t[t.index("<script>\n(function ()") + len("<script>\n"):t.rindex("</script>")].strip()
    d = dict(data)
    d.pop("direct", None)                                          # not used by the page
    d["defects"] = [r[:6] + [0, 0, 0, 0, 0] + r[11:16] + [0] + r[17:] for r in data["defects"]]   # parser labels not shown
    blob = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = os.path.join(REP, "slate")
    os.makedirs(out, exist_ok=True)
    pre, one_name = ("fto2_slate", "FTO2_NC_Dashboard_Slate.html") if page == "main" else ("fto2_suivi_slate", "FTO2_Suivi_Hebdo_Slate.html")
    stamp = ("FTO2 NC dashboard" if page == "main" else "FTO2 weekly follow-up") + " for a Slate code box. Data: NCs created %s to %s. Generated by build/build_all.py; do not edit by hand." % (data["meta"]["from"], data["meta"]["to"])
    open(os.path.join(out, pre + ".html"), "w", encoding="utf-8").write(
        "<!-- %s -->\n<div class=\"fto2\">\n<div id=\"fto2-err\" class=\"fto2-err\" hidden></div>\n%s\n</div>\n" % (stamp, html))
    open(os.path.join(out, pre + ".css"), "w", encoding="utf-8").write(
        "/* %s */\n%s%s.fto2 .fto2-err { background: #fdecea; color: #8a1c12; border: 1px solid #f1b0a8; border-radius: 8px; padding: 10px 14px; font-size: 13px; margin: 12px 20px; }\n" % (stamp, ('/* Fonts: if Slate blocks this address, the page falls back to Georgia and the system sans-serif. */\n@import url("%s");\n' % fonts.group(1)) if fonts else "", _scope_css(css)))
    js = ("/* %s */\n"
          "window.FTO2_EMBED = true;\n"
          "window.FTO2_PAGE = '%s';\n"
          "window.DASH = %s;\n"
          "(function () {\n"
          "  function showError(msg) {\n"
          "    var e = document.getElementById('fto2-err');\n"
          "    if (e) { e.hidden = false; e.textContent = 'Le tableau de bord n\\'a pas pu s\\'afficher / The dashboard could not load: ' + msg; }\n"
          "    if (window.console) console.error('[FTO2 dashboard]', msg);\n"
          "  }\n"
          "  window.addEventListener('error', function (ev) { showError((ev && ev.message) || 'unknown error'); });\n"
          "  function main() {\n%s\n  }\n"
          "  function start() {\n"
          "    if (!document.getElementById('tabs')) { showError('HTML part missing: paste the HTML part into the HTML box.'); return; }\n"
          "    try { main(); } catch (err) { showError((err && err.message) || String(err)); }\n"
          "  }\n"
          "  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();\n"
          "})();\n") % (stamp, page, blob, main)
    open(os.path.join(out, pre + ".js"), "w", encoding="utf-8").write(js)
    # the same three parts in one file: it opens as a normal page, and each part sits between markers to copy into its box
    one = ("<!doctype html>\n<html lang=\"fr\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
           "<title>FTO2 NC Dashboard</title>\n<!--\n  %s\n  One file, three parts. It opens as a page as it is. For a Slate code box, copy each part into its box:\n"
           "    CSS box        = everything between the lines  CSS START  and  CSS END\n"
           "    HTML box       = everything between the lines  HTML START  and  HTML END\n"
           "    JavaScript box = everything between the lines  JS START  and  JS END\n"
           "-->\n"
           "<style>\n/* ===== CSS START ===== */\n%s/* ===== CSS END ===== */\n</style>\n</head>\n<body style=\"margin:0\">\n"
           "<!-- ===== HTML START ===== -->\n%s<!-- ===== HTML END ===== -->\n"
           "<script>\n/* ===== JS START ===== */\n%s/* ===== JS END ===== */\n</script>\n</body>\n</html>\n") % (
        stamp,
        open(os.path.join(out, pre + ".css"), encoding="utf-8").read(),
        open(os.path.join(out, pre + ".html"), encoding="utf-8").read(),
        js.replace("</script", "<\\/script"))
    open(os.path.join(out, one_name), "w", encoding="utf-8").write(one)
    say("slate pack:", {f: os.path.getsize(os.path.join(out, f)) // 1024 for f in os.listdir(out)}, "KB")


def build_dashboard(d, nc, lt, y25=None, dis_t=None):
    rca = lambda t: L.RCA_NAMES.get(t, t)
    ncd = nc.set_index("notification_number")
    defs = []
    for r in d.itertuples():
        defs.append([r.notification_number, int(r.seq), r.date_creation, r.semaine, S_(r.ligne), "",
                     r.groupe, rca(r.rca_type), r.sous_groupe, int(bool(r.mineur)), int(bool(r.defaut_cable)),
                     r.llm_categorie, r.llm_rca_nom, r.llm_sous_categorie, int(bool(r.llm_mineur)), int(bool(r.llm_defaut_cable)),
                     round(float(r.cnq_cost_allocated), 2), round(float(r.cnq_cost_allocated_llm), 2), S_(r.text)[:220],
                     "", r.scope, S_(r.phase), r.sous_code_officiel, S_(r.fin)])   # [19] kept empty: the labelling notes are working notes, not for the page
    ncs = []
    for r in nc.itertuples():
        if not r.date_creation:
            continue
        k = int(r.cnq_on_aec)   # FTO2's cost only where FTO2 is liable; every NC counts
        ncs.append([r.notification_number, r.date_creation, week_of(r.date_creation), S_(r.ligne), "", int(r.cnq_on_aec), r.cnq_rule,
                    r.cnq_decision_label, r.cnq_where_found] + [round(k * v, 2) for v in (r.cnq_cost_airbus, r.cnq_cost_global, r.cnq_cost_total_parser,
                    r.cnq_cost_total, r.cnq_cost_admin, r.cnq_cost_work_parser, r.cnq_cost_work, r.cnq_cost_material_parser, r.cnq_cost_material,
                    r.cnq_cost_engineering)] + [
                    int(r.nc_cable), int(r.nc_cable_llm), int(r.cnq_defect_lines), S_(r.description_short)[:80], r.scope, S_(r.phase)]
                   + nc_extras(r) + [S_(r.plant), 0 if k else round(float(r.cnq_cost_total), 2)])   # [42] plant (the plant switch), [43] cost FTO2 does not bear
    direct = {"%s|%d" % (r.notification_number, r.seq): [round(float(r.cnq_cost_direct), 2), round(float(r.cnq_cost_direct_llm), 2)]
              for r in d.itertuples() if r.cnq_cost_allocated or r.cnq_cost_allocated_llm}
    aec, nl = nc[nc.cnq_on_aec == 1], nc[(nc.cnq_on_aec != 1) & (nc.date_creation != "")]
    aside = {"other": [int(len(nl)), round(float(nl.cnq_cost_total.sum()), 2)]}   # NCs FTO2 is not liable for: counted, cost 0 for FTO2
    no_line = int(((nc.scope == "serie") & (nc.cnq_defect_lines == 0)).sum())
    client, lt_client = customer_return_extras(d, nc, lt)
    actions = mft_actions()
    data = {"defects": defs, "ncs": ncs, "direct": direct, "rca": rca_reference(d), "client": client, "lt": lt_client, "codes": CODE_DESC, "actions": actions,
            "cnqp": cnq_explain(d),
            "meta": {"from": "2026-01-01", "to": REPORT["created_to"], "aside": aside, "noLine": no_line,
                     "modelTotal": round(float(aec.cnq_cost_total.sum()), 2)}}
    # every page carries the production file (rates per MSN); only the review pages carry the made-up gallery data (never in the Slate files)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I leaves the script folder off the path
    import dummy_data
    data["eqmsn"] = eqmsn(nc)
    data["y25"] = y25
    dis_t = dis_t if dis_t is not None else core.dis_table(None)
    data["dis"] = [[None if (isinstance(v, float) and np.isnan(v)) else v for v in r] for r in dis_t.values.tolist()]   # as the JS adapter gives it
    local = dict(data, dummy=dummy_data.make(ROOT))
    # the main page goes through the two tables, as in Skywise: the JS (fto2FromTables) rebuilds the page's data from them
    nc_t, def_t = core.tables(d, nc, lt, REPORT["created_to"])
    nc_t.to_csv(os.path.join(OUT, "fto2_dash_nc.csv"), index=False, encoding="utf-8-sig")
    def_t.to_csv(os.path.join(OUT, "fto2_dash_defects.csv"), index=False, encoding="utf-8-sig")
    dis_t.to_csv(os.path.join(OUT, "fto2_dash_disruptions.csv"), index=False, encoding="utf-8-sig")
    REPORT["dash_tables"] = {"nc": int(len(nc_t)), "defects": int(len(def_t)), "disruptions": int(len(dis_t))}
    src = {"tables": {"nc": colmajor(nc_t), "def": colmajor(def_t), "dis": colmajor(dis_t)}, "ref": reference_block(data)}
    _page("dashboard.html", src, "FTO2_NC_Dashboard.html")
    # the proposed final layout, chart by chart, with the choices to make (review page, local only)
    _page("dashboard.html", local, "FTO2_Revue_Proposition.html", page="review")
    # the same layout as a mock-up of the final dashboard, every chart scored a to e at its side (local only)
    _page("dashboard.html", local, "FTO2_Maquette_Notee.html", page="mock")
    _page("dashboard.html", data, "FTO2_Suivi_Hebdo.html", page="suivi")
    slate_pack(data)
    slate_pack(data, page="suivi")
    import skywise_pack   # the four Skywise migration levels (03_reports/skywise): build/skywise_pack.py
    REPORT["skywise"] = skywise_pack.build(src["ref"], ROOT, _scope_css, say)


def colmajor(df):
    """A table as Slate returns a query result: one array per column (empty -> null)."""
    return {c: [None if (isinstance(v, float) and np.isnan(v)) else v for v in df[c].tolist()] for c in df.columns}


def reference_block(data):
    """What does not come from the two tables: code sheet, MFT actions, cost parameters, production plan, root-cause tree, 2025 (NCs
    summed per month, scope, phase, line and product; deliveries per product).
    Written into the page (and into the Slate JS); the examples, quantities and product lines are rebuilt from the tables."""
    cq = {k: v for k, v in data["cnqp"].items() if k != "qty"}
    eq = {k: v for k, v in data["eqmsn"].items() if k != "line"} if data.get("eqmsn") else None
    return {"from": data["meta"]["from"], "codes": data["codes"], "actions": data["actions"], "cnqp": cq, "eqmsn": eq,
            "rca": [dict(o, ex=[]) for o in data["rca"]], "y25": data.get("y25")}


EQ_NAMES = {"MIP": "MIP A350", "MIP(2)": "MIP A400M"}   # the production file's names, as the page shows them (MIP(2) is the A400M MIP: Mohammad, 29 Oct)


def eqmsn(nc):
    """Production volume for the Production tab: EqMSN per product and month of 2026 (06_input_data/EqMSN_2026.xlsx, both the
    Standard and the Adjusted sheet; "wd": the same counted on working days, see working_day_volume, the page's default), the NC
    product labels it matches (04_reference/eqmsn_produits.csv) and each product's line, taken from the NCs. None if the file is
    missing."""
    path = os.path.join(ROOT, "06_input_data", "EqMSN_2026.xlsx")
    if not os.path.exists(path):
        return None
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {"asof": "2026-10-07", "forecastFrom": "2026-10",   # export of 07/10/2026; the Notes sheet says October to December are forecast
           "months": ["2026-%02d" % m for m in range(1, 13)]}
    for sheet, key in (("Standard", "std"), ("Adjusted", "adj")):
        rows, start = {}, False
        for r in wb[sheet].iter_rows(values_only=True):
            if r[0] == "Produit":
                start = True
                continue
            if not start or r[0] in (None, "Total"):
                if start and r[0] == "Total":
                    break
                continue
            rows[EQ_NAMES.get(str(r[0]), str(r[0]))] = [round(float(v or 0), 2) for v in r[1:13]]
        out[key] = rows
    ref = pd.read_csv(os.path.join(ROOT, "04_reference", "eqmsn_produits.csv"), encoding="utf-8")
    out["map"] = {str(a).upper(): EQ_NAMES.get(b, b) for a, b in zip(ref.produit_nc, ref.produit_eqmsn)}
    out["toConfirm"] = [EQ_NAMES.get(b, b) for b, c in zip(ref.produit_eqmsn, ref.a_confirmer) if c == "oui"]
    lines = {}
    for lab, line in zip(nc.produit.fillna("").astype(str).str.upper(), nc.ligne.fillna("").astype(str)):
        p = out["map"].get(lab)
        if p and line:
            lines.setdefault(p, {}).setdefault(line, 0)
            lines[p][line] += 1
    out["line"] = {p: (max(lines[p], key=lines[p].get) if p in lines else "") for p in out["std"]}
    out["alias"] = product_alias_rules()
    out["msnAsof"], out["msn"] = production_msn()
    asof, recs = _production_export()
    if asof:
        out["wd"] = working_day_volume(asof, recs)   # the page's default volume (Mohammad, 30 Oct)
    REPORT["eqmsn"] = {"products": len(out["std"]), "total_std": round(sum(sum(v) for v in out["std"].values()), 2),
                       "total_wd": round(sum(sum(v) for v in out.get("wd", {}).values()), 2),
                       "msn_dates": len(out["msn"] or {}), "msn_asof": out["msnAsof"]}
    return out


def product_alias_rules():
    """NC products the production plan does not name, put back on the plan product they belong to (04_reference/produits_alias.csv,
    agreed with Mohammad 29 Oct): [line, product regex, station regex or '', plan product]. The first rule that matches wins, and a
    rule applies only to a product that is not itself in the plan. The page applies the same rules to the 2026 NCs (fto2FromTables)."""
    path = os.path.join(ROOT, "04_reference", "produits_alias.csv")
    if not os.path.exists(path):
        return []
    t = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    return [[r.ligne, r.produit_nc, r.poste, r.produit_cible] for r in t.itertuples()]


def alias_product(rules, plan, line, prod, station):
    """The plan product of an NC product (see product_alias_rules); the product itself when no rule matches."""
    prod = prod or "Other"
    if prod.upper() in plan:
        return prod
    for l, rp, rs, to in rules:
        if l == line and re.search(rp, prod) and (not rs or re.search(rs, station or "", re.I)):
            return to
    return prod


def _production_export():
    """The newest 'Tableau Avances / Retards' export (06_input_data/Avances_Retards_*.csv): its date and one record per MSN and
    product, {line, prod, msn, plan, real} with the 8 milestone dates (Impression, Enclenchement, SE, MECA, INTE, TEST, QUALITE,
    Départ OTA) of the 'date prévue du début' and 'date réelle' rows. (None, []) without the file."""
    import csv, datetime as dt
    files = sorted(glob.glob(os.path.join(ROOT, "06_input_data", "Avances_Retards_*.csv")))
    if not files:
        return None, []
    asof = dt.date.fromisoformat(os.path.basename(files[-1])[len("Avances_Retards_"):-4])
    rows = list(csv.reader(open(files[-1], encoding="utf-8")))
    h = next(i for i, r in enumerate(rows) if r[:3] == ["S/HS", "Prog", "Produit"])

    def day(s):
        try:
            return dt.datetime.strptime(s.strip(), "%d/%m/%Y").date()
        except ValueError:
            return None
    recs, cur = [], None
    for r in rows[h + 1:]:
        if len(r) < 15:
            continue
        if r[14] == "date prévue du début" and r[3].strip():
            cur = {"line": r[1].strip(), "prod": EQ_NAMES.get(r[2].strip(), r[2].strip()), "msn": r[3].strip(), "plan": [day(x) for x in r[5:13]], "real": [None] * 8}
            recs.append(cur)
        elif r[14] == "date réelle" and cur:
            cur["real"] = [day(x) for x in r[5:13]]
    return asof, recs


def production_msn():
    """Each aircraft's build dates from the 'Tableau Avances / Retards' export (06_input_data/Avances_Retards_*.csv, newest file):
    four rows per MSN and product (planned start of each milestone, reason, real date, advance / delay). Per line|MSN:
    [start, end, products] where start = the first real milestone date (else the planned Impression date) and end = the real OTA
    (else the planned OTA), the earliest start and latest end over the aircraft's products. A real date after the export or more
    than 200 days from its plan is a typo and is ignored. Checked against the export's own 'en cours' flag on 07/10/2026: 130 of
    its 134 MSN in progress are in progress by this rule, and 7 more. The page hatches an aircraft built between start and end
    at the last NC date. Returns (export date, {line|msn: [start, end, products]}), or (None, None) without the file."""
    asof, recs = _production_export()
    if not asof:
        return None, None
    out = {}
    for c in recs:
        real = [x if x and x <= asof and not (p and abs((x - p).days) > 200) else None for x, p in zip(c["real"], c["plan"])]
        s, e = next((x for x in real if x), None) or c["plan"][0], real[7] or c["plan"][7]
        if not s or not e:
            continue
        k = c["line"] + "|" + c["msn"].lstrip("0")
        o = out.get(k)
        out[k] = [min(o[0], s.isoformat()), max(o[1], e.isoformat()), o[2] + [c["prod"]]] if o else [s.isoformat(), e.isoformat(), [c["prod"]]]
    return asof.isoformat(), out


def _french_holidays(year):
    """French public holidays of a year: the fixed ones and Easter Monday, Ascension and Whit Monday."""
    import datetime as dt
    a, (b, c) = year % 19, divmod(year, 100)
    d, e = divmod(b, 4)
    g = (b - (b + 8) // 25 + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    easter = dt.date(year, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)
    return {dt.date(year, mo, da) for mo, da in ((1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25))} | \
           {easter + dt.timedelta(n) for n in (1, 39, 50)}


def working_day_volume(asof, recs):
    """EqMSN per product and month of 2026 counted on the days the plant works. Same MSNs and dates as the EqMSN sheet (each MSN
    = 1.0 from its Impression date to its OTA, the real date else the planned one, the sheet script's date corrections: a real
    date after the export or more than 200 days from its plan is taken with the plan's year when that lands within 30 days of
    the plan, else the plan is used; the span reaches a real milestone entered after the OTA; a second block of the same MSN is
    dropped), but spread over Monday to Friday minus French public holidays, with the closures and quiet weeks of
    04_reference/calendrier_production.csv at their weight (0 or 0.5). July and August 2026 come to about 58 % of a normal month
    for the MIP A350, as its NCs do (Mohammad, 29 Oct); the sheet spreads over every calendar day (83 %). {product: 12 months}."""
    import datetime as dt
    cal = pd.read_csv(os.path.join(ROOT, "04_reference", "calendrier_production.csv"), encoding="utf-8")
    cal = [(dt.date.fromisoformat(a), dt.date.fromisoformat(b), float(w)) for a, b, w in zip(cal.debut, cal.fin, cal.poids)]
    hol = set().union(*(_french_holidays(y) for y in range(asof.year - 2, asof.year + 3)))

    def weight(d):
        if d.weekday() >= 5 or d in hol:
            return 0
        return next((w for a, b, w in cal if a <= d <= b), 1)

    def fix(x, p):
        if not x:
            return None
        if x <= asof and (not p or abs((x - p).days) <= 200):
            return x
        try:
            y = x.replace(year=p.year) if p else None
        except ValueError:
            y = None
        return y if y and y <= asof and abs((y - p).days) <= 30 else None
    out, seen = {}, set()
    for c in recs:
        if (c["prod"], c["msn"]) in seen:
            continue
        seen.add((c["prod"], c["msn"]))
        real = [fix(x, p) for x, p in zip(c["real"], c["plan"])]
        known = [x for x in real + c["plan"] if x]
        if not known:
            continue
        s = real[0] or c["plan"][0] or min(known)
        e = max([real[7] or c["plan"][7] or max(known)] + [x for x in real if x])
        if e < s:
            continue
        days = [s + dt.timedelta(n) for n in range((e - s).days + 1)]
        w = [weight(d) for d in days]
        tot = sum(w) or 1
        if not sum(w):
            w[-1] = 1
        m = out.setdefault(c["prod"], [0.0] * 12)
        for d, x in zip(days, w):
            if d.year == 2026 and x:
                m[d.month - 1] += x / tot
    return {p: [round(v, 2) for v in m] for p, m in out.items()}

def cnq_explain(d):
    """The CNQ parameters the "explain the calculation" part shows: times and rates, which steps each decision charges,
    minutes and material per defect class, the Airbus standard per decision, and the defect lines counted more than once."""
    import cnq.cnq_params as P
    kind = lambda b: "DERIVED" if b.startswith("TEAM RULE") else "RULE" if b.startswith("Rule from AEC") else b.split(" ")[0].upper()
    R = getattr(P, "STEP_RATES", None) or {}
    return {"p": {"rate": P.RATE_STANDARD, "rateEng": P.RATE_ENGINEERING, "rateProd": getattr(P, "RATE_PROD", P.RATE_STANDARD),
                  "rates": {"alert": R.get("alert"), "writing": R.get("writing"), "support": R.get("support"), "setup": R.get("setup"),
                            "hands": R.get("hands_on"), "recheck": R.get("recheck")} if R else None, "alert": P.MIN_ALERT, "write": P.MIN_WRITE_NC, "writeFinal": P.MIN_WRITE_NC_FINAL,
                  "support": P.MIN_SUPPORT, "setup": P.MIN_SETUP, "floor": P.MIN_WORK_FLOOR, "recheck": P.MIN_RECHECK_CLOSE,
                  "noDefect": P.MIN_HANDS_ON_NO_DEFECT, "writeGlobal": P.MIN_WRITE_NC_GLOBAL, "workGlobal": P.MIN_WORK_GLOBAL,
                  "defDefault": P.MIN_DEFAULT_DEFECT, "crExtra": P.CUSTOMER_RETURN_EXTRA, "version": P.MODEL_VERSION,
                  "connNext": P.MIN_CONNECTION_NEXT, "connCls": list(P.CONNECTION_CLASSES), "intTypes": list(P.INTERNAL_TYPES),
                  "intFactor": P.INTERNAL_WORK_FACTOR, "noAlert": list(P.NO_ALERT_TYPES), "orderTime": bool(getattr(P, "USE_ORDER_TIME", False)),
                  "aleaTime": bool(getattr(P, "USE_ALEA_TIME", False)), "aleaHours": list(getattr(P, "ALEA_LINK_HOURS", (-2, 72)))},
            "rules": {k: list(v[:8]) + [kind(v[8])] for k, v in P.RULES.items()},
            "cls": {k: [v[0], v[1], v[2], kind(v[4])] for k, v in P.DEFECT_TIMES.items()},
            "airbus": P.AIRBUS_STANDARD,
            "qty": {"%s|%d" % (r.notification_number, r.seq): int(r.qty) for r in d.itertuples() if pd.notna(r.qty) and int(r.qty) != 1}}


def nc_extras(r):
    return core.nc_extras(r, REPORT["created_to"])


FR_MONTHS = {"janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "août": 8,
             "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12}


def _month(s):
    m = re.search(r"([A-Za-zÀ-ÿ]+)\s+(20\d\d)", str(s or ""))
    if not m or m.group(1).lower() not in FR_MONTHS:
        return ""
    return "%s-%02d" % (m.group(2), FR_MONTHS[m.group(1).lower()])


def mft_actions():
    """Actions of the A330 and A350 MFT trackers, each tied to the problem it targets (04_reference/mft_actions_mapping.csv,
    to be checked by the line quality team): [line, label fr, label en, level, values, analysis month, action month, status,
    expected benefit month, defects text, root cause, action]."""
    mp = pd.read_csv(os.path.join(ROOT, "04_reference", "mft_actions_mapping.csv"), encoding="utf-8-sig", dtype=str)
    out = []
    for prog in ("A330", "A350"):
        t = pd.read_csv(os.path.join(ROOT, "06_input_data", "MFT_actions_%s.csv" % prog), skiprows=2, dtype=str).dropna(how="all")
        st = "Statut.1" if "Statut.1" in t.columns else "Statut"
        for _, a in t.iterrows():
            cat, dft = S_(a.get("NC Category (Type)")).strip(), S_(a.get("Défauts")).strip()
            m = mp[(mp.programme == prog) & (mp.nc_category.str.strip() == cat) & mp.defauts_debut.map(lambda p: dft.startswith(p))]
            if m.empty:
                say("MFT action not mapped:", prog, cat, dft[:40])
                continue
            m = m.iloc[0]
            clean = lambda s: re.sub(r"\s+", " ", S_(s)).strip()[:400]
            out.append([prog, m.libelle_fr, m.libelle_en, m.niveau, m.valeur.split("|"), _month(a.get("Début de l'analyse")),
                        _month(a.get("Début de l'action")), clean(a.get(st)), _month(a.get("Quand (bénéfices estimés)")),
                        clean(dft), clean(a.get("Analyse de cause racine")), clean(a.get("Action"))])
    REPORT["mft_actions"] = len(out)
    return out


def rca_reference(d):
    """The RCA page: hierarchy official sub-code -> sub-category -> RCA -> category, definitions, real examples."""
    ref = os.path.join(ROOT, "04_reference")
    sc = pd.read_csv(os.path.join(ref, "sous_categories.csv"), encoding="utf-8-sig")
    codes = pd.read_csv(os.path.join(ref, "reference_souscodes_pareto.csv"), encoding="utf-8-sig")
    codes = codes[~codes.sous_code.astype(str).str.startswith("(")]
    defs = pd.read_csv(os.path.join(ref, "rca_definitions.csv"), encoding="utf-8-sig").set_index("rca_nom")
    pool = d[(d.scope != "") & (d.llm_status == "ok") & (d.llm_confiance == "high") & d.text.fillna("").str.len().between(30, 170)]
    pool = pool.sort_values("date_creation", ascending=False)
    out = []
    for rca_nom, g in sc.groupby("rca_nom", sort=False):
        subs = []
        for s in g.itertuples():
            cc = codes[codes.sous_categorie == s.sous_categorie]
            subs.append({"name": s.sous_categorie, "minor": s.mineur == "oui", "note": S_(s.note),
                         "codes": [[c.sous_code, CODE_DESC.get(c.sous_code, [c.object_desc, c.object_desc])[0], CODE_DESC.get(c.sous_code, [c.object_desc, c.object_desc])[1]] for c in cc.itertuples()]})
        ex = pool[pool.llm_rca_nom == rca_nom].drop_duplicates("notification_number").head(3)
        df_ = defs.loc[rca_nom] if rca_nom in defs.index else None
        out.append({"rca": rca_nom, "cat": g.categorie.iloc[0], "fr": "" if df_ is None else df_.definition_fr, "en": "" if df_ is None else df_.definition_en,
                    "subs": subs, "ex": [[e.notification_number, " ".join(str(e.text).split()).strip(" *:-")] for e in ex.itertuples()]})
    REPORT["rca_without_definition"] = [o["rca"] for o in out if not o["fr"]]
    return out


def customer_return_extras(d, nc, lt):
    extra, texts, REPORT["customer_returns"] = core.customer_return_extras(d, nc, lt)
    return extra, texts


# ============================================================ workbooks
def _style(path, wrap_sheet=None, widths=None):
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = load_workbook(path)
    head = PatternFill("solid", fgColor="1F3864")
    for ws in wb:
        if ws.max_row < 1:
            continue
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = head; c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.freeze_panes = "C2" if ws.title != "Read me" else None
        for col in ws.columns:
            name = str(col[0].value or "")
            w = (widths or {}).get(name) or min(max(10, max(len(str(c.value or "")) for c in list(col)[:150]) * 0.9), 50)
            ws.column_dimensions[col[0].column_letter].width = w
        if ws.title == wrap_sheet:
            for row in ws.iter_rows(min_row=2):
                for c in row:
                    c.alignment = Alignment(wrap_text=True, vertical="top")
        if ws.title != "Read me":
            ws.auto_filter.ref = ws.dimensions
    if "Read me" in wb.sheetnames:
        wb["Read me"].column_dimensions["A"].width = 150
    wb.save(path)


def build_review(d, lt):
    f = d[(d.scope != "") & (d.sous_groupe != d.llm_sous_categorie)].copy()
    f["long_text"] = f.notification_number.map(lambda n: lt.get(n, "")[:1500])
    f = f.sort_values(["nb_defauts_nc", "notification_number", "seq"])
    dis = pd.DataFrame({"NC": f.notification_number, "Défaut #": f.seq, "Défauts dans la NC": f.nb_defauts_nc, "Où émise": f.scope.map({"serie": "Usine FTO2", "client": "Retour client", "autre": "Autre usine"}),
                        "Code écrit": f.code, "Extrait": f.text, "Texte complet": f.long_text,
                        "Parser – catégorie": f.groupe, "Parser – sous-catégorie": f.sous_groupe,
                        "Cause racine – catégorie": f.llm_categorie, "Cause racine – sous-catégorie": f.llm_sous_categorie,
                        "Symptôme": f.llm_symptome, "Raison": f.llm_raison, "Confiance": f.llm_confiance,
                        "Verdict (P = parser, L = cause racine, A = autre)": "", "Commentaire": ""})
    fto2 = d[d.scope == "serie"]
    cats = pd.DataFrame({"Parser v4.8": fto2.groupe.value_counts(), "Cause racine (texte complet)": fto2.llm_categorie.value_counts()}).fillna(0).astype(int)
    cats["Écart"] = cats.iloc[:, 1] - cats.iloc[:, 0]
    readme = pd.DataFrame({"Read me": [
        "Défauts où le classement par cause racine (modèle de langage, texte complet de la NC) diffère du parser v4.8. Périmètre série et retours clients (mêmes NC que le tableau de bord).",
        "Remplir la colonne Verdict pour mesurer lequel des deux a raison. Défauts des NC à un seul défaut en premier.",
        "Régénéré par build/build_all.py à partir des exports Skywise de 06_input_data."]})
    path = os.path.join(OUT, "FTO2_llm_longtext_review.xlsx")
    with pd.ExcelWriter(path) as w:
        readme.to_excel(w, sheet_name="Read me", index=False)
        cats.to_excel(w, sheet_name="Catégories FTO2")
        dis.to_excel(w, sheet_name="Désaccords", index=False)
    _style(path, wrap_sheet="Désaccords", widths={"Extrait": 50, "Texte complet": 70, "Raison": 40})
    REPORT["review_disagreements"] = int(len(dis))
    say("workbook: FTO2_llm_longtext_review.xlsx", len(dis), "rows")


def build_detail(d, nc, x):
    n = nc.set_index("notification_number")
    yn = lambda s: s.astype(bool).map({True: "Oui", False: "Non"})
    m = d.join(n[["statut", "closure_time", "msn", "phase", "type_nc_auto", "produit", "station", "station_description", "decision_label",
                  "liability", "user_department", "description_short"]], on="notification_number", rsuffix="_nc")
    kind = pd.cut(m.nb_defauts_nc, [0, 1, 10, 10 ** 6], labels=["Seul (1 défaut)", "Liste courte (2-10)", "Liste d'inspection (>10)"]).astype(str)
    out = pd.DataFrame({
        "NC": m.notification_number, "Défaut #": m.seq, "Défauts dans la NC": m.nb_defauts_nc, "Type de NC": kind,
        "Où émise": m.scope.map({"serie": "Usine FTO2", "client": "Retour client", "autre": "Autre usine"}).fillna(""), "Statut": m.statut, "Créée": m.date_creation, "Semaine": m.semaine,
        "Clôturée": pd.to_datetime(m.closure_time, errors="coerce", utc=True).dt.strftime("%Y-%m-%d"), "Ligne": m.ligne, "MSN": m.msn,
        "Phase": m.phase, "Type NC (pipeline)": m.type_nc_auto, "Produit": m.produit, "Site": m.plant, "Poste": m.station,
        "Description poste": m.station_description, "Décision": m.decision_label, "Responsabilité": m.liability, "Rédacteur": m.user_department,
        "FIN": m.fin, "Défaut (extrait)": m.text, "Code écrit": m.code,
        "Parser – catégorie": m.groupe, "Parser – sous-catégorie": m.sous_groupe, "Parser – RCA": m.rca_nom,
        "Cause racine – catégorie": m.llm_categorie, "Cause racine – sous-catégorie": m.llm_sous_categorie, "Cause racine – RCA": m.llm_rca_nom, "Sous-code officiel": m.sous_code_officiel, "Libellé du sous-code": m.sous_code_officiel.map(lambda c: CODE_DESC.get(c, ["", ""])[1]),
        "Symptôme": m.llm_symptome, "Confiance": m.llm_confiance, "Statut du label": m.llm_status,
        "Mineur": yn(m.mineur), "Défaut câble": yn(m.defaut_cable), "Provenance câble": m.provenance.where(m.defaut_cable, ""),
        "CNQ réparti (EUR)": m.cnq_cost_allocated_llm.round(2), "Titre NC": m.description_short,
    }).sort_values(["Créée", "NC", "Défaut #"], ascending=[False, True, True])
    summ_rows = []
    f = d[d.scope == "serie"]
    for cat in ["MEO Facteur humain", "Erreur Branchement", "Élément Manquant", "Élément Endommagé", "Déverrouillage", "Grounding/Bonding", "Kitting Factory", "FOD", "Autre"]:
        p, l = f[f.groupe == cat], f[f.llm_categorie == cat]
        summ_rows.append([cat, len(p), len(l), int(l.llm_defaut_cable.sum()), int(l.llm_mineur.sum()), round(float(l.cnq_cost_allocated_llm.sum()))])
    summ = pd.DataFrame(summ_rows, columns=["Catégorie", "Défauts série (parser)", "Défauts série (cause racine)", "dont câble", "dont mineurs", "CNQ réparti (EUR)"])
    readme = pd.DataFrame({"Read me": [
        "Une ligne par défaut, NC créées du %s au %s, exports Skywise de 06_input_data (sélection standard complète, complétée par numéro avec les listes GPS et Test)." % (REPORT["created_from"], REPORT["created_to"]),
        "Où émise (comme le tableau de bord) : Usine FTO2 = plant FTO2 ou FT02 ; Retour client = Type_NC_auto du pipeline « NC Retour client » avec FTO2 dans la responsabilité ; Autre usine = le reste. Toutes les NC du pipeline sont là, supprimées et fournisseur comprises.",
        "Deux classements : parser v4.8 (règles, comme dans Skywise) et cause racine (modèle de langage avec le texte complet, 12 oct. 2026, non vérifié à la main).",
        "CNQ réparti : coût de la NC (modèle cnq-2026.10, niveau 3) partagé entre ses défauts. Seules les NC dont FTO2 est responsable ont un coût.",
        "Régénéré par build/build_all.py."]})
    path = os.path.join(OUT, "FTO2_defects_detail.xlsx")
    with pd.ExcelWriter(path) as w:
        out.to_excel(w, sheet_name="Défauts", index=False)
        summ.to_excel(w, sheet_name="Synthèse", index=False)
        readme.to_excel(w, sheet_name="Read me", index=False)
    _style(path, widths={"Défaut (extrait)": 60, "Titre NC": 35, "Description poste": 26})
    say("workbook: FTO2_defects_detail.xlsx", len(out), "rows")


if __name__ == "__main__":
    main()
