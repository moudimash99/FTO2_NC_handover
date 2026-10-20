# -*- coding: utf-8 -*-
"""
Build the CNQ investigation checklist (one offline HTML file) and the CNQ changes document.

    python3 -I build_checklist_html.py <P> <repo> <disrup.csv>

Writes <repo>/05_outputs/CNQ_investigation_checklist.html and <repo>/CNQ_CHANGES.md.
<P> is the folder written by load.py and the other scripts of this folder (see README.md);
run sheet_data.py first.
"""
import datetime, json, re, sys
import numpy as np, pandas as pd

D, REPO, DISRUP = sys.argv[1:4]
wo = pd.read_pickle(D + "/wo.pkl"); wo["h"] = pd.to_numeric(wo.labor_standard_value, errors="coerce").fillna(0) / 100
fam = pd.read_pickle(D + "/s03_family.pkl")
nr = pd.read_pickle(D + "/nc_rw.pkl"); n26, n25 = nr["2026"], nr["2025"]
X = pd.read_pickle(D + "/sheet_data.pkl"); R = X["R"]
ds = pd.read_pickle(D + "/ds2.pkl"); ds["tl"] = pd.to_numeric(ds.time_lost)
raw = pd.read_csv(DISRUP, dtype=str, encoding="utf-8-sig", keep_default_na=False, na_values=[""])
RATE = 50.0
one = lambda s, n=400: "" if not isinstance(s, str) else " ".join(s.split())[:n]
paris = lambda s: s.dt.tz_convert("Europe/Paris")


def rows(df):
    out = []
    for rec in df.to_dict("records"):
        r = {}
        for k, v in rec.items():
            if isinstance(v, (float, np.floating)):
                v = None if np.isnan(v) else round(float(v), 2)
            elif isinstance(v, (np.integer,)):
                v = int(v)
            elif v is None or (not isinstance(v, str) and pd.isna(v)):
                v = None
            r[k] = v
        out.append(r)
    return out


T = {}  # tables: id -> {cols, rows, key, inputs, totals, computed}

# ------------------------------------------------------------------ H1 rework without NC
def kind(t):
    t = t.lower()
    if re.search(r"gestion nc|alerte qualit|ad-hoc|accompagnement", t): return "Quality team time (see H2)"
    if re.search(r"fagot|débiter du", t): return "Cable cutting for stock (see H4)"
    if re.search(r"formboard", t): return "Formboard check after a definition change"
    if re.search(r"nc cable|suite à|suite a", t): return "Cable remake that refers to an NC without its number"
    if re.search(r"impri|câble|cable|débit|plaquette|étiquette", t): return "Cable or label remake, no NC reference"
    if re.search(r"test|continuit|emi|sonn|remise en conformit", t): return "Rework after test, no NC written"
    return "Other rework"
h1 = fam[(fam.family == "FTO2 shop floor") & ~fam.traced].copy(); h1["cat"] = h1.t.map(kind)
h1 = h1.sort_values(["cat", "h"], ascending=[True, False])
T["H1"] = dict(key="order", cols=[["order", "Rework order"], ["prog", "Prog."], ["msn", "MSN"], ["wc", "Work centre(s)"], ["h", "Planned h", "n1"],
                                  ["group", "Group (my reading)"], ["dis", "Named in aléa"], ["text", "What the order says", "long"]],
               rows=rows(pd.DataFrame({"order": h1.index, "prog": h1.prog, "msn": h1.msn, "wc": h1.wcd.map(lambda s: one(s, 120)), "h": h1.h,
                                       "group": h1.cat, "dis": h1.in_disruption.fillna(""), "text": h1.t.map(lambda s: one(s, 350))})),
               inputs=[["nq", "Non-quality?", "yn"], ["ncneeded", "NC should exist?", "yn"], ["comment", "Comment", "text"]],
               totals=[["sum", "h", "Planned h"], ["sumif", "h", "Marked non-quality, h", "nq", "Y"], ["sumif", "h", "NC should exist, h", "ncneeded", "Y"]])

