import os
import re
import time
import numpy as np
import pandas as pd
from foundry.transforms import Dataset, Column
# ==========================================
# REC RULE TEST — run in the pipeline notebook environment
# ==========================================
# Tests the "REC written" rule (writer department) on the Skywise non_conformity dataset.
# Run it where the pipeline notebook runs (same "non_conformity" dataset): paste it in a cell,
# or upload it next to the notebook and run `%run rec_rule_test.py`. Read-only: it writes nothing to Skywise.
# Every filter runs in Skywise: 4 queries, a few thousand rows back. FULL_SCAN = True adds the
# all-Airbus scan (slow: ~800,000 rows since January) for TEST 4 and the cross-plant part of TEST 5.
# Each test prints PASS or REVIEW; rows to read are saved as CSV in OUT_DIR.
#   TEST 1  every NC in the REC tracker is tagged (recall)
#   TEST 2  every NC tagged at a FAL plant is REC: one line per writer to review (precision)
#   TEST 3  REC-looking NCs the rule leaves out (REC inspectors, writers whose department moved)
#   TEST 4  old rules (42RC, RECX/SUBR, workflow regex) against the new one, all plants (FULL_SCAN only)
#   TEST 5  what changes for the pipeline tag and scope
# Skywise run of 21 Oct (five departments): TEST 1 115/115; TEST 2 2,818 tagged at FAL plants, of which
# 2,697 by OSOOM/DERICHEBOURG (a FAL department) -> OSOOM now counts only at a 42RC station.

# %% Configuration
START = "2026-01-01 00:00:00"   # same window as the pipeline
OUT_DIR = "rec_test_output"
CHUNK = 5000                     # NC numbers per isin() query (FULL_SCAN only)
FULL_SCAN = False                # True: also run TEST 4 and the cross-plant part of TEST 5 (slow)

REC_DEPTS = [                             # FTO2 quality departments: REC when they write at a FAL plant
    "QRT/DERICHEBOURG AERONAUTICS",
    "QR/DERICHEBOURG AERONAUTICS",
    "QLOT1/AIRBUS OPERATIONS SAS",
]
REC_DEPTS_AT_REC_STATION = [              # FAL departments that also hold REC inspectors: REC only at a 42RC station
    "OSOOM/DERICHEBOURG AERONAUTICS",     # 21 Oct: 2,697 FAL NCs since January; its 26 tracker NCs are all at 42RC
]
ALL_REC_DEPTS = REC_DEPTS + REC_DEPTS_AT_REC_STATION
REC_STATION = "42RC"
KNOWN_REC_STATIONS = ["V42RC1", "F42RC1", "F42RC2", "D42RC1"]   # TEST 3 reads these; it warns about new 42RC codes
REC_WORKFLOW = r"^(REC-|A30-REJ-PVU|RJ-PVU-REC)"
CURRENT_REGEX = r"\bREC\b|-CRE|-PNC|A30-REJ-PVU2"                 # today's pipeline tag

# Cross-checks only (the rule does not use them)
REC_INSPECTOR_IDS = ["ST32873", "GALIZ81C", "RGAGTM5M", "PMAR3D30", "CLOP5B4I", "TO74350"]
REC_HEADER_ORGS = [                       # writer org as printed in the long text when the NC was written
    "QRT/DERICHEBOURG AERONAUTICS", "QR/DERICHEBOURG AERONAUTICS", "QLOT1/AIRBUS OPERATIONS SAS",
    "QRTE/AIRBUS OPERATIONS SAS", "QRT3E/AIRBUS OPERATIONS SAS", "Q1AF/DERICHEBOURG AERONAUTICS",
]                                         # + OSOOM/DERICHEBOURG AERONAUTICS at a 42RC station
KNOWN_WRITERS = {                         # writers in the REC departments who are not REC (seen in the exports)
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
TEXT_COLS = LIGHT_COLS + ["description_long_text"]
os.makedirs(OUT_DIR, exist_ok=True)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 45)
results = []
T0 = time.time()


# %% The rule
def rec_written(df):
    """True when the NC was written by REC: writer department in REC_DEPTS (OSOOM only at a 42RC
    station) and either raised outside plant FTO2, or inside FTO2 on a REC workflow (IEVB excluded)."""
    at_rec_station = df["station"].str.contains(REC_STATION)
    dept = (df["user_department"].isin(REC_DEPTS)
            | (df["user_department"].isin(REC_DEPTS_AT_REC_STATION) & at_rec_station))
    wf = df["workflow_list"].str.match(REC_WORKFLOW)
    ievb = df["work_ctr"].str.startswith("IEVB")
    return dept & ((df["plant"] != "FTO2") | (wf & ~ievb))


