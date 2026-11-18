"""The Skywise run: everything the pipeline notebook does, in one function the notebook calls.

    from foundry.transforms import Dataset, Column
    from fto2 import skywise
    skywise.run(Dataset, Column)

Dataset and Column are passed in (rather than imported here) so that the same run works in the pipeline notebook and in
the Code Repository's transform (fto2/transform_io.py gives it the transform's inputs and outputs).

Steps:
  0. the settings a person edits and the downloaded files are read once: a mistake stops the run before anything is written
  A. the standard selection: NCs of the plant created in the year followed (config/2_parametres.csv, annee), plus the NCs of
     other plants where the plant is liable; the exclusions and the *_auto columns from the rule tables (fto2/selection.py)
  B. the NCs of the GPS register and the Test list that the selection does not catch, fetched by number
  C. both, with the lists' columns; while 'garder_anciennes_sorties' is oui, the former four outputs are written as before
  D. the dashboard's three tables: parser, root-cause labels, rework orders, aléas, cost model -> fto2_dash_nc,
     fto2_dash_defects, fto2_dash_disruptions; plus fto2_lines_to_label.csv for the next labelling pass
  E. the reference data of the three pages (production plan, comparison year, cables, MFT actions, cost settings, cause tree)
     -> fto2_dash_ref. The production plan and the cable requests come from their exports as they are: pasted in the
     Fusion sheets (fto2/fusion.py), or saved in data/ (fto2/downloads.py).
All the settings come from data/config/ (1_parametres.csv, 2_sources.csv and the other tables).
"""
import time

import pandas as pd

from . import config, downloads, manual_lists, reference, selection
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
    "material", "material_description_fr", "material_description_en",   # the part the NC is about (for its price)
    "article_version_description",
    "creation_time", "changed_time", "closure_time", "completion_time",
]
WO_COLUMNS = ["order_number", "order_type", "operation_number", "operation_short_text", "plant", "labor_standard_value",
              "unit_of_measure_for_the_standard_value_labor", "setup_standard_value", "unit_of_measure_for_the_standard_value_setup"]
ALEA_COLUMNS = ["disruption_id", "plant", "physical_station", "work_order", "wo_designation", "ds_material", "type_desc", "open_date_time",
                "status", "time_lost", "program", "comment"]


def _liable(element, plant):
    """True when the plant is in an NC's liability (a list in Skywise, or a text, possibly written as a list: '[A, B]')."""
    if isinstance(element, list):
        return plant in element
    if isinstance(element, str):
        return element == plant or plant in [x.strip() for x in element.strip("[]").split(",")]
    if hasattr(element, "__iter__"):
        return plant in list(element)
    return False


def _when(df, column):
    try:
        return pd.to_datetime(df[column], errors="coerce", utc=True, format="mixed")
    except (TypeError, ValueError):   # older pandas: no format="mixed"
        return pd.to_datetime(df[column], errors="coerce", utc=True)


def _since(df, column, day):
    """The rows dated on or after a day ('AAAA-MM-JJ'); a row whose date cannot be read is kept (see _until)."""
    return df[~(_when(df, column) < pd.Timestamp(day, tz="UTC"))].reset_index(drop=True)


def _until(df, column, day):
    """The rows dated before a day ('AAAA-MM-JJ'); a row whose date cannot be read is kept. Skywise's filter fails when three
    conditions are joined with & (TypeError in OpAndWrapper): the reads give two, and the end of the year is cut here. The
    column is a date (Skywise) or text in mixed formats."""
    return df[~(_when(df, column) >= pd.Timestamp(day, tz="UTC"))].reset_index(drop=True)


def _work_list(Dataset, name, table, sep):
    """Write a work list (lines to label, materials to price): to the dataset of that name when the run has one (the Code
    Repository's transform declares both), else to a CSV file beside the notebook. Returns where it went."""
    if getattr(Dataset, "has", lambda n: False)(name):
        Dataset.get(name).write_table(table)
        return "dataset " + name
    table.to_csv(name + ".csv", index=False, sep=sep, encoding="utf-8-sig")
    return name + ".csv"


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


