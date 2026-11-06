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
CNQ = os.path.join(ROOT, "cnq_handoever")
OUT = os.path.join(ROOT, "05_outputs")
REP = os.path.join(ROOT, "03_reports")
sys.path.insert(0, ROOT)                                 # the fto2 backend package and config/
from fto2 import config                                 # noqa: E402   the settings in config/
from fto2.parser import fto2_logic as L                 # noqa: E402   the defect reader and the NC columns
from fto2.parser import nc_defect_parser as PARSER      # noqa: E402
from fto2.cost.model import compute_cnq, parameters_as_tables  # noqa: E402   the cost model, settings in config/
from fto2.cost import explain                                   # noqa: E402   the cost explanation of each NC (fto2_dash_cout)
sys.path.insert(0, os.path.join(ROOT, "build"))
from fto2 import core                                   # noqa: E402   the data steps, shared with the Skywise notebook
import page_template                                    # noqa: E402   the page template with its calculations (build/templates/model.js)
from fto2 import reference as REF                       # noqa: E402   the reference data (plan, 2025, cables, actions...)
from fto2.reference import (EQ_NAMES, alias_product, cable_requests, cnq_explain, mft_actions, product_alias_rules,  # noqa: E402,F401
                            production_msn, rca_reference, reference_block, working_day_volume)

REPORT = {}
CODE_DESC = {}   # official sub-code -> [en, fr], filled by the data steps


def say(*a):
    print(*a, flush=True)


# ============================================================ 1. raw exports -> parser
def _raw_times_as_export(raw):
    """A raw Skywise extract gives local times ("2026-10-19 14:01:44", +02:00) and their UTC twins (creation_utc_time...); the
    exports give UTC as "2026-10-19T12:01:44Z". The times become the exports' form, from the UTC columns (completion_time, which
    has none, from its local time and offset), so that every NC reads the same way."""
    iso = lambda t: t.dt.strftime("%Y-%m-%dT%H:%M:%SZ").where(t.notna(), None)
    for c in ("creation_time", "changed_time", "closure_time", "completion_time"):
        u = c.replace("_time", "_utc_time")
        if u in raw.columns:
            raw[c] = iso(pd.to_datetime(raw[u], errors="coerce", format="%Y-%m-%d %H:%M:%S"))
        elif c in raw.columns:
            local = pd.to_datetime(raw[c], errors="coerce", format="%Y-%m-%d %H:%M:%S")
            off = raw.get(c + "_tz", pd.Series("", index=raw.index)).fillna("").astype(str)
            mins = off.str.extract(r"([+-])(\d\d):(\d\d)").apply(
                lambda m: (1 if m[0] == "+" else -1) * (int(m[1]) * 60 + int(m[2])) if isinstance(m[0], str) else 0, axis=1)
            raw[c] = iso(local - pd.to_timedelta(mins, unit="m"))
    return raw


def load_exports():
    """The pipeline notebook's NC exports (06_input_data/fto2_dashboard_data*.csv), plus the NCs of raw Skywise extracts
    (06_input_data/nc_2026_skywise_*.csv, e.g. the extract of 3 Nov: FTO2 NCs created 1 Sep - 26 Oct) that the exports do not
    hold, through the notebook's own rules (fto2_core.pipeline_rules, as for 2025). An NC in an export keeps its export row: the
    exports carry the GPS register and Test list columns that a raw extract does not."""
    files = sorted(glob.glob(os.path.join(ROOT, "06_input_data", "fto2_dashboard_data*.csv")))
    frames = []
    for f in files:
        x = pd.read_csv(f, low_memory=False, dtype={"notification_number": str})
        x["_source"] = os.path.basename(f)
        frames.append(x)
    key = lambda s: s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.lstrip("0")
    have = set().union(*[set(key(x["notification_number"])) for x in frames]) if frames else set()
    raws = sorted(glob.glob(os.path.join(ROOT, "06_input_data", "nc_2026_skywise_*.csv*")))
    for f in raws:
        raw = pd.read_csv(f, dtype=str, keep_default_na=False, na_values=[""], low_memory=False)
        raw["notification_number"] = key(raw["notification_number"])
        raw = raw[~raw["notification_number"].isin(have)].copy()
        raw = _raw_times_as_export(raw)
        r = core.pipeline_rules(raw, core.station_pairs(frames))
        r["_source"] = os.path.basename(f)
        have |= set(r["notification_number"])
        frames.append(r)
        files.append(f)
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
    """2025 for the year comparisons, from the raw Skywise NC extract of 2025 (06_input_data/nc_2025_skywise_fto2.csv.gz): see
    fto2/reference.py. None when the extract is missing."""
    path = os.path.join(ROOT, "06_input_data", "nc_2025_skywise_fto2.csv.gz")
    if not os.path.exists(path):
        return None
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    out = REF.year_2025(raw, core.station_pairs([x]))
    REPORT["y2025"] = REF.REPORT["y2025"]
    return out


