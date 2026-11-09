"""The Skywise run: everything the pipeline notebook does, in one function the notebook calls.

    from foundry.transforms import Dataset, Column
    from fto2 import skywise
    skywise.run(Dataset, Column)

Dataset and Column are passed in (rather than imported here) so that the same run can be rehearsed on the laptop with a
stand-in for Skywise that serves local files (tests/notebook_rehearsal.py).

Steps:
  A. the standard selection: NCs of the plant created since the start date, plus the NCs of other plants where the plant is
     liable; the exclusions and the *_auto columns from the rule tables (fto2/selection.py)
  B. the NCs of the GPS register and the Test list that the selection does not catch, fetched by number
  C. both, with the lists' columns; while 'garder_anciennes_sorties' is oui, the former four outputs are written as before
  D. the dashboard's three tables: parser, root-cause labels, rework orders, aléas, cost model -> fto2_dash_nc,
     fto2_dash_defects, fto2_dash_disruptions; plus fto2_lines_to_label.csv for the next labelling pass
  E. the reference data of the three pages (production plan, comparison year, cables, MFT actions, cost settings, cause tree)
     -> fto2_dash_ref
All the settings come from data/config/ (2_parametres.csv, 2_sources.csv and the rule tables).
"""
import time

import pandas as pd

from . import config, manual_lists, reference, selection
from .cost import explain

# the columns of the non_conformity dataset the run reads
NC_COLUMNS = [
    "skywise_non_conformity_id", "notification_number", "notification_no_leading_zeros", "programme",
    "aircraft_type", "msn", "system", "notification_type", "linked_document",
    "nc_status", "system_status", "status_open_closed", "decision_status",
    "decision_status_description_en", "decision_date", "workflow_list",
    "description_short", "description_long_text",
    "defect_group_description_en", "defect_code", "defect_code_description_en",
    "ata_chapter", "cause_code", "cause_code_description_en",
    "cause_group_description_en", "cause_description",
    "plant", "plant_text", "work_ctr", "station", "major_component_description",
    "constituent_assembly", "operation", "work_order", "trigger", "origin",
    "liability", "liability_description", "responsible_defect_level1",
    "responsible_defect_level1_name", "user_department", "is_orgunit",
    "defect_quantity", "priority", "returned_flag", "article_version",
    "article_version_description",
    "creation_time", "changed_time", "closure_time", "completion_time",
]
WO_COLUMNS = ["order_number", "order_type", "operation_number", "operation_short_text", "plant", "labor_standard_value",
              "unit_of_measure_for_the_standard_value_labor", "setup_standard_value", "unit_of_measure_for_the_standard_value_setup"]
ALEA_COLUMNS = ["disruption_id", "plant", "physical_station", "work_order", "wo_designation", "ds_material", "type_desc", "open_date_time",
                "open_date_time_tz", "status", "time_lost", "program", "comment"]


def _liable(element, plant):
    """True when the plant is in an NC's liability (a list in Skywise, or a text)."""
    if isinstance(element, list):
        return plant in element
    if isinstance(element, str):
        return element == plant
    if hasattr(element, "__iter__"):
        return plant in list(element)
    return False


def station_descriptions(path):
    """{station: description} from the station mapping file (columns 'STATION A320', 'Désignations A320', ...)."""
    m = pd.read_csv(path)
    parts = []
    for line in ["A320", "A330", "A350", "A400M"]:
        t = m[[f"STATION {line}", f"Désignations {line}"]].dropna().copy()
        t.columns = ["station", "station_description"]
        parts.append(t)
    pairs = pd.concat(parts, ignore_index=True).drop_duplicates(subset=["station"])
    return dict(zip(pairs["station"], pairs["station_description"]))


