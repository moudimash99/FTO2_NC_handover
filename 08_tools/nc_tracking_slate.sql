-- ============================================================
-- 01_q_monthly_topics.sql
-- ============================================================
/* q_monthly_topics — the three MFT families per month (stacked bar chart)
   Returns one row per month and family: month, topic, defects, plus the month's
   all_defects and all_ncs repeated on each row (for a table or a tooltip).
   Topics (MFT): Inversion & erreur (family Branchement: wiring errors only),
   Câbles, Déverrouillage. Each defect has exactly one family, so the three never
   overlap and can be stacked. Not the same as the Pareto group Branchement,
   which also holds Déverrouillage and Non connecté.
   Needs: dropdown widget w_program (All / A330 / A350).
   Counting: one row = one defect. Deleted and supplier-liable NCs are left out. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted,
           COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%' AS is_supplier
    FROM foundry_sync.sap_nc
),
d AS (
    SELECT n.nc_id, to_char(date_trunc('month', n.created_on), 'YYYY-MM') AS month, f.famille
    FROM foundry_sync.nc_defects f
    JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
    WHERE NOT n.is_deleted
      AND NOT n.is_supplier
      AND n.created_on >= DATE '2026-01-01'
      AND ('{{w_program.selectedValue}}' IN ('', 'All') OR n.program = '{{w_program.selectedValue}}')
),
months AS (
    SELECT month, COUNT(*) AS all_defects, COUNT(DISTINCT nc_id) AS all_ncs
    FROM d
    GROUP BY 1
),
topics AS (
    SELECT * FROM (VALUES (1, 'Branchement', 'Inversion & erreur'), (2, 'Câbles', 'Câbles'),
                          (3, 'Déverrouillage', 'Déverrouillage')) AS t(ord, famille, topic)
)
SELECT m.month,
       t.topic,
       COUNT(d.nc_id)  AS defects,
       m.all_defects,
       m.all_ncs
FROM months m
CROSS JOIN topics t
LEFT JOIN d ON d.month = m.month AND d.famille = t.famille
GROUP BY m.month, t.ord, t.topic, m.all_defects, m.all_ncs
ORDER BY m.month, t.ord;

-- ============================================================
-- 02_q_pareto.sql
-- ============================================================
/* q_pareto — defects by Pareto group (bar chart)
   Order: Câblage, Branchement, Dommage & manquant, Métallisation by count, then the groups shown
   aside, always last and in this order: Amont, FOD, Dossier, Non classé.
   Returns: pareto_group, defects, aside (true/false), pct, cumulative_pct, ord.
   What is inside each group is in q_pareto_detail.
   Needs: dropdown widget w_program (All / A330 / A350).
   Period: from the date on the marked line to today. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted,
           COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%' AS is_supplier
    FROM foundry_sync.sap_nc
),
d AS (
    SELECT f.groupe
    FROM foundry_sync.nc_defects f
    JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
    WHERE NOT n.is_deleted
      AND NOT n.is_supplier
      AND n.created_on >= DATE '2026-01-01'            -- EDIT: start of the period
      AND ('{{w_program.selectedValue}}' IN ('', 'All') OR n.program = '{{w_program.selectedValue}}')
),
c AS (
    SELECT groupe AS pareto_group,
           COUNT(*) AS defects,
           CASE groupe WHEN 'Amont' THEN 1 WHEN 'FOD' THEN 2 WHEN 'Dossier' THEN 3
                       WHEN 'Non classé' THEN 4 ELSE 0 END AS aside_rank
    FROM d
    GROUP BY 1
),
o AS (
    SELECT c.*,
           ROW_NUMBER() OVER (ORDER BY aside_rank,
                                       CASE WHEN aside_rank = 0 THEN -defects ELSE 0 END,
                                       pareto_group) AS ord
    FROM c
)
SELECT pareto_group,
       defects,
       aside_rank > 0                                    AS aside,
       ROUND(100.0 * defects / SUM(defects) OVER (), 1) AS pct,
       ROUND(100.0 * SUM(defects) OVER (ORDER BY ord ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(defects) OVER (), 1)                  AS cumulative_pct,
       ord
FROM o
ORDER BY ord;

-- ============================================================
-- 03_q_pareto_detail.sql
-- ============================================================
/* q_pareto_detail — what is inside one Pareto group (drill-down under the Pareto)
   Branchement: Inversion, Erreur de branchement, Déverrouillage, Non connecté.
   Câblage: the object worked on (Frettage / colliers, Cheminement, Identification...).
   Dommage & manquant: "Dommage · pièce", "Manquant · colliers", "Pièce HS ou non conforme"...
   Métallisation: Bleu manquant, Bleu à reprendre ou débordant, Mesure de masse, Tresse.
   Returns: detail, defects, pct_of_group.
   Needs: dropdown widgets w_program, and w_group with values {{q_pareto.pareto_group}}.
   Period: same start date as q_pareto. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted,
           COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%' AS is_supplier
    FROM foundry_sync.sap_nc
),
d AS (
    SELECT f.sous_groupe
    FROM foundry_sync.nc_defects f
    JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
    WHERE NOT n.is_deleted
      AND NOT n.is_supplier
      AND n.created_on >= DATE '2026-01-01'            -- EDIT: start of the period, as in q_pareto
      AND ('{{w_program.selectedValue}}' IN ('', 'All') OR n.program = '{{w_program.selectedValue}}')
      AND f.groupe = '{{w_group.selectedValue}}'
),
c AS (
    SELECT sous_groupe AS detail, COUNT(*) AS defects
    FROM d
    GROUP BY 1
)
SELECT detail,
       defects,
       ROUND(100.0 * defects / SUM(defects) OVER (), 1) AS pct_of_group
FROM c
ORDER BY defects DESC, detail;

-- ============================================================
-- 04_q_mft_topics.sql
-- ============================================================
/* q_mft_topics — the list of MFT topics, to fill the dropdown w_topic
   Returns: topic_id, label. Set the dropdown's values to {{q_mft_topics.topic_id}}
   and its labels to {{q_mft_topics.label}}. */
