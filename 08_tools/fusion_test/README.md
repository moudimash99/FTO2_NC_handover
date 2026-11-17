# Test: reading the Fusion settings spreadsheet

Checks that the update can read the settings from Fusion, and how Fusion names the columns, before the pipeline is changed.

1. In Fusion, import `03_reports/skywise/fusion/FTO2 NC Dashboard - Settings.xlsx` as a new spreadsheet named
   "FTO2 NC Dashboard - Settings".
2. On each sheet, select the table (from A1 to its last cell) and sync it to a new dataset, named as on the sheet
   "Read me" (`fto2_set_year`, `fto2_set_targets`…). Two or three sheets are enough for a first test, for example Year,
   Blackout days and Cable tracker.
3. In the Code Workspace, add those datasets in the Data panel, with the same names, read access.
4. In the notebook, add a cell with the content of `fusion_read_test.py` and run it.
5. Send the printed lines. For each dataset they say whether it was read, how many rows, the column names as the notebook
   sees them, and the first row. Columns renamed by Fusion (spaces, accents, "N°") show there.
