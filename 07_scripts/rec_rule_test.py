import os
import re
import numpy as np
import pandas as pd
from foundry.transforms import Dataset, Column
# ==========================================
# REC RULE TEST — run in the pipeline notebook environment
# ==========================================
# Tests the "REC written" rule (writer department) on the Skywise non_conformity dataset.
# Run it where the pipeline notebook runs (same "non_conformity" dataset): paste it in a cell,
# or upload it next to the notebook and run `%run rec_rule_test.py`. Read-only: it writes nothing to Skywise.
# Each test prints PASS or REVIEW; rows to read are saved as CSV in OUT_DIR.
#   TEST 1  every NC in the REC tracker is tagged (recall)
#   TEST 2  every NC tagged at a FAL plant is REC (precision; the part the exports could not show)
#   TEST 3  REC-looking NCs the rule leaves out (REC inspector IDs, writers whose department moved)
#   TEST 4  hits of the old rules (42RC, RECX/SUBR, workflow regex) against the new one, all plants
#   TEST 5  what changes for the pipeline tag and scope
# Expected values come from the exports analysed on 20 Oct (07_scripts/rec_dept_rule.py).

# %% Configuration
START = "2026-01-01 00:00:00"   # same window as the pipeline
OUT_DIR = "rec_test_output"
CHUNK = 1000                     # NC numbers per isin() query

REC_DEPTS = [
    "QRT/DERICHEBOURG AERONAUTICS",
    "QR/DERICHEBOURG AERONAUTICS",
    "OSOOM/DERICHEBOURG AERONAUTICS",
    "QLOT/DERICHEBOURG AERONAUTICS",
    "QLOT1/AIRBUS OPERATIONS SAS",
]
REC_WORKFLOW = r"^(REC-|A30-REJ-PVU|RJ-PVU-REC)"

# Cross-checks only (the rule does not use them)
REC_INSPECTOR_IDS = ["ST32873", "GALIZ81C", "RGAGTM5M", "PMAR3D30", "CLOP5B4I", "TO74350"]
REC_HEADER_ORGS = [                       # writer org as printed in the long text when the NC was written
    "QRT/DERICHEBOURG AERONAUTICS", "QR/DERICHEBOURG AERONAUTICS", "OSOOM/DERICHEBOURG AERONAUTICS",
    "QLOT/DERICHEBOURG AERONAUTICS", "QLOT1/AIRBUS OPERATIONS SAS", "QRTE/AIRBUS OPERATIONS SAS",
    "QRT3E/AIRBUS OPERATIONS SAS", "Q1AF/DERICHEBOURG AERONAUTICS",
]
KNOWN_WRITERS = {                         # writers seen in the exports who are in REC_DEPTS but are not REC
    "MBOUKHY2": "IEVB inspector (MSN 700/701)", "MELMVYRS": "IEVB inspector (MSN 700/701)",
    "CBOB0N1L": "IEVB inspector (MSN 700/701)", "SSEL1BWL": "FTO2 VU final rework",
    "ST10074": "FTO2 fibre optic lab", "TO41873": "FTO2 quality, A330 VU follow-up NCs",
}

# REC tracker "NC rédigées par le REC" (2181014667 read as 218014667).
# 217022710 is in the tracker but marked "non rédigé par le REC": it must NOT be tagged.
TRACKER_NCS = [
    "214170318", "214564707", "214786689", "214978389", "215063111", "215135599", "215304556", "215368287",
    "215411180", "215504841", "215544683", "215745861", "215923423", "215926734", "215980783", "215991735",
    "216004781", "216048141", "216147860", "216349144", "216417082", "216527310", "216564030", "216564948",
    "216570787", "216611489", "216626702", "216798107", "216823015", "216824737", "216872196", "216876758",
    "216913564", "216926613", "216926615", "217007060", "217009247", "217052678", "217054332", "217064401",
    "217093143", "217106860", "217109218", "217121364", "217149828", "217188644", "217198810", "217215302",
    "217229379", "217249319", "217253630", "217277051", "217309600", "217317328", "217317430", "217323840",
    "217336377", "217344224", "217350659", "217350724", "217364858", "217394622", "217413173", "217417593",
    "217473619", "217500008", "217524481", "217553764", "217612037", "217624045", "217656737", "217680626",
    "217700674", "217741493", "217744586", "217744832", "217752265", "217793017", "217812865", "217814121",
    "217883427", "217894119", "217906457", "217939264", "217947196", "217947313", "217952767", "217964165",
    "217977988", "217978073", "217990195", "217998304", "218014667", "218017224", "218017308", "218017365",
    "218023660", "218023731", "218023739", "218027807", "218028102", "218028105", "218134915", "218161939",
    "218162668", "218169931", "218289923", "218296736", "218318519", "218346399", "218346599", "218401324",
    "218414585", "218420973", "218456889",
]
TRACKER_NOT_REC = ["217022710"]

