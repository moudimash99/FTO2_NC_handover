-- FTO2 dashboard: the cost explanation of each NC, worked out by the Skywise notebook (dataset fto2_dash_cout:
-- seq 0 the NC, seq 1... its defect lines). Slate query q_fto2_cout, for the set-up with two functions.
SELECT
    nc,
    seq,
    eur_alert,
    eur_writing,
    eur_support,
    eur_setup,
    eur_hands_on,
    eur_recheck,
    work_factor,
    adjust,
    minutes,
    material,
    defect_class,
    defect_class_en
FROM "foundry_sync"."fto2_dash_cout"
ORDER BY nc, seq