def select_ncs(Dataset, Column, mode, missing_ids=(), since=None):
    """The NCs to process. mode STANDARD: the plant's NCs created in the year followed plus the other plants' NCs where the
    plant is liable; mode MISSING_IDS: the NCs whose numbers are given (those of the GPS register and the Test list that the
    standard selection did not catch), kept when created in the year followed. Both then go through the exclusion rules."""
    plant = config.parameter("usine")
    since = (since or config.first_day()) + " 00:00:00"
    nc = config.parameter("dataset_nc", manual_lists.SOURCES)
    if mode == "STANDARD":
        home = (Dataset.get(nc).where((Column.get("plant") == plant) & (Column.get("creation_time") >= since))
                .select(*NC_COLUMNS).read_table(format="pandas"))
        other = Dataset.get(nc).where((Column.get("plant") != plant) & (Column.get("creation_time") >= since))
        if hasattr(Column, "array_contains"):   # the scheduled pipeline (fto2/transform_io.py): the liability is tested before reading
            other = other.where(Column.array_contains("liability", plant))
        other = other.select(*NC_COLUMNS).read_table(format="pandas")
        other = other[other["liability"].apply(lambda e: _liable(e, plant))]
        df = _until(pd.concat([home, other], ignore_index=True), "creation_time", config.year_end())
    elif mode == "MISSING_IDS":
        df = (Dataset.get(nc).where(Column.get("notification_no_leading_zeros").isin(list(missing_ids)))
              .select(*NC_COLUMNS).read_table(format="pandas"))
        df = _since(_until(df, "creation_time", config.year_end()), "creation_time", config.first_day())
    else:
        raise ValueError("mode must be STANDARD or MISSING_IDS")
    print(f"Total rows fetched: {len(df)}")
    stations = station_descriptions(config.parameter("postes", manual_lists.SOURCES))
    df = selection.apply_rules(df, stations, exclude=True)
    df = df.sort_values(by="creation_time", ascending=False)
    cap = config.parameter("limite_nc")
    return df.head(int(cap)) if cap else df


def check_settings():
    """Read the settings a person edits and the downloaded files once, before anything is fetched from Skywise or written:
    a mistake in one of them stops the run here, in a few seconds, with its message and with nothing changed. (The rule
    tables are checked when the first NCs go through them, also before anything is written.)"""
    from .cost import params, parts   # noqa: F401   the cost settings are read when the module loads
    from . import core
    config.year()
    config.comparison_year()
    core.check_cause_tree()          # the Définitions tab's cause tree says what the code decides
    reference.page_settings()        # the target, the opening view, the technical page settings, colours, alarm settings
    reference.mft_actions_page()     # the MFT actions: ids, kind of problem, dates
    parts.price_list()               # the part prices
    asof, recs = reference._production_export()   # the exports of the production plan
    if asof:
        reference.working_day_volume(asof, recs)  # ... and the shutdown calendar
    for note in reference.calendar_notes():
        print("⚠️ " + note)
    reference.cable_requests()       # the cable team's tracker