# ------------------------------------------------------------------ H2 quality team time
q2 = wo[wo.order_number.isin(["1031243823", "1031225552"])].sort_values(["order_number", "operation_number"])
T["H2"] = dict(key="id", cols=[["order", "Order"], ["pm", "Prog. / MSN"], ["wc", "Work centre"], ["op", "Op"], ["opt", "Operation"], ["lt", "Long text", "long"], ["h", "Planned h", "n1"]],
               rows=rows(pd.DataFrame({"id": q2.order_number + "-" + q2.operation_number, "order": q2.order_number, "pm": q2.order_program + " / " + q2.order_msn.astype(str),
                                       "wc": q2.work_center, "op": q2.operation_number, "opt": q2.operation_short_text, "lt": q2.operation_long_text.map(lambda s: one(s, 120)), "h": q2.h})),
               inputs=[["ncrel", "NC-related?", "yn"], ["steps", "Already in model steps? (writing / support / none)", "text"], ["comment", "Comment", "text"]],
               totals=[["sum", "h", "Planned h"], ["sumif", "h", "NC-related, h", "ncrel", "Y"]])

# ------------------------------------------------------------------ H3 customer returns
cr = R["cr"].copy().join(n26.set_index("notification_number")[["creation_time", "msn", "description_short"]], how="left").sort_values("creation_time")
T["H3"] = dict(key="nc", cols=[["nc", "NC"], ["created", "Created"], ["plant", "Raised at"], ["prog", "Prog."], ["msn", "MSN"], ["found", "What was found", "long"],
                               ["dec", "Decision"], ["lines", "Defect lines"], ["model", "Model cost now (EUR)", "eur"], ["rework", "of which rework at FTO2 times (EUR)", "eur"],
                               ["orders", "Rework order(s) linked"], ["ph", "Planned h on that order (Sept)", "n1"]],
               rows=rows(pd.DataFrame({"nc": cr.index, "created": cr.creation_time.astype(str).str[:10], "plant": cr.plant, "prog": cr.programme,
                                       "msn": cr.msn.astype(str).str.replace(".0", "", regex=False), "found": cr.description_short.map(one), "dec": cr.cnq_rule,
                                       "lines": cr.cnq_defect_lines, "model": cr.cnq_cost_total, "rework": cr.cnq_cost_work, "orders": cr.rework_orders, "ph": cr.planned_h})),
               inputs=[["rep", "Repair hours at the customer", "num"], ["ana", "Analysis / 8D hours", "num"], ["trans", "Transport, kit, logistics (EUR)", "num"],
                       ["oth", "Penalties, other (EUR)", "num"], ["src", "Source", "text"]],
               computed=[["cwf", "Cost with findings (EUR)", "h3cost"]],
               totals=[["sum", "model", "Model cost now, EUR"], ["sumc", "cwf", "Cost with findings, EUR"]])

# ------------------------------------------------------------------ H4 cable cutting
t = (wo.operation_short_text.fillna("") + " " + wo.operation_long_text.fillna("")).str.replace(r"\s+", " ", regex=True)
cut = wo[t.str.contains(r"fagot|débiter du|Débiter câbles BF|Débiter câble BF", case=False) & (wo.order_type == "S03")].copy(); cut["txt"] = t[cut.index]
oc = cut.groupby("order_number").agg(h=("h", "sum"), msn=("order_msn", "first"), day=("actual_start_execution_date", lambda x: str(min(x))[:10]), txt=("txt", " | ".join)).sort_values("day")
T["H4"] = dict(key="order", caption="Cutting orders (A330 print room, work centre 4FEM0E14)",
               cols=[["order", "Order"], ["day", "Confirmed"], ["msn", "MSN"], ["h", "Planned h", "n1"], ["req", "Request", "long"]],
               rows=rows(pd.DataFrame({"order": oc.index, "day": oc.day, "msn": oc.msn, "h": oc.h, "req": oc.txt.map(lambda s: one(s, 220))})),
               inputs=[["comment", "Comment", "text"]], totals=[["sum", "h", "Planned h"]])
bf = ds[ds.comment.fillna("").str.contains(r"BF ?2[04]", case=False)].sort_values("ot")
T["H4d"] = dict(key="id", caption="Related aléas (mention BF24 / BF20)", cols=[["id", "Aléa"], ["day", "Opened"], ["line", "Line"], ["tl", "Time lost (min)", "n0"], ["kind", "Kind"], ["c", "What the operator wrote", "long"]],
                rows=rows(pd.DataFrame({"id": bf.disruption_id, "day": paris(bf.ot).dt.strftime("%Y-%m-%d"), "line": bf.line, "tl": bf.tl, "kind": bf.type_desc, "c": bf.comment.map(lambda s: one(s, 300))})))
