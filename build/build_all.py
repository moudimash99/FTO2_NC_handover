# -*- coding: utf-8 -*-
"""
Rebuild every FTO2 NC output from the raw Skywise exports, in one run.

    python3 build/build_all.py

Input (the only data read):
    06_input_data/fto2_dashboard_data*.csv     Skywise NC exports (standard + missing-IDs). All files are merged;
                                               when an NC is in several, the most recently changed row wins.
    04_reference/llm_labels_longtext.csv       Root-cause labels per defect line (Sonnet, full long text, 12 Oct 2026).

Steps:
    1. parser v4.8 (02_dashboard_pack/.../fto2_logic.py)  -> one row per defect, one row per NC, scope (perimetre)
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

REPORT = {}


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
    x = pd.concat(frames, ignore_index=True)
    x["notification_number"] = x["notification_number"].astype(str).str.strip()
    x["_changed"] = pd.to_datetime(x["changed_time"], errors="coerce", utc=True)
    x = x.sort_values("_changed").drop_duplicates("notification_number", keep="last").reset_index(drop=True)
    REPORT["inputs"] = {os.path.basename(f): int((x["_source"] == os.path.basename(f)).sum()) for f in files}
    REPORT["nc_rows"] = int(len(x))
    created = pd.to_datetime(x["creation_time"], errors="coerce", utc=True)
    REPORT["created_from"], REPORT["created_to"] = str(created.min().date()), str(created.max().date())
    return x


def clean_long_text(t):
    t = str(t or "")
    t = re.sub(r"(?:--\s*){3,}", "", t)
    t = re.sub(r"Tél\.\s*[^\n]*", "", t)
    t = re.sub(r"#(UID|TEL|PRS)~", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\*?\s*\n", "\n", t)
    return t.strip()


def week_of(iso):
    d = pd.Timestamp(iso)
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


# ============================================================ main
def main():
    x = load_exports()
    say("exports:", REPORT["inputs"], "->", len(x), "NCs")
    defects = L.build_defects(x)
    nc = L.build_nc(x, defects)
    defects["notification_number"] = defects["notification_number"].astype(str)
    say("parser v4.8:", len(defects), "defect lines in", defects.notification_number.nunique(), "NCs")

    # NC fields from the export that the parser datasets do not carry
    keep = {"decision_status": "decision_status", "decision_status_description_en": "decision_label", "liability": "liability",
            "liability_description": "liability_description", "responsible_defect_level1": "responsible_level1",
            "responsible_defect_level1_name": "responsible_level1_name", "station": "station", "station_description": "station_description",
            "work_ctr": "work_ctr", "user_department": "user_department", "description_short": "description_short",
            "msn": "msn", "trigger": "trigger", "notification_type": "notification_type", "closure_time": "closure_time",
            "Type_NC_auto": "type_nc_auto", "GPS_Type_NC": "gps_type_nc", "Programme_auto": "phase", "Produit_auto": "produit",
            "Origin_auto": "origin_auto", "Ext_Source": "ext_source", "defect_code_description_en": "sap_defect_code",
            "cause_group_description_en": "sap_cause_group", "cause_code_description_en": "sap_cause_code", "creation_time": "creation_ts", "_source": "source_file"}
    ex = x[["notification_number"] + list(keep)].rename(columns=keep)
    ex["type_nc"] = ex["gps_type_nc"].where(ex["gps_type_nc"].notna(), ex["type_nc_auto"])
    nc = nc.merge(ex, on="notification_number", how="left")
    lt = dict(zip(x.notification_number, x.description_long_text.map(clean_long_text)))

    # ======================================================== 2. long-text labels
    lab = pd.read_csv(os.path.join(ROOT, "04_reference", "llm_labels_longtext.csv"), dtype={"notification_number": str}, encoding="utf-8-sig")
    d = defects.merge(lab, on=["notification_number", "seq"], how="left")
    norm = lambda s: s.fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    same_text = (norm(d["text"]) == norm(d["snippet"])) | (norm(d["text"]).isin(["", "N/A"]) & (norm(d["snippet"]) == ""))
    d["llm_status"] = np.where(d["llm_sous_categorie"].isna(), "a_labelliser", np.where(same_text, "ok", "texte_change"))
    # a line without a usable label falls back to the parser label, so every chart stays complete
    use = d["llm_status"] == "ok"
    for c_llm, c_par in (("llm_sous_categorie", "sous_groupe"), ("llm_defaut_cable", "defaut_cable")):
        d[c_llm] = d[c_llm].where(use, d[c_par])
    d["llm_defaut_cable"] = d["llm_defaut_cable"].astype(str).str.lower().isin(["true", "1"])
    d["llm_categorie"] = d["llm_sous_categorie"].map(lambda s: PARSER.SOUS_CATEGORIES.get(s, ("Autre",))[0])
    d["llm_rca_type"] = d["llm_sous_categorie"].map(lambda s: PARSER.SOUS_CATEGORIES.get(s, (None, "AUTRE"))[1])
    d["llm_rca_nom"] = d["llm_rca_type"].map(L.RCA_NAMES).fillna("Non classé")
    d["llm_mineur"] = d["llm_sous_categorie"].map(PARSER.est_mineur)
    d["sous_code_officiel"] = official_subcode(d)
    d = d.drop(columns=["snippet"])
    REPORT["labels"] = d["llm_status"].value_counts().to_dict()
    say("labels:", REPORT["labels"])

    # ======================================================== 3. CNQ, both classifications
    nc_in = nc.rename(columns={"responsabilite": "responsabilite"})[
        ["notification_number", "statut", "decision_status", "liability", "date_creation", "type_nc", "produit",
         "responsabilite", "perimetre", "programme", "plant"]].copy()
    runs = {}
    for key, sub, cab in (("parser", "sous_groupe", "defaut_cable"), ("llm", "llm_sous_categorie", "llm_defaut_cable")):
        dd = d[["notification_number", "seq", "qty", sub, cab]].rename(columns={sub: "sous_groupe", cab: "cable"})
        n_out, d_out = compute_cnq(nc_in, dd)
        # share each NC's cost among its defect lines: the line's own work and material + an equal part of the rest
        a = n_out.set_index("notification_number")
        lines = d_out.groupby("notification_number")["seq"].transform("size")
        direct_sum = d_out.groupby("notification_number")["cnq_cost_direct"].transform("sum")
        nc_cost = d_out["notification_number"].map(a["cnq_cost_total"]) * d_out["cnq_on_aec"]
        d_out["cnq_cost_allocated"] = d_out["cnq_cost_direct"] + (nc_cost - direct_sum * d_out["cnq_on_aec"]) / lines
        runs[key] = (n_out, d_out)
    np_, dp_ = runs["parser"]
    nl_, dl_ = runs["llm"]          # root-cause labels: the main figures
    REPORT["unknown_cnq_classes"] = sorted(set(d.sous_groupe) - set(__import__("cnq.cnq_params", fromlist=["x"]).DEFECT_TIMES))

    # reference datasets
    dp_i = dp_.set_index(["notification_number", "seq"])
    dl_i = dl_.set_index(["notification_number", "seq"])
    k = list(zip(d.notification_number, d.seq))
    d["cnq_cost_direct"] = [dp_i.at[i, "cnq_cost_direct"] for i in k]
    d["cnq_cost_allocated"] = [dp_i.at[i, "cnq_cost_allocated"] for i in k]
    d["cnq_cost_direct_llm"] = [dl_i.at[i, "cnq_cost_direct"] for i in k]
    d["cnq_cost_allocated_llm"] = [dl_i.at[i, "cnq_cost_allocated"] for i in k]
    d["nb_defauts_nc"] = d.groupby("notification_number")["seq"].transform("size")
    d["semaine"] = d["date_creation"].map(lambda s: week_of(s) if s else "")
    cnq_cols = [c for c in np_.columns if c.startswith("cnq_")]
    nc_ref = nc.merge(nl_[["notification_number"] + cnq_cols], on="notification_number", how="left")
    pc = np_.set_index("notification_number")
    for c in ("cnq_cost_total", "cnq_cost_work", "cnq_cost_material", "cnq_cost_global"):
        nc_ref[c + "_parser"] = nc_ref.notification_number.map(pc[c])
    nc_ref["nc_cable"] = nc_ref.notification_number.isin(set(d[d.defaut_cable].notification_number))
    nc_ref["nc_cable_llm"] = nc_ref.notification_number.isin(set(d[d.llm_defaut_cable].notification_number))
    nc_ref["long_text"] = nc_ref.notification_number.map(lt)
    # the reporting scope used by every page, so all of them count the same NCs:
    #   serie  = raised at FTO2, FTO2 in the liability, not deleted
    #   client = customer return (raised elsewhere, FTO2 in the liability, not deleted)
    liab_f = nc_ref["liability"].fillna("").astype(str).str.upper().str.contains("FTO2")
    nc_ref["scope"] = np.select([(nc_ref.perimetre == "FTO2") & liab_f, nc_ref.perimetre == "Retour client"], ["serie", "client"], default="")
    d["scope"] = d.notification_number.map(nc_ref.set_index("notification_number")["scope"]).fillna("")
    d["phase"] = d.notification_number.map(nc_ref.set_index("notification_number")["phase"]).fillna("")
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
    REPORT["scope"] = nc_ref.perimetre.value_counts().to_dict()
    REPORT["report_scope"] = {k: {"ncs": int((nc_ref.scope == k).sum()), "ncs_without_defect_line": int(((nc_ref.scope == k) & (nc_ref.cnq_defect_lines == 0)).sum()),
                                  "defects": int((d.scope == k).sum()), "cnq": round(float(nc_ref.loc[nc_ref.scope == k, "cnq_cost_total"].sum()), 2)}
                              for k in ("serie", "client")}
    REPORT["defects_by_scope"] = d.perimetre.value_counts().to_dict()

    # ======================================================== 4a. CNQ package: same data, same totals
    refresh_cnq_package(nc_in, d)
    # ======================================================== 4b. pages and workbooks
    build_dashboard(d, nc_ref, lt)
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
def _page(template, data, name, page="main"):
    t = open(os.path.join(ROOT, "build", "templates", template), encoding="utf-8").read().replace("__PAGE__", page)
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


def build_dashboard(d, nc, lt):
    rca = lambda t: L.RCA_NAMES.get(t, t)
    ncd = nc.set_index("notification_number")
    defs = []
    for r in d.itertuples():
        defs.append([r.notification_number, int(r.seq), r.date_creation, r.semaine, S_(r.ligne), r.perimetre,
                     r.groupe, rca(r.rca_type), r.sous_groupe, int(bool(r.mineur)), int(bool(r.defaut_cable)),
                     r.llm_categorie, r.llm_rca_nom, r.llm_sous_categorie, int(bool(r.llm_mineur)), int(bool(r.llm_defaut_cable)),
                     round(float(r.cnq_cost_allocated), 2), round(float(r.cnq_cost_allocated_llm), 2), S_(r.text)[:220],
                     "", r.scope, S_(r.phase), r.sous_code_officiel, S_(r.fin)])   # [19] kept empty: the labelling notes are working notes, not for the page
    ncs = []
    for r in nc.itertuples():
        if not r.date_creation:
            continue
        ncs.append([r.notification_number, r.date_creation, week_of(r.date_creation), S_(r.ligne), r.perimetre, int(r.cnq_on_aec), r.cnq_rule,
                    r.cnq_decision_label, r.cnq_where_found, round(r.cnq_cost_airbus, 2), round(r.cnq_cost_global, 2), round(r.cnq_cost_total_parser, 2),
                    round(r.cnq_cost_total, 2), round(r.cnq_cost_admin, 2), round(r.cnq_cost_work_parser, 2), round(r.cnq_cost_work, 2),
                    round(r.cnq_cost_material_parser, 2), round(r.cnq_cost_material, 2), round(r.cnq_cost_engineering, 2),
                    int(r.nc_cable), int(r.nc_cable_llm), int(r.cnq_defect_lines), S_(r.description_short)[:80], r.scope, S_(r.phase)]
                   + nc_extras(r))
    direct = {"%s|%d" % (r.notification_number, r.seq): [round(float(r.cnq_cost_direct), 2), round(float(r.cnq_cost_direct_llm), 2)]
              for r in d.itertuples() if r.cnq_cost_allocated or r.cnq_cost_allocated_llm}
    aec = nc[nc.cnq_on_aec == 1]
    dele, other = aec.cnq_rule == "DELETED", (aec.scope == "") & (aec.cnq_rule != "DELETED")
    aside = {"deleted": [int(dele.sum()), round(float(aec.loc[dele, "cnq_cost_total"].sum()), 2)],
             "other": [int(other.sum()), round(float(aec.loc[other, "cnq_cost_total"].sum()), 2)]}
    no_line = int(((nc.scope == "serie") & (nc.cnq_defect_lines == 0)).sum())
    client, lt_client = customer_return_extras(d, nc, lt)
    actions = mft_actions()
    data = {"defects": defs, "ncs": ncs, "direct": direct, "rca": rca_reference(d), "client": client, "lt": lt_client, "codes": CODE_DESC, "actions": actions,
            "meta": {"from": "2026-01-01", "to": REPORT["created_to"], "aside": aside, "noLine": no_line,
                     "modelTotal": round(float(aec.cnq_cost_total.sum()), 2)}}
    _page("dashboard.html", data, "FTO2_NC_Dashboard.html")
    _page("dashboard.html", data, "FTO2_Suivi_Hebdo.html", page="suivi")
    slate_pack(data)
    slate_pack(data, page="suivi")


def nc_extras(r):
    """NC fields for the aircraft, product, lead-time, time-of-day and NC charts: [msn, product family, station, creation hour (Paris),
    days to close (None while open), open, age in days if open, closure date, NC type, liability, SAP defect code, SAP cause group,
    SAP cause, status]. SAP labels lose their brackets."""
    msn = S_(r.msn)
    msn = msn[:-2] if msn.endswith(".0") else msn
    created = pd.to_datetime(r.creation_ts, errors="coerce", utc=True)
    closed = pd.to_datetime(r.closure_time, errors="coerce", utc=True)
    hour = int(created.tz_convert("Europe/Paris").hour) if pd.notna(created) else -1
    is_open = int(r.statut == "open")
    lead = round((closed - created).total_seconds() / 86400, 2) if pd.notna(created) and pd.notna(closed) and not is_open else None
    end = pd.Timestamp(REPORT["created_to"] + "T23:59:59", tz="UTC")
    age = round((end - created).total_seconds() / 86400, 1) if is_open and pd.notna(created) else None
    sap = lambda v: S_(v).strip().strip("[]").strip()
    return [msn, S_(r.produit) or "Other", S_(r.station_description).strip(), hour, lead, is_open, age,
            closed.strftime("%Y-%m-%d") if pd.notna(closed) else "", S_(r.type_nc).strip(), sap(r.liability), sap(r.sap_defect_code),
            sap(r.sap_cause_group), sap(r.sap_cause_code), S_(r.statut)]


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


CODE_DESC = {}


def official_subcode(d):
    """Official sub-code of each defect line: the one chosen by the long-text labelling; for the approved exceptions,
    which have no sub-code of their own, the parent code (E1 = part of Q06-001; E2 = a Q11 component code)."""
    ref = pd.read_csv(os.path.join(ROOT, "04_reference", "reference_souscodes_pareto.csv"), encoding="utf-8-sig")
    ref = ref[~ref.sous_code.astype(str).str.startswith("(")]
    fr = pd.read_csv(os.path.join(ROOT, "04_reference", "souscodes_fr.csv"), encoding="utf-8-sig").set_index("sous_code").description_fr
    missing = sorted(set(ref.sous_code) - set(fr.index))
    assert not missing, "French description missing in 04_reference/souscodes_fr.csv for: %s" % missing
    CODE_DESC.update({c: [en, fr[c]] for c, en in zip(ref.sous_code, ref.object_desc)})
    first = ref.groupby("sous_categorie").sous_code.first()
    fallback = {"Câble à refaire (ligne)": "Q06-001", "Composant HS": "Q11 (composant)", "Composant – cause non écrite": "Q11 (composant)",
                "Non classé": "Non codé"}
    CODE_DESC.update({"Q11 (composant)": ["Component (sub-code not specified)", "Composant (sous-code non précisé)"], "Non codé": ["No code", "Sans code"]})
    out = []
    for code, sub, status in zip(d.llm_sous_code.fillna("").astype(str).str.strip(), d.llm_sous_categorie, d.llm_status):
        if status == "ok" and code in CODE_DESC:
            out.append(code)
        elif sub in fallback:
            out.append(fallback[sub])
        elif sub in first.index:
            head = first[sub][:3] + " (non précisé)"
            CODE_DESC.setdefault(head, ["Sub-code not specified", "Sous-code non précisé"])
            out.append(head)
        else:
            out.append("Non codé")
    s = pd.Series(out, index=d.index)
    REPORT["subcodes"] = {"exact": int(s.isin(ref.sous_code).sum()), "parent_or_none": int((~s.isin(ref.sous_code)).sum())}
    return s


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
    """Customer-return tab: damage type, detection, observed consequence, cause text, plant, liability; and the NC texts."""
    ncd = nc.set_index("notification_number")
    r = d[d.scope == "client"]
    extra, texts = {}, {}
    for x in r.itertuples():
        n = ncd.loc[x.notification_number]
        L_ = lt.get(x.notification_number, "")
        det = re.search(r"Moment of Detection\s*:\s*([^\n]+)", L_)
        det = det.group(1).strip() if det else ""
        nat = ""
        if x.llm_categorie == "Élément Endommagé":
            if re.search(r"unpacking|reception", det, re.I):
                nat = "recu"
            elif x.llm_sous_categorie == "Composant HS":
                nat = "hs"
            elif x.llm_sous_categorie == "Composant – cause non écrite":
                nat = "nc"
            else:
                nat = "phys"
        sym = S_(x.llm_symptome)
        extra["%s|%d" % (x.notification_number, x.seq)] = [nat, det, sym[:1].upper() + sym[1:], "", S_(n.plant), S_(n.liability)]
        texts[x.notification_number] = L_[:2500]
    REPORT["customer_returns"] = {"ncs": int((nc.scope == "client").sum()), "defects": int(len(r)),
                                  "damage_types": pd.Series([v[0] for v in extra.values() if v[0]]).value_counts().to_dict()}
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
    dis = pd.DataFrame({"NC": f.notification_number, "Défaut #": f.seq, "Défauts dans la NC": f.nb_defauts_nc, "Périmètre": f.scope.map({"serie": "Série", "client": "Retour client"}),
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
        "Périmètre": m.perimetre, "Périmètre rapport": m.scope.map({"serie": "Série", "client": "Retour client"}).fillna(""), "Statut": m.statut, "Créée": m.date_creation, "Semaine": m.semaine,
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
    for cat in ["MEO Câblage", "Erreur Branchement", "Élément Manquant", "Élément Endommagé", "Déverrouillage", "Grounding/Bonding", "Kitting Factory", "FOD", "Autre"]:
        p, l = f[f.groupe == cat], f[f.llm_categorie == cat]
        summ_rows.append([cat, len(p), len(l), int(l.llm_defaut_cable.sum()), int(l.llm_mineur.sum()), round(float(l.cnq_cost_allocated_llm.sum()))])
    summ = pd.DataFrame(summ_rows, columns=["Catégorie", "Défauts série (parser)", "Défauts série (cause racine)", "dont câble", "dont mineurs", "CNQ réparti (EUR)"])
    readme = pd.DataFrame({"Read me": [
        "Une ligne par défaut, NC créées du %s au %s, exports Skywise de 06_input_data (le standard est limité aux 1 000 NC les plus récentes, complété par numéro)." % (REPORT["created_from"], REPORT["created_to"]),
        "Périmètre rapport (celui du tableau de bord) : Série = émise à FTO2, FTO2 responsable, non supprimée ; Retour client = émise hors FTO2 avec FTO2 responsable. La colonne Périmètre garde le détail du pack (FTO2, Hors périmètre, Fournisseur, Supprimée).",
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
