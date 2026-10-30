-- FTO2 NC dashboard, level 3: one row per defect line (dataset fto2_dash_defects). Slate query q_fto2_def.
SELECT
    nc,
    seq,
    cat,
    rca,
    sub,
    minor,
    cable,
    cost_alloc,
    qty,
    text,
    subcode,
    fin,
    label_src,
    ai_conf,
    cr_nature,
    cr_detection,
    cr_symptom
FROM "foundry_sync"."fto2_dash_defects"
ORDER BY nc, seq