bn = n26[n26.description_long_text.fillna("").str.contains(r"BF ?2[04]")].sort_values("creation_time")
T["H4n"] = dict(key="nc", caption="Related NCs (2026 NCs mentioning BF24 / BF20)", cols=[["nc", "NC"], ["day", "Created"], ["prog", "Prog."], ["type", "NC type"], ["found", "What was found"], ["lt", "Long text (extract)", "long"]],
                rows=rows(pd.DataFrame({"nc": bn.notification_number, "day": bn.creation_time.astype(str).str[:10], "prog": bn.programme, "type": bn.Type_NC_auto, "found": bn.description_short.map(one),
                                        "lt": bn.description_long_text.map(lambda s: one(s[max(0, s.find("BF") - 120):], 250))})))

# ------------------------------------------------------------------ H5 reworked NCs with no rework order
parts = []
for yr, n in [("2026", n26), ("2025", n25)]:
    z = n[(n.cnq_rule == "RWK") & (n.cnq_on_aec == 1) & (n.plant == "FTO2") & ~n.has_rw & (pd.to_datetime(n.creation_time, utc=True, errors="coerce").dt.year == int(yr))]
    parts.append(pd.DataFrame({"nc": z.notification_number.astype(str), "year": yr, "created": z.creation_time.astype(str).str[:10], "type": z.Type_NC_auto, "wf": z.workflow_list,
                               "station": z.station, "who": z.user_department, "found": z.description_short.map(one), "links": z.linked_document.fillna(""),
                               "own": z.work_order.astype(str).str.replace(".0", "", regex=False)}))
T["H5"] = dict(key="nc", cols=[["nc", "NC"], ["year", "Year"], ["created", "Created"], ["type", "NC type"], ["wf", "Workflow"], ["station", "Station"], ["who", "Written by"],
                               ["found", "What was found", "long"], ["links", "linked_document"], ["own", "Own work order"]],
               rows=rows(pd.concat(parts, ignore_index=True)),
               inputs=[["spot", "Fixed on the spot?", "yn"], ["unlinked", "Order exists, not linked?", "yn"], ["comment", "Comment", "text"]],
               totals=[["count", "nc", "NCs"], ["countif", "nc", "Fixed on the spot", "spot", "Y"], ["countif", "nc", "Order not linked", "unlinked", "Y"]])

# ------------------------------------------------------------------ H6 rework orders with no planned time
z = R["noplan"].copy(); z["nc"] = z.nc_link_2026.fillna("")
z = z.join(n26.set_index("notification_number")[["Type_NC_auto", "description_short"]], on="nc").sort_values(["family", "traced"], ascending=[True, False])
T["H6"] = dict(key="order", cols=[["order", "Rework order"], ["fam", "Family"], ["prog", "Prog."], ["msn", "MSN"], ["nc", "Linked NC"], ["type", "NC type"], ["found", "NC: what was found"],
                                  ["wc", "Work centre(s)"], ["ops", "Operations", "long"]],
               rows=rows(pd.DataFrame({"order": z.index, "fam": z.family, "prog": z.prog, "msn": z.msn, "nc": z.nc, "type": z.Type_NC_auto.fillna(""),
                                       "found": z.description_short.map(one).fillna(""), "wc": z.wcd.map(lambda s: one(s, 100)), "ops": z.t.map(lambda s: one(s, 250))})),
               inputs=[["why", "Why no time? (your finding)", "text"], ["comment", "Comment", "text"]], totals=[["count", "order", "Orders"]])

# ------------------------------------------------------------------ H7 disruption export
o = pd.to_datetime(raw.open_date_time)
T["H7f"] = dict(key="k", caption="What we know", cols=[["k", "Fact"], ["v", "Value"]], rows=[
    {"k": "Rows in the file", "v": str(len(raw))}, {"k": "First aléa", "v": str(o.min())}, {"k": "Last aléa", "v": str(o.max())},
    {"k": "File order", "v": "newest first (30 Sep 23:31 on the first row)"}, {"k": "NCs created 29 Dec 2025 - 2 Jan 2026", "v": "0 (plant closed?)"},
    {"k": "First NC of 2026", "v": "5 Jan 2026, same day as the first aléa"}, {"k": "Usual time of the first aléa of a day", "v": "about 07:43"},
    {"k": "First aléa on 5 Jan", "v": "08:57 (9 aléas that day; a usual Monday has about 14)"},
    {"k": "Time columns", "v": "time_lost is typed by the operator (minutes). time_to_get_ack / fix do not match the timestamps (1-2 h time-zone shift; fix = 0 for 64%)."}])