SELECT topic_id,
       topic_id || ' · ' || topic_en AS label
FROM foundry_sync.mft_actions
ORDER BY topic_id;

-- ============================================================
-- 05_q_mft_weekly.sql
-- ============================================================
/* q_mft_weekly — one MFT topic, week by week, before and after its action started
   Returns one row per ISO week: iso_week, week_start, phase (Before / After action start /
   No start date), defects (defects that match the topic's rule), program_defects (all
   defects of that program that week), per_100_defects.
   Needs: dropdown widget w_topic, filled from q_mft_topics.
   The rule comes from the mft_actions table: program + categories + optional cable
   state, text regex and station regex. Change the table, not this query. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(station_description::text, '')             AS station,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted,
           COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%' AS is_supplier
    FROM foundry_sync.sap_nc
),
d AS (
    SELECT n.created_on, n.program, n.station, f.categorie,
           COALESCE(f.etat_cable::text, '') AS etat_cable,
           COALESCE(f.text::text, '')       AS text
    FROM foundry_sync.nc_defects f
    JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
    WHERE NOT n.is_deleted
      AND NOT n.is_supplier
      AND n.created_on >= DATE '2026-01-01'
),
m AS (
    SELECT topic_id, program,
           NULLIF(action_start::text, '')::date      AS action_start,
           COALESCE(rule_categories::text, '')       AS rule_categories,
           COALESCE(rule_etat_cable::text, '')       AS rule_etat_cable,
           COALESCE(rule_text_regex::text, '')       AS rule_text_regex,
           COALESCE(rule_station_regex::text, '')    AS rule_station_regex
    FROM foundry_sync.mft_actions
    WHERE topic_id = '{{w_topic.selectedValue}}'
),
weeks AS (
    SELECT generate_series(date_trunc('week', DATE '2026-01-01'),
                           date_trunc('week', CURRENT_DATE) - INTERVAL '1 week',   -- last complete week
                           INTERVAL '1 week')::date AS week
),
hits AS (
    SELECT date_trunc('week', d.created_on)::date AS week, COUNT(*) AS defects
    FROM d JOIN m ON d.program = m.program
    WHERE (m.rule_categories    = '' OR d.categorie = ANY (string_to_array(m.rule_categories, '|')))
      AND (m.rule_etat_cable    = '' OR d.etat_cable = m.rule_etat_cable)
      AND (m.rule_text_regex    = '' OR d.text    ~* m.rule_text_regex)
      AND (m.rule_station_regex = '' OR d.station ~* m.rule_station_regex)
    GROUP BY 1
),
prog AS (
    SELECT date_trunc('week', d.created_on)::date AS week, COUNT(*) AS program_defects
    FROM d JOIN m ON d.program = m.program
    GROUP BY 1
)
SELECT to_char(w.week, 'IYYY-"W"IW')                                    AS iso_week,
       w.week                                                           AS week_start,
       CASE WHEN m.action_start IS NULL THEN 'No start date'
            WHEN w.week >= date_trunc('week', m.action_start)::date THEN 'After action start'
            ELSE 'Before' END                                           AS phase,
       COALESCE(h.defects, 0)                                           AS defects,
       COALESCE(p.program_defects, 0)                                   AS program_defects,
       ROUND(100.0 * COALESCE(h.defects, 0) / NULLIF(p.program_defects, 0), 1) AS per_100_defects
FROM weeks w
CROSS JOIN m
LEFT JOIN hits h ON h.week = w.week
LEFT JOIN prog p ON p.week = w.week
ORDER BY w.week;

-- ============================================================
-- 06_q_mft_summary.sql
-- ============================================================
/* q_mft_summary — every MFT topic on one line: is the action moving the numbers?
   Returns one row per topic: topic_id, topic, program, action_start, owner, status,
   per_week_before (average over the 13 weeks before the action started),
   per_week_after (average since it started), weeks_after,
   per_100_before / per_100_after (the topic's share of all the program's defects,
   which corrects for busy and quiet weeks).
   Averages only use weeks in which the program had at least one defect, so
   shutdown weeks do not pull them down. No widget needed (table widget). */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(station_description::text, '')             AS station,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted,
           COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%' AS is_supplier
    FROM foundry_sync.sap_nc
),
d AS (
    SELECT n.created_on, n.program, n.station, f.categorie,
           COALESCE(f.etat_cable::text, '') AS etat_cable,
           COALESCE(f.text::text, '')       AS text
    FROM foundry_sync.nc_defects f
    JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
    WHERE NOT n.is_deleted
      AND NOT n.is_supplier
      AND n.created_on >= DATE '2026-01-01'
),
m AS (
    SELECT topic_id, topic_en, program, owner::text AS owner, status::text AS status,
           NULLIF(action_start::text, '')::date      AS action_start,
           COALESCE(rule_categories::text, '')       AS rule_categories,
           COALESCE(rule_etat_cable::text, '')       AS rule_etat_cable,
           COALESCE(rule_text_regex::text, '')       AS rule_text_regex,
           COALESCE(rule_station_regex::text, '')    AS rule_station_regex
    FROM foundry_sync.mft_actions
),
weeks AS (
    SELECT generate_series(date_trunc('week', DATE '2026-01-01'),
                           date_trunc('week', CURRENT_DATE) - INTERVAL '1 week',
                           INTERVAL '1 week')::date AS week
),
hits AS (
    SELECT m.topic_id, date_trunc('week', d.created_on)::date AS week, COUNT(*) AS defects
    FROM d JOIN m ON d.program = m.program
    WHERE (m.rule_categories    = '' OR d.categorie = ANY (string_to_array(m.rule_categories, '|')))
      AND (m.rule_etat_cable    = '' OR d.etat_cable = m.rule_etat_cable)
      AND (m.rule_text_regex    = '' OR d.text    ~* m.rule_text_regex)
      AND (m.rule_station_regex = '' OR d.station ~* m.rule_station_regex)
    GROUP BY 1, 2
),
prog AS (
    SELECT program, date_trunc('week', created_on)::date AS week, COUNT(*) AS program_defects
    FROM d
    GROUP BY 1, 2
),
g AS (                                                  -- topic x week grid, busy weeks only
    SELECT m.topic_id, w.week, COALESCE(h.defects, 0) AS defects, p.program_defects,
           CASE WHEN m.action_start IS NULL THEN NULL
                WHEN w.week >= date_trunc('week', m.action_start)::date THEN 'after'
                WHEN w.week >= (date_trunc('week', m.action_start) - INTERVAL '13 weeks')::date THEN 'before'
           END AS phase
    FROM m CROSS JOIN weeks w
    JOIN prog p ON p.program = m.program AND p.week = w.week
    LEFT JOIN hits h ON h.topic_id = m.topic_id AND h.week = w.week
)
SELECT m.topic_id,
       m.topic_en                                                                  AS topic,
       m.program,
       m.action_start,
       m.owner,
       m.status,
       ROUND(AVG(CASE WHEN g.phase = 'before' THEN g.defects END), 1)              AS per_week_before,
       ROUND(AVG(CASE WHEN g.phase = 'after'  THEN g.defects END), 1)              AS per_week_after,
       SUM(CASE WHEN g.phase = 'after' THEN 1 ELSE 0 END)                          AS weeks_after,
       ROUND(100.0 * SUM(CASE WHEN g.phase = 'before' THEN g.defects END)
             / NULLIF(SUM(CASE WHEN g.phase = 'before' THEN g.program_defects END), 0), 1) AS per_100_before,
       ROUND(100.0 * SUM(CASE WHEN g.phase = 'after' THEN g.defects END)
             / NULLIF(SUM(CASE WHEN g.phase = 'after' THEN g.program_defects END), 0), 1)  AS per_100_after
