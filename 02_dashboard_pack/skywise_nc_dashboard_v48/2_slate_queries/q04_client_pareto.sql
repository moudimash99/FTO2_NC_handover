/* q04_client_pareto: Client returns (NCs raised outside FTO2 that we are liable for, not deleted), defects per Pareto category (bar chart)
   Order: the main categories by number of defects, then the categories shown aside, always last
   and in this order: Kitting Factory, FOD, Autre.
   Returns: categorie, defects, defects_principal, defects_a_part, aside, pct, cumulative_pct, ord.
   Chart: renderer stackedBar, x = categorie, two series: defects_principal (colour) and
   defects_a_part (grey). Each bar has a value in only one of the two, so aside bars come out grey.
   Widgets: w_mineurs (dropdown or radio buttons with the two values "Avec mineurs" and
   "Sans mineurs", default "Avec mineurs").
   Reads: foundry_sync.fto2_defects (the Postgres sync of the fto2_defects dataset).
   If your sync has another name, change it on the FROM lines. Nothing else to edit. */
WITH c AS (
    SELECT groupe AS categorie,
           COUNT(*) AS defects,
           CASE groupe WHEN 'Kitting Factory' THEN 1 WHEN 'FOD' THEN 2 WHEN 'Autre' THEN 3 ELSE 0 END AS aside_rank
    FROM foundry_sync.fto2_defects
    WHERE perimetre = 'Retour client'
      AND COALESCE(dans_periode::text, '') IN ('true', 't', '1')
      AND ('{{w_mineurs.selectedValue}}' NOT IN ('Sans mineurs', 'false')
           OR COALESCE(mineur::text, '') NOT IN ('true', 't', '1'))
    GROUP BY groupe
),
o AS (
    SELECT c.*,
           ROW_NUMBER() OVER (ORDER BY aside_rank, CASE WHEN aside_rank = 0 THEN -defects ELSE 0 END, categorie) AS ord
    FROM c
)
SELECT categorie,
       defects,
       CASE WHEN aside_rank = 0 THEN defects END         AS defects_principal,
       CASE WHEN aside_rank > 0 THEN defects END         AS defects_a_part,
       aside_rank > 0                                    AS aside,
       ROUND(100.0 * defects / SUM(defects) OVER (), 1) AS pct,
       ROUND(100.0 * SUM(defects) OVER (ORDER BY ord ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(defects) OVER (), 1)                  AS cumulative_pct,
       ord
FROM o
ORDER BY ord;