T["H7c"] = dict(key="k", caption="Checks (any one is enough)", cols=[["k", "Check"]], rows=[
    {"k": "1. Re-export Jan-Mar 2026 only: does 5 January get more than 9 aléas, or aléas before 08:57?"},
    {"k": "2. Look for a row limit or a 'first N rows' setting in the export tool (Skywise / Contour)."},
    {"k": "3. Count the aléas in MES for 5 January 2026 and compare with 9."}],
    inputs=[["res", "Result", "text"], ["ok", "Export complete?", "yn"]])
dd = o.dt.date.value_counts().sort_index().head(10)
T["H7d"] = dict(key="d", caption="Aléas per day, first two weeks of the file", cols=[["d", "Day"], ["n", "Aléas", "n0"]], rows=[{"d": str(k), "n": int(v)} for k, v in dd.items()])

# ------------------------------------------------------------------ D disruption block (option B)
qb = R["blockB"].sort_values("ot").copy()
T["D"] = dict(key="id", cols=[["id", "Aléa"], ["day", "Opened"], ["month", "Month"], ["line", "Line"], ["station", "Station"], ["wo", "Work order"], ["tl", "Time lost (min)", "n0"],
                              ["c", "What the operator wrote", "long"], ["ans", "Answer"], ["erma", "Possible ERMA"]],
              rows=rows(pd.DataFrame({"id": qb.disruption_id, "day": paris(qb.ot).dt.strftime("%Y-%m-%d %H:%M"), "month": paris(qb.ot).dt.strftime("%Y%m").astype(int),
                                      "line": qb.line, "station": qb.physical_station, "wo": qb.work_order.fillna(""), "tl": qb.tl, "c": qb.comment.map(one),
                                      "ans": qb.solution.fillna("").str.replace("solve$$", "", regex=False).map(lambda s: one(s, 200)),
                                      "erma": np.where(qb.wf201_like, "possible ERMA NC (MIP / 1101VB)", "")})),
              inputs=[["keep", "Keep in block?", "yn", {"field": "erma", "nonempty": "N", "empty": "Y"}], ["comment", "Comment", "text"]],
              totals=[["sumif_ne", "tl", "Kept, minutes", "keep", "N"], ["countif_ne", "id", "Kept, aléas", "keep", "N"]])

# ------------------------------------------------------------------ M1 quality-like aléas of other kinds
g3 = R["m1"].sort_values(["category", "ot"]).copy()
cats = ["Cable damaged, cut too short or duplicated", "Workmanship error on the line (crimping, forgotten, wrong fitting)",
        "Part or component broken, damaged or faulty", "Wrong or non-conforming part or document supplied", "Other wording"]
T["M1g"] = dict(key="g", caption="Answer yes / no per group", cols=[["g", "Group"], ["n", "Aléas", "n0"], ["h", "Hours lost", "n1"], ["ex", "Three examples", "long"]],
                rows=[{"g": c, "n": int((g3.category == c).sum()), "h": round(g3[g3.category == c].tl.sum() / 60, 2),
                       "ex": " | ".join(g3[g3.category == c].comment.map(lambda s: one(s, 110)).head(3))} for c in cats],
                inputs=[["yes", "Count as quality?", "yn"], ["comment", "Comment", "text"]])
T["M1"] = dict(key="id", caption="All 107 aléas, for reference", cols=[["id", "Aléa"], ["day", "Opened"], ["month", "Month"], ["kind", "Kind"], ["line", "Line"],
                                                                      ["tl", "Time lost (min)", "n0"], ["g", "Group"], ["c", "What the operator wrote", "long"]],
               rows=rows(pd.DataFrame({"id": g3.disruption_id, "day": paris(g3.ot).dt.strftime("%Y-%m-%d"), "month": paris(g3.ot).dt.strftime("%Y%m").astype(int),
                                       "kind": g3.type_desc, "line": g3.line, "tl": g3.tl, "g": g3.category, "c": g3.comment.map(one)})))