FROM m
LEFT JOIN g ON g.topic_id = m.topic_id
GROUP BY m.topic_id, m.topic_en, m.program, m.action_start, m.owner, m.status
ORDER BY m.topic_id;

-- ============================================================
-- 07_q_mft_categories.sql
-- ============================================================
/* q_mft_categories — for one MFT topic, which categories make it up, before vs after
   Most useful for the A330 "Mise en oeuvre" topic, which spans nine categories.
   Returns one row per category and period: category, period ('13 weeks before' or
   'Since action start'), defects, weeks, per_week. Per week, because the two periods
   have different lengths. Needs: dropdown widget w_topic. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(station_description::text, '')             AS station,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted,
           COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%' AS is_supplier
    FROM foundry_sync.sap_nc
),
d AS (
    SELECT n.created_on, n.program, n.station, f.categorie,
           COALESCE(f.etat_cable::text, '') AS etat_cable,
           COALESCE(f.text::text, '')       AS text
    FROM foundry_sync.nc_defects f
    JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
    WHERE NOT n.is_deleted
      AND NOT n.is_supplier
),
m AS (
    SELECT topic_id, program,
           date_trunc('week', NULLIF(action_start::text, '')::date)::date AS start_week,
           COALESCE(rule_categories::text, '')       AS rule_categories,
           COALESCE(rule_etat_cable::text, '')       AS rule_etat_cable,
           COALESCE(rule_text_regex::text, '')       AS rule_text_regex,
           COALESCE(rule_station_regex::text, '')    AS rule_station_regex
    FROM foundry_sync.mft_actions
    WHERE topic_id = '{{w_topic.selectedValue}}'
),
p AS (                                                  -- the two periods, whole weeks only
    SELECT '13 weeks before' AS period, 1 AS ord,
           (start_week - INTERVAL '13 weeks')::date AS p_from, start_week AS p_to
    FROM m
    UNION ALL
    SELECT 'Since action start', 2, start_week, date_trunc('week', CURRENT_DATE)::date
    FROM m
),
hits AS (
    SELECT d.categorie, d.created_on
    FROM d JOIN m ON d.program = m.program
    WHERE (m.rule_categories    = '' OR d.categorie = ANY (string_to_array(m.rule_categories, '|')))
      AND (m.rule_etat_cable    = '' OR d.etat_cable = m.rule_etat_cable)
      AND (m.rule_text_regex    = '' OR d.text    ~* m.rule_text_regex)
      AND (m.rule_station_regex = '' OR d.station ~* m.rule_station_regex)
)
SELECT h.categorie                                              AS category,
       p.period,
       COUNT(*)                                                 AS defects,
       GREATEST((p.p_to - p.p_from) / 7, 0)                     AS weeks,
       ROUND(COUNT(*)::numeric / NULLIF(GREATEST((p.p_to - p.p_from) / 7, 0), 0), 1) AS per_week
FROM hits h
JOIN p ON h.created_on >= p.p_from AND h.created_on < p.p_to
GROUP BY h.categorie, p.period, p.ord, p.p_from, p.p_to
ORDER BY h.categorie, p.ord;

-- ============================================================
-- 08_q_unlocked_by_fin.sql
-- ============================================================
/* q_unlocked_by_fin — A350 connectors not locked, per connector (FIN)
   Answers MFT A350-02 action 1: is there a recurrence on VT / VG, and on which pins?
   Returns one row per FIN: fin_family (VG, VT, VC...), fin, defects, ncs,
   pins (terminals named in the text), first_seen, last_seen.
   The chart by family is a GROUP BY on fin_family of this result, or a second
   query that sums defects by fin_family. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted,
           COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%' AS is_supplier
    FROM foundry_sync.sap_nc
),
d AS (
    SELECT n.nc_id, n.created_on, f.fin, COALESCE(f.text::text, '') AS text
    FROM foundry_sync.nc_defects f
    JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
    WHERE NOT n.is_deleted
      AND NOT n.is_supplier
      AND n.program = 'A350'
      AND f.categorie = 'Connectors not locked'
      AND n.created_on >= DATE '2026-01-01'
)
SELECT COALESCE(substring(upper(COALESCE(fin, '')) from '[0-9]+([A-Z]{2})'), '(none)')  AS fin_family,
       upper(regexp_replace(COALESCE(fin, ''), '\s+', '', 'g'))                         AS fin,
       COUNT(*)                                                                          AS defects,
       COUNT(DISTINCT nc_id)                                                             AS ncs,
       COALESCE(string_agg(DISTINCT upper(substring(text from '(?i)borne\s+([0-9]{1,2}[a-z]?|[a-z]{1,2})\y')), ', '), '') AS pins,
       MIN(created_on)                                                                   AS first_seen,
       MAX(created_on)                                                                   AS last_seen
FROM d
GROUP BY 1, 2
ORDER BY defects DESC, last_seen DESC;

-- ============================================================
-- 09_q_client_returns.sql
-- ============================================================
/* q_client_returns — NCs raised at a customer site (plant other than FTO2), by Pareto group
   Returns one row per Pareto group: pareto_group, defects, ncs, plus two totals repeated on
   every row for the headline tiles: client_ncs (all) and client_ncs_open (not deleted).
   Tiles: {{q_client_returns.client_ncs[0]}} and {{q_client_returns.client_ncs_open[0]}}.
   Needs: dropdown widget w_program. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(plant::text, '')                           AS plant,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted
    FROM foundry_sync.sap_nc
    WHERE COALESCE(plant::text, '') <> 'FTO2'           -- EDIT if your own plant code differs
      AND (creation_time::timestamptz)::date >= DATE '2026-01-01'
      AND ('{{w_program.selectedValue}}' IN ('', 'All') OR programme::text = '{{w_program.selectedValue}}')
),
t AS (
    SELECT COUNT(*) AS client_ncs,
           SUM(CASE WHEN NOT is_deleted THEN 1 ELSE 0 END) AS client_ncs_open
    FROM nc
)
SELECT f.groupe                 AS pareto_group,
       COUNT(*)                 AS defects,
       COUNT(DISTINCT n.nc_id)  AS ncs,
       MAX(t.client_ncs)        AS client_ncs,
       MAX(t.client_ncs_open)   AS client_ncs_open
FROM foundry_sync.nc_defects f
JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
CROSS JOIN t
WHERE NOT n.is_deleted
GROUP BY 1
ORDER BY CASE f.groupe WHEN 'Amont' THEN 1 WHEN 'FOD' THEN 2 WHEN 'Dossier' THEN 3
                       WHEN 'Non classé' THEN 4 ELSE 0 END,
         2 DESC, 1;

-- ============================================================
-- 10_q_supplier_returns.sql
-- ============================================================
/* q_supplier_returns — NCs where SAP makes the supplier liable, by Pareto group
   These NCs are left out of every other query. Returns one row per Pareto group:
   pareto_group, defects, ncs, plus supplier_ncs (all) and supplier_ncs_open (not deleted)
   repeated on every row for the headline tiles.
   Needs: dropdown widget w_program. */
