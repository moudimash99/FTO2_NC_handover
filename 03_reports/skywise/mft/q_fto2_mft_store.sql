-- FTO2 MFT page: the MFT actions kept for everyone, in the NC writer's object type ("a30 Nc Writer Dataset"): the objects
-- whose Msn is MFT-ACTIONS, their Texte Sap holding every action as JSON. Each save adds one; the page takes the one saved
-- last. Slate query q_fto2_mft_store, optional (03_reports/skywise/README.md, step 4): the state key "store".
-- The table: the dataset the object type's action writes to, synced to Postgres as fto2_mft_store (schema foundry_sync).
-- If Slate says a column does not exist, write its name as Postgres has it, between double quotes (for example "Msn", "Texte Sap").
-- Only the 20 saved last are read (their save time is in the text, after "saved_at").
SELECT
    *
FROM "foundry_sync"."fto2_mft_store"
WHERE msn = 'MFT-ACTIONS'
ORDER BY substring(texte_sap from '"saved_at":"([^"]*)"') DESC NULLS LAST
LIMIT 20