# ------------------------------------------------------------------ M2, M3
m2 = fam[fam.status == "E. names an NC we DON'T have"].copy().sort_values("h", ascending=False)
T["M2"] = dict(key="order", cols=[["order", "Rework order"], ["fam", "Family"], ["prog", "Prog."], ["msn", "MSN"], ["nc", "NC named"], ["h", "Planned h", "n1"], ["text", "What the order says", "long"]],
               rows=rows(pd.DataFrame({"order": m2.index, "fam": m2.family, "prog": m2.prog, "msn": m2.msn, "nc": m2.nc_in_text.map(", ".join), "h": m2.h, "text": m2.t.map(lambda s: one(s, 250))})),
               inputs=[["plant", "Plant of the NC", "text"], ["liab", "Liability", "text"], ["who", "Written by (ERMA?)", "text"], ["comment", "Comment", "text"]], totals=[["sum", "h", "Planned h"]])
ex = R["exc"].join(n26.set_index("notification_number")[["description_short", "description_long_text"]])
T["M3"] = dict(key="nc", cols=[["nc", "NC"], ["type", "NC type"], ["lines", "Defect lines"], ["ph", "Planned rework (h)", "n1"], ["mh", "Model rework (h)", "n1"], ["found", "What was found"], ["lt", "Long text (extract)", "long"]],
               rows=rows(pd.DataFrame({"nc": ex.index, "type": ex.Type_NC_auto, "lines": ex.cnq_defect_lines, "ph": ex.total / 60, "mh": ex.model_new / 60,
                                       "found": ex.description_short.map(one), "lt": ex.description_long_text.map(lambda s: one(s[150:] if isinstance(s, str) else s, 300))})),
               inputs=[["finding", "Finding", "text"]])

