"""
FALLBACK: use this only if you cannot create a Code Repository.

Code Workbook version of the two transforms.
1. In the workbook, open Global code (Python). Paste the whole of nc_defect_parser.py,
   then the whole of fto2_logic.py below it, and edit the EDIT block. The dataset paths
   in that block are not used here; leave them as they are.
2. Add the SAP NC dataset to the workbook. In each new transform's Inputs tab, set the
   input type to "Pandas dataframe".
3. Create a Python transform named fto2_defects with the SAP NC dataset as its input,
   and paste the first function below. The argument name must match the input's alias
   in the workbook: rename `sap_nc` if your alias is different.
4. Create a Python transform named fto2_nc with two inputs, the SAP NC dataset and
   fto2_defects, and paste the second function below.
5. Turn on "Save as dataset" for both nodes, then run fto2_defects first, then fto2_nc.
"""


def fto2_defects(sap_nc):
    return build_defects(sap_nc)


def fto2_nc(sap_nc, fto2_defects):
    return build_nc(sap_nc, fto2_defects)