# %% Helpers
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
    """Strings everywhere (vectorised; only the liability array is mapped row by row)."""
    df = df.copy()
    for c in df.columns:
        if c == "liability":
            df[c] = df[c].map(as_text)
        elif c != "creation_time":
            df[c] = df[c].where(df[c].notna(), "").astype(str).str.strip()
    if "creation_time" in df:
        df["created"] = pd.to_datetime(df["creation_time"].astype(str).str[:19].str.replace("T", " "),
                                       errors="coerce")
    if "status_open_closed" in df:
        df["deleted"] = df["status_open_closed"].str.contains("deleted", case=False)
    df = df.drop_duplicates("notification_no_leading_zeros").reset_index(drop=True)
    df["rec_written"] = rec_written(df)
    return df


def fetch(condition, cols, label):
    t = time.time()
    df = (Dataset.get("non_conformity")
          .where(condition)
          .select(*cols)
          .read_table(format="pandas"))
    print(f"  {label}: {len(df)} rows in {time.time() - t:.0f} s")
    return prep(df)


HEADER = re.compile(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\(\s*(\S+)\s+([^)]*?)\s*\)")


def creation_line(text):
    """The header that opens the long text = who wrote the NC. When the text opens with the
    'Moment of Detection' block there is no creation line and the first header is a later comment."""
    m = HEADER.search(text)
    if not m or m.start() > 150 or "Moment of Detection" in text[:m.start()]:
        return None
    return m


def add_writer(df):
    """Writer ID and org from the creation line ('' when there is none; masked IDs show as #UID~)."""
    t = df["description_long_text"]
    first = t.map(creation_line)
    df = df.assign(writer_id=first.map(lambda m: m.group(1) if m else ""),
                   writer_org=first.map(lambda m: m.group(2) if m else ""),
                   text_start=t.str.replace(r"\s+", " ", regex=True).str[:300])
    df["writer"] = np.where(df.writer_id.eq(""), "(no creation line)", df.writer_id)
    df["kind"] = np.select(
        [df.writer_id.isin(REC_INSPECTOR_IDS), df.writer_id.isin(list(KNOWN_WRITERS)), df.writer_id.eq("#UID~"),
         df.writer_id.eq("")],
        ["REC inspector", "known non-REC: " + df.writer_id.map(KNOWN_WRITERS).fillna(""), "masked",
         "no creation line"],
        default="NEW - who is this?")
    return df


def verdict(name, ok, detail):
    results.append((name, "PASS" if ok else "REVIEW", detail))
    print(f"\n>>> {name}: {'PASS' if ok else 'REVIEW'} — {detail}")


def save(df, name):
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"    saved {len(df)} rows to {path}")


# %% Fetch: filters run in Skywise, only the rows the tests use come back
print(f"Fetching NCs since {START}:")
since = Column.get("creation_time") >= START
cand = add_writer(fetch(Column.get("user_department").isin(ALL_REC_DEPTS) & since, TEXT_COLS,
                        "written by the REC departments"))
recst = add_writer(fetch(Column.get("station").isin(KNOWN_REC_STATIONS) & since, TEXT_COLS,
                         "at the REC stations"))
trk = add_writer(fetch(Column.get("notification_no_leading_zeros").isin(TRACKER_NCS + TRACKER_NOT_REC), TEXT_COLS,
                       "tracker NCs (all dates)"))
fto2 = fetch((Column.get("plant") == "FTO2") & since, LIGHT_COLS, "plant FTO2")
print(f"Tagged REC written since {START}: {cand.rec_written.sum()} ({time.time() - T0:.0f} s so far)")

# %% TEST 1 — recall on the REC tracker (all dates)
print("\n" + "=" * 70 + "\nTEST 1 — REC tracker: every NC REC wrote must be tagged")
is_rec = trk["notification_no_leading_zeros"].isin(TRACKER_NCS)
not_found = sorted(set(TRACKER_NCS) - set(trk["notification_no_leading_zeros"]))
missed = trk[is_rec & ~trk.rec_written]
wrong = trk[~is_rec & trk.rec_written]
print(f"Found in Skywise: {is_rec.sum()}/{len(TRACKER_NCS)} | caught: {(is_rec & trk.rec_written).sum()}"
      f" | missed: {len(missed)} | 217022710 tagged: {len(wrong)}")
print(f"For comparison, the 6 inspector IDs find {(is_rec & trk.kind.eq('REC inspector')).sum()}/{is_rec.sum()} "
      f"(masked #UID~ on {(is_rec & trk.kind.eq('masked')).sum()}, no creation line on "
      f"{(is_rec & trk.kind.eq('no creation line')).sum()})")
if not_found:
    print("Not found in Skywise:", not_found)
cols = ["notification_no_leading_zeros", "created", "plant", "station", "workflow_list", "user_department",
        "writer", "kind", "description_short"]