# ------------------------------------------------------------------ checklist items
ITEMS = [
 dict(id="H1", prio="High", title="Rework done without an NC (shop floor)", tables=["H1"],
      know=f"{len(T['H1']['rows'])} rework orders on FTO2 work centres, about 181 planned hours in September, with no NC behind them: quality-team time, cable cutting, rework after test with no NC, cable or label remakes with no NC reference, formboard checks.",
      q="Which are non-quality? Which should have had an NC?", where="Rework order texts in SAP; line leaders; quality."),
 dict(id="H2", prio="High", title="Quality team time booked on rework orders", tables=["H2"],
      know="2 orders, 70.5 h in September (A350 and A330 lines), incl. 15 h 'Gestion NC retours clients + analyse' and 4 h 'Alerte qualité'.",
      q="Is there one per line every month? Which hours are NC handling (CNQ) and which are normal quality work? Overlap with the model's 'writing the NC' or 'technical support' steps?",
      where="Quality line managers (work centres 4QEH5I07, 4QEH1I07); SAP orders."),
 dict(id="H3", prio="High", title="Customer returns: the actual cost, work at the customer included", tables=["H3"],
      know="69 returns in 2026, 12,577 EUR in the model (every step, customer's alert included, rework at FTO2's times). FNZ1 returns get an FTO2 order that only checks the kit sent to Montoir-de-Bretagne; two FFF1 returns are linked to REC orders at the FAL. The quality team's A350 order booked 15 h of customer-return management for 8 returns in September.",
      q="Repair hours actually spent at the customer, analysis hours, transport / kits, penalties. Type them in; 'Cost with findings' replaces the model's rework by the real repair hours.",
      where="Quality (customer returns); TOF / FNZ1 / FFF1 contacts; REC."),
 dict(id="H4", prio="High", title="BF24 / BF20 cable cutting for stock", tables=["H4", "H4d", "H4n"],
      know="37 orders, 78 h, 2,600 cables cut in September for the PTVU line, after aléas about BF24 quantities in Elec ABC and missing BF24 cables.",
      q="A consequence of non-quality (cables remade because of defects), or a definition / kitting problem?", where="Methods (Elec ABC), A330 print room, PTVU line leader."),
 dict(id="H5", prio="High", title="Reworked NCs with no rework order", tables=["H5"],
      know=f"{len(T['H5']['rows'])} NCs (2026 and 2025) decided 'rework' with nothing in linked_document. 96-97% of reworked NCs do have their own rework order.",
      q="Fixed on the spot, or an order that exists but was never linked to the NC?", where="SAP: orders on the same work order / MSN."),
 dict(id="H6", prio="High", title="Rework orders with no planned time", tables=["H6"],
      know=f"{len(T['H6']['rows'])} of 614 rework orders in September have no standard value (63 of 249 on the shop floor). Until known, the model's estimate is used for their NCs.",
      q="Why no time (created without times, closed without confirmation, time booked elsewhere)? How should those NCs be costed?", where="Methods / technical support who create the orders."),
 dict(id="H7", prio="High", title="Is the disruption export complete?", tables=["H7f", "H7c", "H7d"],
      know="Exactly 2,500 rows, newest first, 5 Jan 08:57 to 30 Sep 23:31: the pattern of an export cut at a row limit. But it starts on the plant's restart day, so it is probably complete.",
      q="Re-export January-March and compare 5 January; look for a row limit.", where="Skywise / Contour export; MES."),
 dict(id="M1", prio="Medium", title="Other aléas that look like quality", tables=["M1g", "M1"],
      know="107 logistics / work-order / line aléas, no NC after them, whose text reads like a quality problem. Grouped in 5 so you can answer per group.",
      q="Yes or no per group. Groups marked yes are added to the disruption block.", where="This page."),
 dict(id="M4", prio="Medium", title="ERMA aléas in the disruption block", tables=["D"], filter="possible ERMA",
      know="19 of the 108 quality aléas with no NC are on the MIP / 1101VB, where ERMA writes NCs. As decided, they are left out of the block (Keep = N) until checked.",
      q="Does each have an ERMA NC? If not, set Keep = Y so it counts.", where="Skywise NCs on the same work order."),
 dict(id="M2", prio="Medium", title="Rework orders naming NCs we do not have", tables=["M2"],
      know=f"{len(T['M2']['rows'])} orders, about 27 h, name 2026 NCs that are in neither of our NC exports.",
      q="Plant, liability and writer of those NCs: out of scope (ERMA, other plants), or missing from our export?", where="Skywise NC lookup."),
 dict(id="M3", prio="Medium", title="Exceptional NCs (not for the presentation)", tables=["M3"],
      know="4 NCs where the order plans far more than the model, e.g. NC 218233692 'Câbles non lasérisés': one defect line, 34 h of reprinting cables for six routes.",
      q="Is the planned time right? Should such NCs be costed from their order?", where="You."),
 dict(id="D", prio="Info", title="Disruption block (option B): the list behind the figure", tables=["D"],
      know="Quality aléas with no NC on the same work order within 72 h, Jan-Sep 2026. Aléas that led to an NC are inside the NC cost (alert step), not here.",
      q="Nothing to do unless an aléa should not count: set Keep = N.", where="This page."),
 dict(id="L2", prio="Low", title="Internal NCs with no aléa logged in MES (later, not tomorrow)", tables=[],
      know="Only 10 of 61 internal NCs (Jul-Sep 2026) have a quality aléa logged in MES before them. Assumption (Mohammad, 19 Oct): an internal NC always starts with an aléa, even when it is not logged. The model already charges the 41-min alert on every internal NC.",
      q="Why are most aléas of internal NCs not logged in MES? Confirm the assumption.", where="Line leaders; MES."),
 dict(id="L1", prio="Low", title="MSN 700/701 work (IEVB work centres)", tables=[],
      know="74 rework orders, 217 h in September on MSN 700/701 (e.g. 'Repose FTI sur bouteille oxy'), most likely flight-test installation.",
      q="Confirm it is flight-test work and out of scope.", where="Flight-test / IEV team."),
]

