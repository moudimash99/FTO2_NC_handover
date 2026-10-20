-- FTO2 NC dashboard, level 3: one row per quality aléa with no NC, the disruption block (dataset fto2_dash_disruptions). Slate query q_fto2_dis.
SELECT
    id,
    CAST(opened AS VARCHAR) AS opened,
    line,
    station,
    work_order,
    minutes,
    in_block,
    reason,
    status,
    comment
FROM "foundry_sync"."fto2_dash_disruptions"
ORDER BY opened, id
