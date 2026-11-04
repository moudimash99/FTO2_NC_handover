-- FTO2 pages: reference data (production plan, 2025, cables, MFT actions, cost settings, cause tree), written by the
-- Skywise notebook as dataset fto2_dash_ref: one row per piece of JSON text. Slate query q_fto2_ref.
SELECT
    partie,
    morceau,
    texte
FROM "foundry_sync"."fto2_dash_ref"
ORDER BY partie, morceau