# ------------------------------------------------------------------ changes (also written to CNQ_CHANGES.md)
CHANGES = [
 ("Applied to the CNQ model (version cnq-2026.10.20b)", [
  ("Operator alert only when an operator raises one: not for NCs found at test or at final inspection", "0 of 52 test NCs and 4 of 23 final-inspection NCs started with an aléa (Jul-Sep 2026)", "NO_ALERT_TYPES"),
  ("Customer returns always get the alert, whatever their NC type", "The customer's operator raises it; AEC is the direct cause", "cnq_core.compute_cnq"),
  ("Alert time 41 min instead of 30", "Mean time lost declared on the 214 quality aléas that led to an NC (median 30)", "MIN_ALERT"),
  ("Connection errors: 35 min for the first in an NC, 15 min for each following one", "Rework orders of test NCs plan about 77 min + 15 min per error (11 NCs, Sept 2026)", "CONNECTION_CLASSES, MIN_CONNECTION_NEXT"),
  ("Internal NCs: rework (setup + hands-on) x 2", "Planned 1,896 min against 951 in the model on 11 complete orders; per-NC median ratio 2.0", "INTERNAL_TYPES, INTERNAL_WORK_FACTOR"),
  ("Exchange: no rework, swapped part counted", "0 of 20 exchanges in 2026 had a rework order", "RULES['EXC']"),
  ("Rejection with a rework order: rework charged (rule REJ_RW)", "About half of rejections get a rework order (median 1 h 40 planned)", "REWORK_ORDER_PREFIXES, RULES['REJ_RW']"),
  ("Rework orders: the planned time of the NC's closed rework order replaces the model's setup and hands-on (no connection rule, no x 2)", "Catches exceptional NCs (34 h on NC 218233692). 71 NCs have a closed, planned order in the Sept 2026 operations; AEC level 3 175,663 -> 177,436 EUR. Orders still open or without planned time keep the model", "USE_ORDER_TIME, cnq_orders.nc_order_times"),
  ("Alert step: the declared time of the quality aléa that led to the NC replaces the flat 41 min, also on NCs found at test or final inspection when an aléa was raised", "Aléa linked to the NC: same work order, NC created from 2 h before to 72 h after. 175 NCs; a declared 0 means not filled and keeps 41 min. AEC level 3 177,436 -> 178,847 EUR", "USE_ALEA_TIME, cnq_disruptions.nc_alea_times"),
  ("Rates per step (cnq-2026.10.20b): production 123 EUR/h for the alert, setup, hands-on work and aléa time; quality 107 EUR/h for writing, re-check and closing; ME 76 EUR/h for technical support. Engineering stays at the Airbus 78.16 EUR/h", "Given by the team on 20 Oct 2026; before, every step was at 50 EUR/h. AEC level 3 on the dashboard data 178,847 -> 376,511 EUR (856 AEC NCs); 2025 série 366,582 EUR", "RATES, STEP_WHO"),
 ]),
 ("Decided, outside the model", [
  ("Two calculations: the NC cost of non-quality, and a disruption block shown beside it, never added inside it", "The aléa that leads to an NC is inside the NC cost (alert step)", "-"),
  ("Disruption block = quality aléas that did not lead to an NC (option B), plus other-kind aléas whose group you mark as quality (M1)", "Jan-Sep 2026: 89 aléas, 66.9 h, about 3,350 EUR (possible ERMA aléas left out). On the dashboard's Coût tab since 20 Oct; the M1 groups are not added until answered", "-"),
  ("Possible ERMA aléas (MIP / 1101VB) left out of the disruption block until checked", "19 aléas, 24.3 h", "-"),
  ("Scope: REC and ERMA are not included", "REC: 746 h of rework orders in Sept 2026. ERMA: 184 NCs in 2025, 46,158 EUR (new model)", "-"),
  ("Customer returns: count every cost we can find, including work done at the customer (AEC is the direct cause)", "Figures to collect in check H3", "-"),
  ("Year comparisons without ERMA", "The 2026 pipeline excludes ERMA", "-"),
  ("Year comparisons and targets: 2025 from the 2025 Skywise extract through the pipeline's rules (ERMA out); target = 2025 - 25 %, cost budget = 2025 cost - 25 %", "2025, série raised at FTO2: 732 NCs, 170,433 EUR. Per line: NCs per product delivered (Livraisons 2025 sheet, 343 products)", "-"),
  ("Internal NCs always have an aléa, even when none is logged in MES: the alert step is charged on every internal NC", "Assumption (Mohammad, 19 Oct). Only 10 of 61 internal NCs (Jul-Sep 2026) have a logged aléa. Already how the model works; to investigate later (check L2)", "-"),
 ]),
 ("Kept for later (not applied)", [
  ("Change 5: two defect classes missing from the time table", "'Mesure hors tolérance' -> 5 min like 'Point de masse / mesure'; 'Dommage – tresse de masse' -> 30 min like 'Dommage – câble'. About 25 lines a year, almost 0 EUR", "DEFECT_TIMES"),
  ("Customer returns: add the real costs (repair at the customer, analysis, transport, penalties)", "After check H3: per return in the customer_return_cost column, or a flat CUSTOMER_RETURN_EXTRA", "CUSTOMER_RETURN_EXTRA / customer_return_cost"),
  ("Responders' time on aléas (quality, support, logistics answering)", "Not in 'time lost'; a flat time per aléa could be added to the disruption block", "to decide"),
  ("Re-check the WO rules on a full year of rework orders", "15 min per extra connection error, x2 on internal NCs, exchange, rejection: from one month (Sept 2026)", "WO parameters"),
  ("Decide from checks H1, H2, H4, H6", "Rework without an NC, quality team time, cable cutting, orders with no planned time", "to decide"),
 ]),
 ("For the pipeline team (data needed)", [
  ("NC dataset columns", "decision_status, liability, type_nc, produit (README section 7), plus linked_document and work_order (rework order of the NC)", "-"),
  ("Keep NCs with no defect line in the NC dataset", "They still cost handling time", "-"),
  ("Rework orders (S03) with their operations and planned times", "Linked to NCs through linked_document", "-"),
  ("Aléa-NC link and a disruption-block dataset", "Same work order, NC created between 2 h before and 72 h after the aléa; quality aléas with no NC", "-"),
  ("Disruption export without a row limit", "Check H7", "-"),
 ]),
]

