-- =====================================================================================
-- Cost of non-quality (CNQ) - Slate queries
-- =====================================================================================
-- Two tables, written by the CNQ pipeline step:
--     fto2_nc_cnq        one row per NC
--     fto2_defects_cnq   one row per defect line
-- Replace both names with the dataset references used by your other Slate queries.
--
-- The queries contain NO rates, times or rules. All of that is done in the pipeline
-- (cnq_params.py), so a parameter change never requires touching Slate.
--
-- "AEC" = NCs where liability is on the plant (cnq_on_aec = 1). Only those are cost of
-- non-quality. NCs on other plants or suppliers are shown aside (query q08).
--
-- Plain SQL only (SUM, CASE, GROUP BY, UNION ALL, LIMIT), so it runs on Postgres and Spark SQL.
-- Optional filters: add the lines marked "-- filter:" and bind them to your Slate widgets.
-- One query per block; the name after "--@" is the suggested Slate query name.
-- =====================================================================================


--@ q00_three_levels    -> bar chart or tiles: the same AEC NCs counted three ways
SELECT sort_order, level, ROUND(cost, 0) AS cost, ROUND(cost / NULLIF(nc_count, 0), 0) AS cost_per_nc
FROM (
    SELECT 1 AS sort_order, 'Level 1 - Airbus transnational' AS level, SUM(cnq_cost_airbus) AS cost, COUNT(*) AS nc_count FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 2, 'Level 2 - Global average', SUM(cnq_cost_global), COUNT(*) FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 3, 'Level 3 - Per defect',     SUM(cnq_cost_total),  COUNT(*) FROM fto2_nc_cnq WHERE cnq_on_aec = 1
) t
ORDER BY sort_order
;


--@ q01_kpis            -> tiles: total, count, average, aside
SELECT
    COUNT(*)                                                             AS nc_in_dataset,
    SUM(cnq_on_aec)                                                      AS nc_on_aec,
    ROUND(SUM(cnq_cost_aec), 0)                                          AS cost_aec,
    ROUND(SUM(cnq_cost_aec) / NULLIF(SUM(cnq_on_aec), 0), 0)             AS cost_per_aec_nc,
    SUM(CASE WHEN cnq_liability_group IN ('Other Airbus plant', 'Supplier', 'Other or blank') THEN 1 ELSE 0 END) AS nc_not_on_aec,
    ROUND(SUM(cnq_cost_total) - SUM(cnq_cost_aec), 0)                    AS cost_not_on_aec,
    SUM(CASE WHEN cnq_liability_group = 'No master data' THEN 1 ELSE 0 END) AS nc_no_master_data
FROM fto2_nc_cnq
-- filter: WHERE cnq_month BETWEEN {{w_month_from.selectedValue}} AND {{w_month_to.selectedValue}}
;


--@ q02_cost_by_component   -> bar chart: what the AEC cost is made of
SELECT sort_order, component, ROUND(cost, 0) AS cost
FROM (
    SELECT 1 AS sort_order, 'Alert by the operator'            AS component, SUM(cnq_cost_alert)       AS cost FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 2, 'Writing the NC',                         SUM(cnq_cost_writing)     FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 3, 'Technical support',                      SUM(cnq_cost_support)     FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 4, 'Around the work (badging, setup)',       SUM(cnq_cost_setup)       FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 5, 'Hands-on work',                          SUM(cnq_cost_hands_on)    FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 6, 'Re-check and closing',                   SUM(cnq_cost_recheck)     FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 7, 'Engineering study (design queries)',     SUM(cnq_cost_engineering) FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 8, 'Material',                               SUM(cnq_cost_material)    FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 9, 'Value of rejected or exchanged parts',   SUM(cnq_cost_part)        FROM fto2_nc_cnq WHERE cnq_on_aec = 1
    UNION ALL SELECT 10, 'Customer returns: extra or real amounts', SUM(cnq_cost_customer_adjust) FROM fto2_nc_cnq WHERE cnq_on_aec = 1
) t
ORDER BY sort_order
;