def run(Dataset, Column, say=None, old_outputs=None):
    """The whole run. Returns the three dashboard tables (also written to Skywise). old_outputs: write the former Slate app's
    tables too (None: as the line garder_anciennes_sorties of 2_parametres.csv says; the scheduled transform says no)."""
    from . import core   # the data steps (parser, labels, cost model, tables)
    t0 = time.time()
    say = say or (lambda msg: print(f"[{time.time() - t0:6.1f} s] {msg}", flush=True))
    say("Checking the settings and the downloaded files...")
    check_settings()
    keep_old = config.parameter_yes("garder_anciennes_sorties") if old_outputs is None else old_outputs
    since = config.aleas_since() + " 00:00:00"
    plant = config.parameter("usine")
    say(f"Year followed: {config.year()} (compared with {config.comparison_year()})")

    say("Reading the GPS register and the Test list...")
    external = manual_lists.external_table()
    ids = manual_lists.list_ids()
    say(f"   {len(ids)} NC numbers on the lists dated {config.year()}")

    say("Standard selection: fetching the plant's NCs and the NCs it is liable for...")
    standard = manual_lists.add_external(select_ncs(Dataset, Column, "STANDARD", since=config.first_day_read()), external)
    say(f"   standard selection: {len(standard)} NCs")
    caught = set(standard["notification_number"].astype(str).str.lstrip("0"))
    missing = sorted(i.lstrip("0") for i in ids if i.lstrip("0") not in caught)
    print(f"GPS / Test lists: {len(ids)} NCs; {len(missing)} not in the standard selection, fetched by number")
    runs = [("fto2_dashboard_data", standard)]
    if missing:
        say(f"Missing IDs: fetching {len(missing)} NCs by number...")
        extra = manual_lists.add_external(select_ncs(Dataset, Column, "MISSING_IDS", missing), external)
        found = set(extra["notification_number"].astype(str).str.lstrip("0"))
        print(f"   kept: {len(found)}; the other {len(set(missing) - found)} are dated another year, left out by the "
              f"exclusion rules, or not in Skywise")
        runs.append(("fto2_dashboard_data_missing_ids", extra))

    frames = []
    for name, final_df in runs:
        final_df["Ext_Nb_Defauts"] = pd.to_numeric(final_df["Ext_Nb_Defauts"], errors="coerce")
        if keep_old:   # the former outputs, for the former Slate app: the year followed only, as it has always had
            from .parser.nc_defect_parser import explode_dataframe
            say(f"Former outputs: parsing and writing {name}...")
            old_df = _since(final_df, "creation_time", config.first_day())
            _, defects_df = explode_dataframe(df=old_df, text_col="description_long_text", id_col="notification_number",
                                              manual_count_col="Ext_Nb_Defauts")
            for col in ["code", "fin", "text", "source_format", "mode_erreur", "type_reporting", "loc", "severite", "sub_code",
                        "confidence", "resolved_by", "sap_type", "severite_off"]:
                if col in defects_df.columns:
                    defects_df[col] = defects_df[col].astype(str).fillna("")
            Dataset.get(name.replace("fto2_dashboard_data", "fto2_parsed_defects")).write_table(defects_df)
            Dataset.get(name).write_table(old_df)
            print(f"✅ {name}: {len(old_df)} NCs, {len(defects_df)} defects (former outputs)")
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
        from .cost import params as cost_settings
        ops = (Dataset.get(wo).where((Column.get("plant") == plant) & Column.get("order_type").isin(list(cost_settings.ORDER_TYPES)))
               .select(*WO_COLUMNS).read_table(format="pandas"))
        say(f"   {len(ops)} operations")
    al = config.parameter("dataset_aleas", manual_lists.SOURCES)
    if al:
        say(f"Reading {al} (aléas at {plant} since {since[:10]})...")
        dis = (Dataset.get(al).where((Column.get("plant") == plant) & (Column.get("open_date_time") >= since))
               .select(*ALEA_COLUMNS).read_table(format="pandas"))
        dis = _until(dis, "open_date_time", config.year_end())
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
    where = _work_list(Dataset, "fto2_lines_to_label", to_label, sep=",")
    say(f"{len(to_label)} defect lines to label -> {where}")
    to_price = prepared["parts_to_price"]
    where = _work_list(Dataset, "fto2_parts_to_price", to_price, sep=";")
    print("parts:", info.get("parts"), "|", len(to_price), "materials with no price yet ->", where)

    say(f"The comparison year {config.comparison_year()}, from the same NCs...")
    y25 = reference.comparison_year(prepared)   # 'y25': the block's name for it, whatever the year
    say("   %s NCs" % (reference.REPORT.get("comparison_year", {}).get("ncs", 0) if y25 else "no"))
    say("Reference data: production plan, cable requests, MFT actions, settings...")
    eq = reference.eqmsn(prepared["nc"])
    blocks = {"dashboard": reference.dashboard_block(prepared["d"], prepared["nc"], prepared["codes"], y25),
              "mft": reference.mft_block(eq)}
    ref_t = reference.ref_table(blocks)
    Dataset.get("fto2_dash_ref").write_table(ref_t)
    print("✅ fto2_dash_ref:", len(ref_t), "rows (the pages' reference data)")
    for line in downloads.report():
        print("  ", line)
    # the cost explanation of each NC, for the optional Slate functions:
    # optional, so a missing dataset only prints a note
    try:
        cx_t = explain.table(nc_t, def_t, blocks["dashboard"]["cnqp"])
        Dataset.get("fto2_dash_cout").write_table(cx_t)
        print("✅ fto2_dash_cout:", len(cx_t), "rows (the cost explanation of each NC)")
    except Exception as e:
        why = "the dataset is not in the Data panel" if isinstance(e, KeyError) or "AliasNotDefined" in str(e) else str(e).splitlines()[0][:200]
        print("fto2_dash_cout not written (%s): normal, only an optional Slate set-up reads it." % why)
    say("Done.")
    from . import fusion
    for line in fusion.ALERTS:   # a Fusion sheet pasted as it is that the run could not use: said at the start, and here
        print(line)
    for path in manual_lists.NOT_READ:
        print(f"⚠️ The list '{path}' could not be read (see the error above): its NCs carry no GPS / Test information in this run.\n"
              f"   Its name is in data/config/2_sources.csv ({{annee}} stands for the year followed).")
    for note in reference.calendar_notes():   # again at the end, where it is read
        print("⚠️ " + note)
    import datetime as dt
    if dt.date.today().year > config.year():
        print(f"⚠️ The year followed is {config.year()} and we are in {dt.date.today().year}: the pages show the NCs of {config.year()} only.\n"
              f"   To follow the current year, empty the line 'annee' of data/config/1_parametres.csv and run the notebook again.")
    return nc_t, def_t, dis_t