LIGHT_COLS = [
    "notification_no_leading_zeros", "plant", "station", "work_ctr", "workflow_list", "user_department",
    "liability", "status_open_closed", "decision_status", "creation_time", "programme", "msn",
    "description_short",
]
TEXT_COLS = ["notification_no_leading_zeros", "description_long_text"]
os.makedirs(OUT_DIR, exist_ok=True)
results = []


# %% The rule
def rec_written(df):
    """True when the NC was written by REC: writer department in REC_DEPTS and either raised
    outside plant FTO2, or inside FTO2 on a REC workflow (IEVB work centres excluded)."""
    dept = df["user_department"].isin(REC_DEPTS)
    wf = df["workflow_list"].str.match(REC_WORKFLOW)
    ievb = df["work_ctr"].str.startswith("IEVB")
    return dept & ((df["plant"] != "FTO2") | (wf & ~ievb))


# %% Helpers
def fetch(condition, cols):
    return (Dataset.get("non_conformity")
            .where(condition)
            .select(*cols)
            .read_table(format="pandas"))


def fetch_ids(ids, cols):
    ids = sorted({str(i) for i in ids})
    parts = [fetch(Column.get("notification_no_leading_zeros").isin(ids[i:i + CHUNK]), cols)
             for i in range(0, len(ids), CHUNK)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=cols)


def as_text(v):
    if isinstance(v, (list, tuple, np.ndarray)):
        return ",".join(str(x) for x in v)
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v)


def prep(df):
    df = df.copy()
    for c in df.columns:
        df[c] = df[c].map(as_text).str.strip()
    if "creation_time" in df:
        df["created"] = pd.to_datetime(df["creation_time"].str[:19].str.replace("T", " "), errors="coerce")
    if "status_open_closed" in df:
        df["deleted"] = df["status_open_closed"].str.contains("deleted", case=False)
    return df.drop_duplicates("notification_no_leading_zeros").reset_index(drop=True)


HEADER = re.compile(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\(\s*(\S+)\s+([^)]*?)\s*\)")


def creation_line(text):
    """The header that opens the long text = who wrote the NC. When the text opens with the
    'Moment of Detection' block there is no creation line and the first header is a later comment."""
    m = HEADER.search(text)
    if not m or m.start() > 150 or "Moment of Detection" in text[:m.start()]:
        return None
    return m


def add_writer(df):
    """Writer ID and org from the creation line of the long text ('' when there is none; masked IDs show as #UID~)."""
    if df.empty:
        return df.assign(writer_id="", writer_org="", text_start="")
    txt = prep(fetch_ids(df["notification_no_leading_zeros"], TEXT_COLS))
    txt = txt.set_index("notification_no_leading_zeros")["description_long_text"]
    t = df["notification_no_leading_zeros"].map(txt).fillna("")
    first = t.map(creation_line)
    return df.assign(writer_id=first.map(lambda m: m.group(1) if m else ""),
                     writer_org=first.map(lambda m: m.group(2) if m else ""),
                     text_start=t.str.replace(r"\s+", " ", regex=True).str[:300])


def verdict(name, ok, detail):
    results.append((name, "PASS" if ok else "REVIEW", detail))
    print(f"\n>>> {name}: {'PASS' if ok else 'REVIEW'} — {detail}")


def save(df, name):
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"    saved {len(df)} rows to {path}")


# %% Fetch: every NC since START, light columns (same split as the pipeline)
fto2_plant_df = fetch((Column.get("plant") == "FTO2") & (Column.get("creation_time") >= START), LIGHT_COLS)
other_plant_df = fetch((Column.get("plant") != "FTO2") & (Column.get("creation_time") >= START), LIGHT_COLS)
nc = prep(pd.concat([fto2_plant_df, other_plant_df], ignore_index=True))
nc["rec_written"] = rec_written(nc)
print(f"NCs since {START}: {len(nc)} (plant FTO2 {len(fto2_plant_df)}, other plants {len(other_plant_df)})")
print(f"Tagged REC written: {nc.rec_written.sum()}")