def select_ncs(Dataset, Column, mode, missing_ids=()):
    """The NCs to process. mode STANDARD: the plant's NCs since the start date plus the other plants' NCs where the plant is
    liable, then the exclusion rules; mode MISSING_IDS: the NCs whose numbers are given (no exclusion)."""
    plant = config.parameter("usine")
    since = config.parameter("date_debut") + " 00:00:00"
    nc = config.parameter("dataset_nc", manual_lists.SOURCES)
    if mode == "STANDARD":
        home = (Dataset.get(nc).where((Column.get("plant") == plant) & (Column.get("creation_time") >= since))
                .select(*NC_COLUMNS).read_table(format="pandas"))
        other = (Dataset.get(nc).where((Column.get("plant") != plant) & (Column.get("creation_time") >= since))
                 .select(*NC_COLUMNS).read_table(format="pandas"))
        other = other[other["liability"].apply(lambda e: _liable(e, plant))]
        df = pd.concat([home, other], ignore_index=True)
    elif mode == "MISSING_IDS":
        df = (Dataset.get(nc).where(Column.get("notification_no_leading_zeros").isin(list(missing_ids)))
              .select(*NC_COLUMNS).read_table(format="pandas"))
    else:
        raise ValueError("mode must be STANDARD or MISSING_IDS")
    print(f"Total rows fetched: {len(df)}")
    stations = station_descriptions(config.parameter("postes", manual_lists.SOURCES))
    df = selection.apply_rules(df, stations, exclude=(mode == "STANDARD"))
    df = df.sort_values(by="creation_time", ascending=False)
    cap = config.parameter("limite_nc")
    return df.head(int(cap)) if cap else df