--@ q03_cost_by_month       -> bar chart: AEC cost per month (level 3 only)
SELECT
    cnq_month                              AS month,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_admin), 0)          AS cost_admin,
    ROUND(SUM(cnq_cost_work), 0)           AS cost_work,
    ROUND(SUM(cnq_cost_engineering), 0)    AS cost_engineering,
    ROUND(SUM(cnq_cost_material), 0)       AS cost_material,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1
GROUP BY cnq_month
ORDER BY cnq_month
;


--@ q04_cost_by_week        -> bar chart: AEC cost per week
SELECT
    cnq_week                               AS week,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1
GROUP BY cnq_week
ORDER BY cnq_week
;


--@ q05_cost_by_where_found -> bar chart: where the NC was found (customer returns are their own bar)
SELECT
    cnq_where_found                        AS where_found,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total,
    ROUND(SUM(cnq_cost_total) / COUNT(*), 0) AS cost_per_nc
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1
GROUP BY cnq_where_found
ORDER BY SUM(cnq_cost_total) DESC
;


--@ q06_cost_by_programme   -> bar chart
SELECT
    programme,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1
GROUP BY programme
ORDER BY SUM(cnq_cost_total) DESC
;


--@ q06b_cost_by_product    -> bar chart, top 10 (needs the `produit` column in the NC dataset)
SELECT
    produit                                AS product,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1
GROUP BY produit
ORDER BY SUM(cnq_cost_total) DESC
LIMIT 10
;


--@ q07_cost_by_decision    -> bar chart: rework, reject, exchange, deleted...
SELECT
    cnq_decision_label                     AS decision,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_airbus), 0)         AS cost_level1_airbus,
    ROUND(SUM(cnq_cost_global), 0)         AS cost_level2_global,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total,
    ROUND(SUM(cnq_cost_total) / COUNT(*), 0) AS cost_per_nc
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1
GROUP BY cnq_decision_label
ORDER BY SUM(cnq_cost_total) DESC
;


--@ q08_aside_by_liability  -> bar chart: who is liable. Only the AEC bar is cost of non-quality.
SELECT
    cnq_liability_group                    AS liability_group,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total
FROM fto2_nc_cnq
GROUP BY cnq_liability_group
ORDER BY SUM(cnq_cost_total) DESC
;


--@ q09_customer_returns_by_month -> bar chart: customer returns on AEC, shown apart
SELECT
    cnq_month                              AS month,
    COUNT(*)                               AS nc_count,
    ROUND(SUM(cnq_cost_modelled), 0)       AS cost_estimated,
    SUM(cnq_customer_amount_known)         AS real_amounts_known,
    ROUND(SUM(cnq_cost_total), 0)          AS cost_total
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1 AND cnq_customer_return = 1
GROUP BY cnq_month
ORDER BY cnq_month
;


--@ q09b_customer_returns_list    -> table: every customer return, estimate and real amount when known
SELECT
    notification_number,
    cnq_month                              AS month,
    programme,
    cnq_decision_label                     AS decision,
    cnq_defect_lines                       AS defect_lines,
    ROUND(cnq_cost_modelled, 0)            AS cost_estimated,
    cnq_customer_amount_known              AS real_amount_known,
    ROUND(cnq_cost_total, 0)               AS cost_total
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1 AND cnq_customer_return = 1
ORDER BY cnq_month, notification_number
;


--@ q10_pareto_by_group     -> two-series bar chart: how often vs how much, by parser group
SELECT
    groupe                                 AS defect_group,
    SUM(cnq_line_costed)                   AS defect_lines,
    ROUND(SUM(cnq_min_hands_on) / 60.0, 1) AS hands_on_hours,
    ROUND(SUM(cnq_cost_direct), 0)         AS cost_direct
FROM fto2_defects_cnq
WHERE cnq_line_costed = 1
GROUP BY groupe
ORDER BY SUM(cnq_cost_direct) DESC
;


