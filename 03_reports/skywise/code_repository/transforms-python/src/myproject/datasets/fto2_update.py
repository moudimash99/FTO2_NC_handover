"""FTO2 NC dashboard: the update, as a transform that Skywise can run on a schedule.

The same steps as the pipeline notebook. The code is in src/fto2 (start with fto2/skywise.py), the settings in
src/fto2/settings, the station list in src/fto2/files.

Inputs: the four Skywise datasets below. Optional inputs, one line each in the list below (nothing else to change):
  - the settings kept in Fusion: fto2_set_targets, fto2_set_cost, fto2_set_blackout, fto2_set_deliveries, fto2_set_eqmsn,
    fto2_set_plant, fto2_set_part_prices, fto2_set_cables, fto2_set_gps, fto2_set_test. One that is not listed: its file
    of src/fto2/settings is used.
  - fto2_plan_exports: a dataset holding the exports of the Tableau Avances / Retards (production plan), one file per
    download, the date at the end of its name, the older ones kept. Not listed: the plan stays as last read.
Outputs: the four tables the pages read, and two work lists (the defect lines still to label, the parts still to price).
"""
from transforms.api import Input, LightweightInput, LightweightOutput, Output, transform

FOLDER = "/Users/MMACX64V/workbook-output/"   # the folder where the tables are written
TEST = "_test"   # first builds: tables of their own, to compare with the notebook's; then TEST = "" to write the real ones


@transform.using(
    non_conformity=Input("ri.foundry.main.dataset.de7c8f7e-90d4-435f-9b13-23291d662b0e"),
    fto2_ai_labels=Input("ri.foundry.main.dataset.750e7ebc-b07d-4ccc-bcd5-7163bb5da733"),
    work_order_operation=Input("ri.foundry.main.dataset.76c493ed-e717-4fd6-94e2-0207c0893c1c"),
    mes_disruptions=Input("ri.foundry.main.dataset.dda34674-9103-44da-9a4f-43f43d5074e7"),
    # optional inputs, for example:
    # fto2_set_cost=Input("<the dataset of the Fusion sheet 'Cost rates and times'>"),
    # fto2_plan_exports=Input("<the dataset holding the exports of the production plan>"),
    fto2_dash_nc=Output(FOLDER + "fto2_dash_nc" + TEST),
    fto2_dash_defects=Output(FOLDER + "fto2_dash_defects" + TEST),
    fto2_dash_disruptions=Output(FOLDER + "fto2_dash_disruptions" + TEST),
    fto2_dash_ref=Output(FOLDER + "fto2_dash_ref" + TEST),
    fto2_lines_to_label=Output(FOLDER + "fto2_lines_to_label" + TEST),
    fto2_parts_to_price=Output(FOLDER + "fto2_parts_to_price" + TEST),
)
def compute(
    non_conformity: LightweightInput,
    fto2_ai_labels: LightweightInput,
    work_order_operation: LightweightInput,
    mes_disruptions: LightweightInput,
    fto2_dash_nc: LightweightOutput,
    fto2_dash_defects: LightweightOutput,
    fto2_dash_disruptions: LightweightOutput,
    fto2_dash_ref: LightweightOutput,
    fto2_lines_to_label: LightweightOutput,
    fto2_parts_to_price: LightweightOutput,
    **optional_inputs,
):
    datasets = dict(locals())   # every input and output, by name
    datasets.update(datasets.pop("optional_inputs"))
    from fto2 import transform_io
    transform_io.run(datasets)