def run(Dataset, Column, say=None):
    """The whole run. Returns the three dashboard tables (also written to Skywise)."""
    from . import core   # the data steps (parser, labels, cost model, tables)
    t0 = time.time()
    say = say or (lambda msg: print(f"[{time.time() - t0:6.1f} s] {msg}", flush=True))
    keep_old = config.parameter_yes("garder_anciennes_sorties")
    since = config.parameter("debut_ordres_et_aleas") + " 00:00:00"
    plant = config.parameter("usine")

    say("Reading the GPS register and the Test list...")
    external = manual_lists.external_table()
    ids = manual_lists.list_ids()
    say(f"   {len(ids)} NC numbers on the lists from {config.parameter('annee_listes_manuelles')}")

    say("Standard selection: fetching the plant's NCs and the NCs it is liable for...")
    standard = manual_lists.add_external(select_ncs(Dataset, Column, "STANDARD"), external)
    say(f"   standard selection: {len(standard)} NCs")
    caught = set(standard["notification_number"].astype(str).str.lstrip("0"))
    missing = sorted(i.lstrip("0") for i in ids if i.lstrip("0") not in caught)
    print(f"GPS / Test lists: {len(ids)} NCs; {len(missing)} not in the standard selection, fetched by number")
    runs = [("fto2_dashboard_data", standard)]
    if missing:
        say(f"Missing IDs: fetching {len(missing)} NCs by number...")
        extra = manual_lists.add_external(select_ncs(Dataset, Column, "MISSING_IDS", missing), external)
        found = set(extra["notification_number"].astype(str).str.lstrip("0"))
        print(f"   found in the NC dataset: {len(found)}; not in Skywise at all: {len(set(missing) - found)}")
        runs.append(("fto2_dashboard_data_missing_ids", extra))

    frames = []
    for name, final_df in runs:
        final_df["Ext_Nb_Defauts"] = pd.to_numeric(final_df["Ext_Nb_Defauts"], errors="coerce")
        if keep_old:   # the former outputs, for the former Slate app
            from .parser.nc_defect_parser import explode_dataframe
            say(f"Former outputs: parsing and writing {name}...")
            _, defects_df = explode_dataframe(df=final_df, text_col="description_long_text", id_col="notification_number",
                                              manual_count_col="Ext_Nb_Defauts")
            for col in ["code", "fin", "text", "source_format", "mode_erreur", "type_reporting", "loc", "severite", "sub_code",
                        "confidence", "resolved_by", "sap_type", "severite_off"]:
                if col in defects_df.columns:
                    defects_df[col] = defects_df[col].astype(str).fillna("")
            Dataset.get(name.replace("fto2_dashboard_data", "fto2_parsed_defects")).write_table(defects_df)
            Dataset.get(name).write_table(final_df)
            print(f"✅ {name}: {len(final_df)} NCs, {len(defects_df)} defects (former outputs)")
        final_df = final_df.copy()
        final_df["_source"] = name   # origin of each NC: normal, or missing_ids
        frames.append(final_df)

    say("Reading the root-cause labels...")
    labels = Dataset.get(config.parameter("dataset_labels", manual_lists.SOURCES)).read_table(format="pandas")
    say(f"   {len(labels)} stored labels")
    ops = dis = None
    wo = config.parameter("dataset_ordres", manual_lists.SOURCES)
    if wo:
        say(f"Reading {wo} (rework orders at {plant})...")
        ops = (Dataset.get(wo).where((Column.get("plant") == plant) & (Column.get("order_type") == "S03"))
               .select(*WO_COLUMNS).read_table(format="pandas"))
        say(f"   {len(ops)} operations")
    al = config.parameter("dataset_aleas", manual_lists.SOURCES)
    if al:
        say(f"Reading {al} (aléas at {plant} since {since[:10]})...")
        dis = (Dataset.get(al).where((Column.get("plant") == plant) & (Column.get("open_date_time") >= since))
               .select(*ALEA_COLUMNS).read_table(format="pandas"))
        say(f"   {len(dis)} aléas")
    say("Dashboard tables: parser, root-cause labels, rework orders, aléas, cost model...")
    nc_t, def_t, dis_t, info, to_label, prepared = core.build(frames, labels, ops=ops, dis=dis, say=say)

    say("Writing fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions...")
    Dataset.get("fto2_dash_nc").write_table(nc_t)
    Dataset.get("fto2_dash_defects").write_table(def_t)
    Dataset.get("fto2_dash_disruptions").write_table(dis_t)
    print("✅ FTO2 dashboard tables:", info["nc_table"], "NCs,", info["defect_table"], "defect lines,", info["disruption_table"],
          "aléas; level-3 CNQ:", info["level3_aec"], "EUR")
    print("NCs created", info["created_from"], "to", info["created_to"], "| origin:", info["origin"],
          "| defect lines without an AI label (parser label used):", info["to_label"])
    print("rework orders:", info["rework_orders"], "| aléas:", info.get("aleas", "not read"))
    to_label.to_csv("fto2_lines_to_label.csv", index=False)
    say(f"{len(to_label)} defect lines to label -> fto2_lines_to_label.csv")

    year = int(config.parameter("annee_comparaison"))
    say(f"Reading the NCs of {year} (comparison year)...")
    nc = config.parameter("dataset_nc", manual_lists.SOURCES)
    # two conditions only: Skywise's filter fails when three are joined with & (TypeError in OpAndWrapper); the end of the
    # year is cut here instead
    raw_year = (Dataset.get(nc).where((Column.get("plant") == plant) & (Column.get("creation_time") >= f"{year}-01-01 00:00:00"))
                .select(*NC_COLUMNS).read_table(format="pandas"))
    try:   # a date column (Skywise) or text in mixed formats
        created = pd.to_datetime(raw_year["creation_time"], errors="coerce", utc=True, format="mixed")
    except (TypeError, ValueError):   # older pandas: no format="mixed"
        created = pd.to_datetime(raw_year["creation_time"], errors="coerce", utc=True)
    raw_year = raw_year[created < pd.Timestamp(f"{year + 1}-01-01", tz="UTC")].reset_index(drop=True)
    say(f"   {len(raw_year)} NCs")
    stations = station_descriptions(config.parameter("postes", manual_lists.SOURCES))
    y25 = reference.year_2025(raw_year, stations) if len(raw_year) else None
    eq = reference.eqmsn(prepared["nc"])
    blocks = {"dashboard": reference.dashboard_block(prepared["d"], prepared["nc"], prepared["codes"], y25),
              "mft": reference.mft_block(eq),
              "elizabeth": {"vol": reference.weekly_volume(eq), "settings": reference.page_settings()}}
    ref_t = reference.ref_table(blocks)
    Dataset.get("fto2_dash_ref").write_table(ref_t)
    print("✅ fto2_dash_ref:", len(ref_t), "rows (the pages' reference data)")
    # the cost explanation of each NC, for the Slate set-up with two functions (03_reports/skywise/level3_datasets/fonctions/):
    # optional, so a missing dataset only prints a note
    try:
        cx_t = explain.table(nc_t, def_t, blocks["dashboard"]["cnqp"])
        Dataset.get("fto2_dash_cout").write_table(cx_t)
        print("✅ fto2_dash_cout:", len(cx_t), "rows (the cost explanation of each NC)")
    except Exception as e:
        print("fto2_dash_cout not written (%s). Only the Slate set-up with two functions reads it: add the dataset to the Data panel to use it." % e)
    say("Done.")
    return nc_t, def_t, dis_t