WITH nc AS (                                           -- EDIT: SAP table and column names
    SELECT ltrim(notification_number::text, '0')               AS nc_id,
           (creation_time::timestamptz)::date                  AS created_on,
           programme::text                                     AS program,
           COALESCE(status_open_closed::text, '') = 'deleted'  AS is_deleted
    FROM foundry_sync.sap_nc
    WHERE COALESCE(liability_description::text, '') ILIKE '%SUPPLIER%'
      AND (creation_time::timestamptz)::date >= DATE '2026-01-01'
      AND ('{{w_program.selectedValue}}' IN ('', 'All') OR programme::text = '{{w_program.selectedValue}}')
),
t AS (
    SELECT COUNT(*) AS supplier_ncs,
           SUM(CASE WHEN NOT is_deleted THEN 1 ELSE 0 END) AS supplier_ncs_open
    FROM nc
)
SELECT f.groupe                 AS pareto_group,
       COUNT(*)                 AS defects,
       COUNT(DISTINCT n.nc_id)  AS ncs,
       MAX(t.supplier_ncs)      AS supplier_ncs,
       MAX(t.supplier_ncs_open) AS supplier_ncs_open
FROM foundry_sync.nc_defects f
JOIN nc n ON n.nc_id = ltrim(f.notification_number::text, '0')
CROSS JOIN t
WHERE NOT n.is_deleted
GROUP BY 1
ORDER BY CASE f.groupe WHEN 'Amont' THEN 1 WHEN 'FOD' THEN 2 WHEN 'Dossier' THEN 3
                       WHEN 'Non classé' THEN 4 ELSE 0 END,
         2 DESC, 1;