# %% TEST 1 — recall on the REC tracker (all dates)
print("\n" + "=" * 70 + "\nTEST 1 — REC tracker: every NC REC wrote must be tagged")
trk = prep(fetch_ids(TRACKER_NCS + TRACKER_NOT_REC, LIGHT_COLS))
trk["rec_written"] = rec_written(trk)
trk = add_writer(trk)
is_rec = trk["notification_no_leading_zeros"].isin(TRACKER_NCS)
not_found = sorted(set(TRACKER_NCS) - set(trk["notification_no_leading_zeros"]))
missed = trk[is_rec & ~trk.rec_written]
wrong = trk[~is_rec & trk.rec_written]
ids_hit = (is_rec & trk.writer_id.isin(REC_INSPECTOR_IDS)).sum()
print(f"Found in Skywise: {is_rec.sum()}/{len(TRACKER_NCS)} | caught: {(is_rec & trk.rec_written).sum()}"
      f" | missed: {len(missed)} | 217022710 tagged: {len(wrong)}")
print(f"For comparison, the 6 inspector IDs find {ids_hit}/{is_rec.sum()} (writer masked #UID~ on "
      f"{(is_rec & trk.writer_id.eq('#UID~')).sum()}, no creation line on {(is_rec & trk.writer_id.eq('')).sum()})")
if not_found:
    print("Not found in Skywise:", not_found)
save(pd.concat([missed, wrong]), "test1_tracker_missed.csv")
verdict("TEST 1 tracker recall", len(missed) == 0 and len(wrong) == 0 and not not_found,
        f"{(is_rec & trk.rec_written).sum()}/{len(TRACKER_NCS)} caught (expected 115/115)")

# %% TEST 2 — precision at FAL plants (cannot be checked from the exports)
print("\n" + "=" * 70 + "\nTEST 2 — NCs tagged REC outside plant FTO2: are they all REC?")
fal = nc[nc.rec_written & (nc.plant != "FTO2")].copy()
print(f"Tagged REC outside plant FTO2: {len(fal)} ({fal.deleted.sum()} deleted). "
      f"Exports: at least 84 (11 deleted) since 2026-01-01")
if len(fal):
    print(pd.crosstab(fal.user_department, fal.plant, margins=True).to_string())
    print("\nBy month (a department dropping to 0 can mean a rename):")
    print(pd.crosstab(fal.created.dt.to_period("M"), fal.user_department).to_string())
fal = add_writer(fal)
fal["in_tracker"] = fal["notification_no_leading_zeros"].isin(TRACKER_NCS)
fal["rec_signature"] = fal.station.str.contains("42RC") | fal.workflow_list.str.startswith("REC-")
fal["writer_note"] = fal.writer_id.map(KNOWN_WRITERS).fillna("")
print("\nWriter on the creation line (REC inspector IDs, masked, no creation line, others):")
print(fal.assign(kind=np.where(fal.writer_id.isin(REC_INSPECTOR_IDS), "REC inspector",
                       np.where(fal.writer_id.eq("#UID~"), "masked",
                                np.where(fal.writer_id.eq(""), "no creation line", fal.writer_id))))
      .groupby("kind").size().sort_values(ascending=False).head(25).to_string())
to_read = fal[~fal.in_tracker & (~fal.rec_signature | fal.writer_note.ne("")
                                 | ~fal.writer_id.isin(REC_INSPECTOR_IDS + ["#UID~", ""]))]
cols = ["notification_no_leading_zeros", "created", "plant", "station", "workflow_list", "decision_status",
        "user_department", "writer_id", "writer_org", "writer_note", "description_short", "text_start"]
print(f"\nRows to read (not in tracker, and no 42RC/REC- signature or an unknown/known non-REC writer): "
      f"{len(to_read)}")
print(to_read[cols[:-1]].head(40).to_string())
save(fal[cols + ["in_tracker", "rec_signature"]], "test2_fal_all_tagged.csv")
save(to_read[cols], "test2_fal_rows_to_read.csv")
verdict("TEST 2 FAL-plant precision", len(to_read) == 0,
        f"{len(fal)} tagged, {len(to_read)} rows to read by hand (each non-REC one is a false positive)")

# %% TEST 3 — REC-looking NCs the rule does not tag (all plants)
print("\n" + "=" * 70 + "\nTEST 3 — NCs at REC stations / REC work centres / REC workflows not tagged")
ctx = (nc.station.str.contains("42RC") | nc.work_ctr.str.match(r"^(RECX|SUBR)")
       | nc.workflow_list.str.startswith("REC-"))
untagged = nc[ctx & ~nc.rec_written].copy()
print(f"Untagged NCs in a REC context: {len(untagged)} (expected: written by FAL or FTO2 methods for REC to fix)")
print(untagged.user_department.value_counts().head(25).to_string())
own = untagged[untagged.user_department.isin(REC_DEPTS)]
print(f"\nOf these, written by REC_DEPTS and left out on purpose (plant FTO2 with an FTO2 workflow, or IEVB): "
      f"{len(own)}")
