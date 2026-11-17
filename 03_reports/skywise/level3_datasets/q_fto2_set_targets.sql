-- FTO2 pages: the settings of the Fusion sheet "Target and pages" (dataset fto2_set_targets, synced from the spreadsheet
-- "FTO2 NC Dashboard - Settings"): one row per setting, its name (nom) and its value (valeur). Slate query
-- q_fto2_set_targets, optional: the dashboard and the MFT page read it through the state key "reglages".
-- Every column is taken: the pages find nom and valeur however the sync wrote their names.
SELECT
    *
FROM "foundry_sync"."fto2_set_targets"