# ============================================================ main
def main():
    x = load_exports()
    say("exports:", REPORT["inputs"], "->", len(x), "NCs")
    ops, dis = load_orders(), load_disruptions()
    lab = pd.read_csv(os.path.join(ROOT, "04_reference", "llm_labels_longtext.csv"), dtype={"notification_number": str}, encoding="utf-8-sig")
    y25 = year_2025(x.copy())
    say("2025:", REPORT.get("y2025"))
    p = core.prepare(x, lab, ops, dis)   # parser, labels, CNQ, rework orders, aléas, scope: build/fto2_core.py
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
    REPORT.update({k: v for k, v in REF.REPORT.items() if k not in REPORT})   # counts from the reference data
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
    t = page_template.read(template).replace("__PAGE__", page)
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
    t = page_template.read(template)
    css = re.sub(r"/\*.*?\*/", "", t.split("<style>", 1)[1].split("</style>", 1)[0], flags=re.S)
    fonts = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">', t)
    html = t[t.index('<div class="wrap">'):t.index('<script type="application/json" id="fto2-data">')].strip()   # the page, without its data
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
    data = {"defects": defs, "ncs": ncs, "direct": direct, "rca": rca_reference(d, CODE_DESC), "client": client, "lt": lt_client, "codes": CODE_DESC, "actions": actions,
            "cnqp": cnq_explain(d), "cables": cable_requests(),
            "meta": {"from": config.parameter("date_debut"), "to": REPORT["created_to"], "aside": aside, "noLine": no_line,
                     "modelTotal": round(float(aec.cnq_cost_total.sum()), 2)}}
    # every page carries the production file (rates per MSN); only the review pages carry the made-up gallery data (never in the Slate files)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I leaves the script folder off the path
    import dummy_data
    data["eqmsn"] = REF.eqmsn(nc, os.path.join(OUT, "fto2_msn_semaine.csv"))
    data["y25"] = y25
    data["settings"] = REF.page_settings()   # the pages' settings (config/2_reglages_pages.csv...)
    dis_t = dis_t if dis_t is not None else core.dis_table(None)
    data["dis"] = [[None if (isinstance(v, float) and np.isnan(v)) else v for v in r] for r in dis_t.values.tolist()]   # as the JS adapter gives it
    local = dict(data, dummy=dummy_data.make(ROOT))
    # the main page goes through the two tables, as in Skywise: the JS (fto2FromTables) rebuilds the page's data from them
    nc_t, def_t = core.tables(d, nc, lt, REPORT["created_to"])
    nc_t.to_csv(os.path.join(OUT, "fto2_dash_nc.csv"), index=False, encoding="utf-8-sig")
    def_t.to_csv(os.path.join(OUT, "fto2_dash_defects.csv"), index=False, encoding="utf-8-sig")
    dis_t.to_csv(os.path.join(OUT, "fto2_dash_disruptions.csv"), index=False, encoding="utf-8-sig")
    REPORT["dash_tables"] = {"nc": int(len(nc_t)), "defects": int(len(def_t)), "disruptions": int(len(dis_t))}
    # the reference data, as the Skywise notebook writes it (dataset fto2_dash_ref): the dashboard's, the MFT page's, Elizabeth's
    blocks = {"dashboard": REF.dashboard_block(d, nc, CODE_DESC, y25), "mft": REF.mft_block(data["eqmsn"]),
              "elizabeth": {"vol": REF.weekly_volume(data["eqmsn"]), "settings": REF.page_settings()}}
    REF.ref_table(blocks).to_csv(os.path.join(OUT, "fto2_dash_ref.csv"), index=False, encoding="utf-8-sig")
    # the cost explanation of each NC as the notebook works it out (fto2_dash_cout): read by the page only in the Skywise set-up
    # with two Slate functions; the laptop page works it out itself
    cx_t = explain.table(nc_t, def_t, blocks["dashboard"]["cnqp"])
    cx_t.to_csv(os.path.join(OUT, "fto2_dash_cout.csv"), index=False, encoding="utf-8-sig")
    REPORT["dash_tables"]["cout"] = int(len(cx_t))
    src = {"tables": {"nc": colmajor(nc_t), "def": colmajor(def_t), "dis": colmajor(dis_t)}, "ref": blocks["dashboard"]}
    _page("dashboard.html", src, "FTO2_NC_Dashboard.html")
    # the proposed final layout, chart by chart, with the choices to make (review page, local only)
    _page("dashboard.html", local, "FTO2_Revue_Proposition.html", page="review")
    # the same layout as a mock-up of the final dashboard, every chart scored a to e at its side (local only)
    _page("dashboard.html", local, "FTO2_Maquette_Notee.html", page="mock")
    _page("dashboard.html", data, "FTO2_Suivi_Hebdo.html", page="suivi")
    # the two monthly views, Synthèse (QCM) and Détail (QLS), made of this dashboard's charts (build/build_vues.py rebuilds it alone)
    _page("dashboard.html", src, "FTO2_Vues.html", page="vues", title="FTO2 · Synthèse et détail")
    slate_pack(data)
    slate_pack(data, page="suivi")
    import skywise_pack   # the four Skywise migration levels (03_reports/skywise): build/skywise_pack.py
    REPORT["skywise"] = skywise_pack.build(src["ref"], ROOT, _scope_css, say)
    import views_pack   # Synthèse and Détail for Slate, two ways (03_reports/skywise/views): build/views_pack.py
    views_pack.build(say)


def colmajor(df):
    """A table as Slate returns a query result: one array per column (empty -> null)."""
    return {c: [None if (isinstance(v, float) and np.isnan(v)) else v for v in df[c].tolist()] for c in df.columns}


def nc_extras(r):
    return core.nc_extras(r, REPORT["created_to"])


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