print(own.groupby(["workflow_list", own.work_ctr.str[:4].rename("work_ctr")]).size().to_string())
untagged = add_writer(untagged)
by_inspector = untagged[untagged.writer_id.isin(REC_INSPECTOR_IDS)]
by_rec_org = untagged[untagged.writer_org.isin(REC_HEADER_ORGS) & ~untagged.user_department.isin(REC_DEPTS)]
cols = ["notification_no_leading_zeros", "created", "plant", "station", "work_ctr", "workflow_list",
        "user_department", "writer_id", "writer_org", "description_short", "text_start"]
print(f"\nWritten by a REC inspector ID: {len(by_inspector)} | written under a REC org but department now "
      f"elsewhere (moved or renamed): {len(by_rec_org)}")
print(pd.concat([by_inspector, by_rec_org])[cols[:-1]].drop_duplicates().head(40).to_string())
dept_new = (untagged[untagged.user_department.str.contains("DERICHEBOURG|EXPLEO", case=False)
                     | untagged.user_department.str.match(r"^Q")]
            .groupby("user_department").size().sort_values(ascending=False))
print("\nQuality / subcontractor departments in that list (read a few rows if one looks like REC):")
print(dept_new.head(20).to_string())
save(untagged[cols], "test3_rec_context_untagged.csv")
save(pd.concat([by_inspector, by_rec_org])[cols].drop_duplicates(), "test3_possible_missed.csv")
verdict("TEST 3 missed REC NCs", len(by_inspector) + len(by_rec_org) == 0,
        f"{len(by_inspector)} by REC inspector IDs, {len(by_rec_org)} under a REC org with another department now")

# %% TEST 4 — old rules against the new one, all plants
print("\n" + "=" * 70 + "\nTEST 4 — how general each rule is (all NCs since START)")
rules = {
    "station 42RC": nc.station.str.contains("42RC"),
    "work_ctr RECX/SUBR": nc.work_ctr.str.match(r"^(RECX|SUBR)"),
    "current workflow regex": nc.workflow_list.str.contains(r"\bREC\b|-CRE|-PNC|A30-REJ-PVU2", case=False),
    "writer department (new)": nc.rec_written,
}
rec_dept = nc.user_department.isin(REC_DEPTS)
table = pd.DataFrame([{"rule": k, "hits": int(m.sum()), "written by REC depts": int((m & rec_dept).sum()),
                       "written by others": int((m & ~rec_dept).sum()),
                       "outside plant FTO2": int((m & (nc.plant != "FTO2")).sum())}
                      for k, m in rules.items()])
print(table.to_string(index=False))
save(table, "test4_rule_comparison.csv")
verdict("TEST 4 rule comparison", True, "information only (see table)")

# %% TEST 5 — what changes for the pipeline
print("\n" + "=" * 70 + "\nTEST 5 — changes against the current pipeline tag")
fto2_liable = nc.liability.str.contains(r"\bFTO2\b")
in_scope = (nc.plant == "FTO2") | fto2_liable
current = in_scope & rules["current workflow regex"]
new_scope = nc.rec_written & ~in_scope
follow_up = nc.rec_written & (nc.plant == "FTO2") & nc.workflow_list.str.match(r"^(A30-REJ-PVU|RJ-PVU-REC)")
print(f"Current pipeline scope: {in_scope.sum()} NCs, tagged REC today: {current.sum()}")
print(f"New rule inside that scope: {(in_scope & nc.rec_written).sum()} | REC today, not REC now: "
      f"{(current & ~nc.rec_written).sum()} | REC now, not REC today: {(in_scope & nc.rec_written & ~current).sum()}")
print("REC today, not REC now — by writer department (FAL / methods NCs sent to REC):")
print(nc[current & ~nc.rec_written].user_department.value_counts().head(15).to_string())
print(f"\nREC NCs the pipeline does not fetch today (plant not FTO2 and not FTO2-liable): {new_scope.sum()}")
print(nc[new_scope].plant.value_counts().to_string())
print(f"\nDecision pending — A330 VU follow-up NCs (plant FTO2, A30-REJ-PVU / RJ-PVU-REC): {follow_up.sum()}")
save(nc[current ^ (in_scope & nc.rec_written)], "test5_tag_changes.csv")
verdict("TEST 5 pipeline changes", (in_scope & nc.rec_written & ~current).sum() == 0,
        f"{(current & ~nc.rec_written).sum()} lose REC, {(in_scope & nc.rec_written & ~current).sum()} gain REC "
        f"in scope, {new_scope.sum()} new REC NCs outside scope")

# %% Summary
print("\n" + "=" * 70 + "\nSUMMARY")
for name, status, detail in results:
    print(f"{status:7} {name}: {detail}")
print(f"\nCSV files in ./{OUT_DIR}/")
