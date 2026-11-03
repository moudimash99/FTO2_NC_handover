"""Batches of the defect lines without a usable AI label (new since 12 Oct), in the 12 Oct format (07_scripts/llm_longtext/prep.py)."""
import sys, json, re, os
R = "/home/user/FTO2_NC_handover/"
for p in ("build", "01_parser", "02_dashboard_pack/skywise_nc_dashboard_v48/1_pipeline", "cnq_handoever"): sys.path.insert(0, R + p)
import build_all as B, fto2_core as core, pandas as pd
S = os.path.dirname(os.path.abspath(__file__)) + "/"
x = B.load_exports()
lab = pd.read_csv(R + "04_reference/llm_labels_longtext.csv", dtype={"notification_number": str}, encoding="utf-8-sig")
p = core.prepare(x.copy(), lab, R + "04_reference", B.load_orders(), B.load_disruptions())
d = p["d"]; t = d[~d.llm_status.isin(["ok", "titre"])].copy()
print("lines to label:", len(t), t.llm_status.value_counts().to_dict(), "NCs:", t.notification_number.nunique())
xi = x.set_index("notification_number")
s = lambda v: "" if pd.isna(v) else str(v)
ncs = []
for nc, g in t.groupby("notification_number", sort=False):
    r = xi.loc[nc]
    ncs.append({"notification_number": nc, "programme": s(r.programme), "perimetre": "",
                "station": (s(r.station) + " " + s(r.get("station_description", ""))).strip(), "user_department": s(r.user_department),
                "description_short": s(r.description_short),
                "sap_defect_code": (s(r.defect_code) + " " + s(r.defect_code_description_en)).strip(),
                "sap_cause": (s(r.cause_code_description_en) + " " + s(r.cause_description)).strip(),
                "long_text": core.clean_long_text(r.description_long_text),
                "defects": [{"seq": int(z.seq), "written_code": s(z.code), "fin": s(z.fin), "snippet": s(z.text)} for z in g.sort_values("seq").itertuples()]})
batches, cur, n = [], [], 0
for c in ncs:
    if n + len(c["defects"]) > 100 and cur: batches.append(cur); cur, n = [], 0
    cur.append(c); n += len(c["defects"])
if cur: batches.append(cur)
for i, b in enumerate(batches, 1): json.dump(b, open(S + "batches/n%02d.json" % i, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
t[["notification_number", "seq", "text"]].to_csv(S + "to_label.csv", index=False)
print(len(batches), "batches:", [sum(len(c["defects"]) for c in b) for b in batches])
