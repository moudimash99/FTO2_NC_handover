"""
Skywise (Foundry) transforms for the FTO2 NC dashboard: parser v4.8.

Put this file, fto2_logic.py and nc_defect_parser.py in the same folder of a Python
transforms Code Repository (the folder that holds the example transform, usually
src/<project>/datasets/). Edit only the EDIT block at the top of fto2_logic.py.
Then Commit and Build fto2_defects first, then fto2_nc. Both datasets are created on
their first build.

pandas must be listed as a run dependency of the repository (Libraries panel, or
meta.yml); otherwise the build fails on "No module named pandas".
"""
from transforms.api import transform_pandas, Input, Output

from .fto2_logic import SAP_NC_DATASET, DEFECTS_DATASET, NC_DATASET, build_defects, build_nc


@transform_pandas(
    Output(DEFECTS_DATASET),
    sap_nc=Input(SAP_NC_DATASET),
)
def fto2_defects(sap_nc):
    return build_defects(sap_nc)


@transform_pandas(
    Output(NC_DATASET),
    sap_nc=Input(SAP_NC_DATASET),
    defects=Input(DEFECTS_DATASET),
)
def fto2_nc(sap_nc, defects):
    return build_nc(sap_nc, defects)