--@ q11_top_defects_by_cost -> bar chart: top 15 defect classes by direct work cost
SELECT
    cnq_label_en                           AS defect_class,
    sous_groupe                            AS defect_class_original,
    SUM(cnq_line_costed)                   AS defect_lines,
    ROUND(SUM(cnq_min_hands_on) / 60.0, 1) AS hands_on_hours,
    ROUND(SUM(cnq_cost_material), 0)       AS cost_material,
    ROUND(SUM(cnq_cost_direct), 0)         AS cost_direct
FROM fto2_defects_cnq
WHERE cnq_line_costed = 1
GROUP BY cnq_label_en, sous_groupe
ORDER BY SUM(cnq_cost_direct) DESC
LIMIT 15
;


--@ q12_top_defects_by_count -> bar chart: top 15 defect classes by how often they occur
SELECT
    cnq_label_en                           AS defect_class,
    sous_groupe                            AS defect_class_original,
    SUM(cnq_line_costed)                   AS defect_lines,
    ROUND(SUM(cnq_cost_direct), 0)         AS cost_direct
FROM fto2_defects_cnq
WHERE cnq_line_costed = 1
GROUP BY cnq_label_en, sous_groupe
ORDER BY SUM(cnq_line_costed) DESC
LIMIT 15
;


--@ q13_pareto_by_category  -> two-series bar chart on the dashboard's English categories
SELECT
    categorie                              AS category,
    SUM(cnq_line_costed)                   AS defect_lines,
    ROUND(SUM(cnq_cost_direct), 0)         AS cost_direct
FROM fto2_defects_cnq
WHERE cnq_line_costed = 1
GROUP BY categorie
ORDER BY SUM(cnq_cost_direct) DESC
;


--@ q14_data_gaps           -> table: what the model cannot cost properly
SELECT sort_order, gap, nc_count
FROM (
    SELECT 1 AS sort_order, 'AEC NCs with a part value unknown (counted as 0)' AS gap, COUNT(*) AS nc_count
        FROM fto2_nc_cnq WHERE cnq_on_aec = 1 AND cnq_complete = 'Part value unknown'
    UNION ALL SELECT 2, 'AEC reworked NCs with no defect line (flat work time)', COUNT(*)
        FROM fto2_nc_cnq WHERE cnq_on_aec = 1 AND cnq_complete = 'Work time is a flat estimate (no defect line)'
    UNION ALL SELECT 3, 'AEC NCs still open (costed as if finished)', COUNT(*)
        FROM fto2_nc_cnq WHERE cnq_on_aec = 1 AND statut = 'open'
    UNION ALL SELECT 4, 'AEC NCs deleted (administrative cost only)', COUNT(*)
        FROM fto2_nc_cnq WHERE cnq_on_aec = 1 AND cnq_rule = 'DELETED'
    UNION ALL SELECT 5, 'NCs with an unknown decision code', COUNT(*)
        FROM fto2_nc_cnq WHERE cnq_rule = 'UNKNOWN'
    UNION ALL SELECT 6, 'NCs with no master data (not costed)', COUNT(*)
        FROM fto2_nc_cnq WHERE cnq_liability_group = 'No master data'
    UNION ALL SELECT 7, 'Defect lines whose class has no time in the parameters (default used)', COUNT(*)
        FROM fto2_defects_cnq WHERE cnq_time_known = 0
) t
ORDER BY sort_order
;


--@ q15_most_expensive_ncs  -> table: drill-down, 20 most expensive AEC NCs
SELECT
    notification_number,
    cnq_month                              AS month,
    programme,
    cnq_decision_label                     AS decision,
    cnq_where_found                        AS where_found,
    cnq_defect_lines                       AS defect_lines,
    ROUND(cnq_cost_admin, 0)               AS cost_admin,
    ROUND(cnq_cost_work, 0)                AS cost_work,
    ROUND(cnq_cost_material, 0)            AS cost_material,
    ROUND(cnq_cost_total, 0)               AS cost_total
FROM fto2_nc_cnq
WHERE cnq_on_aec = 1
ORDER BY cnq_cost_total DESC
LIMIT 20
;