# ------------------------------------------------------------------ figures
nc_fig = [["2026 Feb-Sep, raised at FTO2 (695 NCs)", 149824], ["2025, raised at FTO2, without ERMA (818 NCs)", 178870], ["CNQ pack reference data, 5 Jan - 6 Jul 2026 (595 NCs)", 128741]]
DATA = dict(meta=dict(built=datetime.date.today().isoformat(), rate=RATE, model="cnq-2026.10.20b"), items=ITEMS, tables=T, changes=CHANGES,
            figures=dict(nc=nc_fig, cr_model=round(float(R["cr"].cnq_cost_total.sum())), rec_h=746, erma=46158))

js = json.dumps(DATA, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = open(REPO + "/07_scripts/wo_disruption/checklist_template.html", encoding="utf-8").read().replace("/*__DATA__*/null", js)
open(REPO + "/05_outputs/CNQ_investigation_checklist.html", "w", encoding="utf-8").write(html)

md = ["# CNQ changes: done, decided and to do", "",
      f"Updated {DATA['meta']['built']}. Generated by `07_scripts/wo_disruption/build_checklist_html.py` (the same list appears in "
      "`05_outputs/CNQ_investigation_checklist.html`, button 'Changes'). Details of each model change and its evidence: "
      "`cnq_handoever/README_handover.md`, section 4.", "",
      "Effect of the applied changes on level 3: 134,206 -> 128,741 EUR on the CNQ pack data; 151,093 -> 149,824 EUR on 2026 Feb-Sep; "
      "178,170 -> 178,870 EUR on 2025 without ERMA; customer returns 2026: 11,975 -> 12,577 EUR. The totals move little; the cost moves "
      "between NC types (test NCs down, internal NCs and rejections with a rework order up). Version cnq-2026.10.20 (planned time of the rework order, then the declared aléa time): AEC level 3 on the dashboard data 175,663 -> 177,436 -> 178,847 EUR. Version cnq-2026.10.20b (rates per role, production 123, quality 107, ME 76 EUR/h instead of 50 for all): 178,847 -> 376,511 EUR.", ""]
for sec, lst in CHANGES:
    md += [f"## {sec}", "", "| Change | Why / detail | Where |", "|---|---|---|"]
    md += [f"| {a} | {b} | `{c}` |" if c not in ("-", "to decide", "pipeline") else f"| {a} | {b} | {c} |" for a, b, c in lst]
    md += [""]
md += ["## Open checks", "", "One line per check in `05_outputs/CNQ_investigation_checklist.html`:", ""]
md += [f"- **{it['id']} ({it['prio']})** {it['title']}: {it['q']}" for it in ITEMS]
open(REPO + "/CNQ_CHANGES.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("written: checklist html (%d kB), CNQ_CHANGES.md" % (len(html.encode("utf-8")) // 1024))