print(pd.concat([missed, wrong])[cols].to_string(index=False))
save(pd.concat([missed, wrong]), "test1_tracker_missed.csv")
verdict("TEST 1 tracker recall", len(missed) == 0 and len(wrong) == 0 and not not_found,
        f"{(is_rec & trk.rec_written).sum()}/{len(TRACKER_NCS)} caught (expected 115/115)")

# %% TEST 2 — precision at FAL plants: one line per writer to review
print("\n" + "=" * 70 + "\nTEST 2 — NCs tagged REC outside plant FTO2: are they all REC?")
fal = cand[cand.rec_written & (cand.plant != "FTO2")].copy()
fal["in_tracker"] = fal["notification_no_leading_zeros"].isin(TRACKER_NCS)
fal["at_42RC"] = fal.station.str.contains(REC_STATION)
print(f"Tagged REC outside plant FTO2: {len(fal)} ({fal.deleted.sum()} deleted). Exports: at least 84 (11 deleted). "
      f"21 Oct before the OSOOM fix: QRT 45, QR 34, QLOT1 38")
if len(fal):
    print(pd.crosstab(fal.user_department, fal.plant, margins=True).to_string())
osoom = cand[cand.user_department.isin(REC_DEPTS_AT_REC_STATION) & (cand.plant != "FTO2")]
print(f"\nOSOOM at FAL plants: {len(osoom)} NCs, {osoom.station.str.contains(REC_STATION).sum()} at a 42RC station "
      f"(tagged). Writers of the tagged ones:")
print(osoom[osoom.station.str.contains(REC_STATION)].groupby(["writer", "kind"]).size()
      .sort_values(ascending=False).head(15).to_string())
writers = (fal.groupby(["user_department", "writer", "kind"])
           .agg(ncs=("notification_no_leading_zeros", "size"), at_42RC=("at_42RC", "sum"),
                in_tracker=("in_tracker", "sum"), first=("created", "min"), last=("created", "max"),
                examples=("description_short", lambda s: " | ".join(s.head(3))))
           .reset_index().sort_values(["kind", "ncs"], ascending=[True, False]))
writers["dept"] = writers.user_department.str.split("/").str[0]
print("\nWriters of the NCs tagged at FAL plants (review the 'NEW' and 'known non-REC' lines):")
print(writers[["dept", "writer", "kind", "ncs", "at_42RC", "in_tracker", "examples"]].to_string(index=False))
to_read = fal[~fal.in_tracker & ~fal.kind.eq("REC inspector")].sort_values(["user_department", "writer"])
cols = ["notification_no_leading_zeros", "created", "plant", "station", "workflow_list", "decision_status",
        "user_department", "writer", "writer_org", "kind", "description_short", "text_start"]
print(f"\nRows not in the tracker and not by a known REC inspector: {len(to_read)} from {to_read.writer.nunique()} "
      f"writers (test2_fal_rows_to_read.csv)")
save(fal[cols + ["in_tracker", "at_42RC"]], "test2_fal_all_tagged.csv")
save(writers.drop(columns="dept"), "test2_writers.csv")
save(to_read[cols], "test2_fal_rows_to_read.csv")
new_or_bad = fal.kind.str.startswith(("NEW", "known non-REC"))
verdict("TEST 2 FAL-plant precision", not new_or_bad.any(),
        f"{len(fal)} tagged; {new_or_bad.sum()} NCs by {fal[new_or_bad].writer.nunique()} new or non-REC writers; "
        f"{len(to_read)} not in tracker and not by a REC inspector")

# %% TEST 3 — REC-looking NCs the rule does not tag
print("\n" + "=" * 70 + "\nTEST 3 — REC NCs the rule leaves out")
untagged = recst[~recst.rec_written]
print(f"NCs at the REC stations {KNOWN_REC_STATIONS} not tagged: {len(untagged)} "
      f"(expected: written by FAL or FTO2 methods for REC to fix). By department:")
print(untagged.user_department.value_counts().head(20).to_string())
by_inspector = pd.concat([untagged, cand[~cand.rec_written]]).drop_duplicates("notification_no_leading_zeros")
by_inspector = by_inspector[by_inspector.kind.eq("REC inspector")]
rec_org = (untagged.writer_org.isin(REC_HEADER_ORGS) | untagged.writer_org.isin(REC_DEPTS_AT_REC_STATION))
by_rec_org = untagged[rec_org & ~untagged.user_department.isin(ALL_REC_DEPTS)]
new_st = sorted(set(cand.station[cand.station.str.contains(REC_STATION)]) - set(KNOWN_REC_STATIONS))
cols = ["notification_no_leading_zeros", "created", "plant", "station", "work_ctr", "workflow_list",
        "user_department", "writer", "writer_org", "description_short", "text_start"]
print(f"\nNot tagged but written by a REC inspector: {len(by_inspector)} | at a REC station, written under a REC org "
      f"by someone now in another department: {len(by_rec_org)}")
print(pd.concat([by_inspector, by_rec_org])[cols[:-1]].drop_duplicates().head(40).to_string(index=False))
if new_st:
    print(f"42RC stations used by the REC departments but missing from KNOWN_REC_STATIONS (add them): {new_st}")
save(untagged[cols], "test3_rec_station_untagged.csv")
save(pd.concat([by_inspector, by_rec_org])[cols].drop_duplicates(), "test3_possible_missed.csv")
verdict("TEST 3 missed REC NCs", len(by_inspector) + len(by_rec_org) == 0 and not new_st,
        f"{len(by_inspector)} by REC inspectors, {len(by_rec_org)} under a REC org with another department now, "
        f"{len(new_st)} new 42RC stations")

# %% TEST 4 — old rules against the new one, all plants (FULL_SCAN only)
print("\n" + "=" * 70 + "\nTEST 4 — how general each rule is (all NCs since START)")
if FULL_SCAN:
    nc = pd.concat([fto2, fetch((Column.get("plant") != "FTO2") & since, LIGHT_COLS, "other plants (full scan)")],
                   ignore_index=True)
    rules = {
        "station 42RC": nc.station.str.contains(REC_STATION),
        "work_ctr RECX/SUBR": nc.work_ctr.str.match(r"^(RECX|SUBR)"),
        "current workflow regex": nc.workflow_list.str.contains(CURRENT_REGEX, case=False),
        "writer department (new)": nc.rec_written,
    }
    rec_dept = nc.user_department.isin(ALL_REC_DEPTS)
    table = pd.DataFrame([{"rule": k, "hits": int(m.sum()), "written by REC depts": int((m & rec_dept).sum()),
                           "written by others": int((m & ~rec_dept).sum()),
                           "outside plant FTO2": int((m & (nc.plant != "FTO2")).sum())} for k, m in rules.items()])
    print(table.to_string(index=False))
    print("42RC station codes:", nc.station[rules["station 42RC"]].value_counts().to_dict())
    save(table, "test4_rule_comparison.csv")
    verdict("TEST 4 rule comparison", True, "information only (see table)")
else:
    print("Skipped (FULL_SCAN = False). 21 Oct: 42RC 396 hits, 263 written by others; RECX/SUBR 36; "
          "current regex 35,866 across Airbus.")

# %% TEST 5 — what changes for the pipeline
print("\n" + "=" * 70 + "\nTEST 5 — changes against the current pipeline tag")
current = fto2.workflow_list.str.contains(CURRENT_REGEX, case=False)
print(f"Plant FTO2 since START: {len(fto2)} NCs | REC today: {current.sum()} | REC with the new rule: "
      f"{fto2.rec_written.sum()} | lose REC: {(current & ~fto2.rec_written).sum()} | gain REC: "
      f"{(fto2.rec_written & ~current).sum()}")
print("Plant FTO2, REC today but not now — by writer department:")
print(fto2[current & ~fto2.rec_written].user_department.value_counts().head(12).to_string())
follow_up = fto2.rec_written & fto2.workflow_list.str.match(r"^(A30-REJ-PVU|RJ-PVU-REC)")
print(f"Decision pending — A330 VU follow-up NCs (plant FTO2, A30-REJ-PVU / RJ-PVU-REC): {follow_up.sum()}")
outside = fal[~fal.liability.str.contains(r"\bFTO2\b")]
print(f"\nREC NCs the pipeline does not fetch today (plant not FTO2, not FTO2-liable): {len(outside)}")
print(outside.plant.value_counts().to_string())
if FULL_SCAN:
    cross = nc[(nc.plant != "FTO2") & nc.liability.str.contains(r"\bFTO2\b")]
    cur_x = cross.workflow_list.str.contains(CURRENT_REGEX, case=False)
    print(f"FTO2-liable NCs at other plants: {len(cross)} | REC today: {cur_x.sum()} | lose REC: "
          f"{(cur_x & ~cross.rec_written).sum()} | gain REC: {(cross.rec_written & ~cur_x).sum()}")
save(fto2[current ^ fto2.rec_written], "test5_tag_changes_plant_fto2.csv")
verdict("TEST 5 pipeline changes", (fto2.rec_written & ~current).sum() == 0,
        f"plant FTO2: {(current & ~fto2.rec_written).sum()} lose REC, {(fto2.rec_written & ~current).sum()} gain; "
        f"{len(outside)} REC NCs outside today's scope")

# %% Summary
print("\n" + "=" * 70 + "\nSUMMARY")
for name, status, detail in results:
    print(f"{status:7} {name}: {detail}")
print(f"\nCSV files in ./{OUT_DIR}/ — total {time.time() - T0:.0f} s")
